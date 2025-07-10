import requests
import pandas as pd
import json
from config import settings
import logging

logger = logging.getLogger(__name__)

def _extract_metric(action_list, key):
    """Helper to safely extract metric values from nested action lists."""
    # This check handles cases where the input is not a list, returning 0.0
    if not isinstance(action_list, list):
        return 0.0
    for item in action_list:
        if item.get("action_type") == key:
            try:
                return float(item.get("value", 0))
            except (TypeError, ValueError):
                return 0.0
    return 0.0

def fetch_campaigns() -> pd.DataFrame:
    """Fetches a list of all campaigns and their metadata."""
    url = f"https://graph.facebook.com/{settings.API_VERSION}/{settings.AD_ACCOUNT_ID}/campaigns"
    params = {
        "access_token": settings.ACCESS_TOKEN,
        "fields": "id,name,status,effective_status,start_time,stop_time",
        "limit": "500"
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "data" not in data or not data["data"]:
            logger.warning(f"No campaigns found or API error: {data}")
            return pd.DataFrame()
        return pd.DataFrame(data["data"])
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request to fetch campaigns failed: {e}")
        raise

def fetch_insights_in_batch(campaign_ids: list) -> pd.DataFrame:
    """Fetches performance insights for all campaign IDs in a single batch request."""
    if not campaign_ids:
        return pd.DataFrame()

    insights_fields = [
        "date_start", "date_stop", "campaign_name", "campaign_id", "spend", "reach",
        "impressions", "frequency", "clicks", "cpc", "cpm", "ctr", "unique_clicks",
        "unique_ctr", "outbound_clicks", "unique_outbound_clicks", "actions",
        "cost_per_action_type"
    ]
    
    batch_payload = [
        {
            "method": "GET",
            "relative_url": f"{settings.API_VERSION}/{campaign_id}/insights?date_preset=maximum&fields={','.join(insights_fields)}"
        }
        for campaign_id in campaign_ids
    ]

    url = f"https://graph.facebook.com/{settings.API_VERSION}/"
    params = {
        "access_token": settings.ACCESS_TOKEN,
        "batch": json.dumps(batch_payload)
    }

    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        results = response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP batch request to fetch insights failed: {e}")
        raise

    all_insights = []
    for i, res in enumerate(results):
        campaign_id = campaign_ids[i]
        if res is None or res.get("code") != 200:
            logger.warning(f"Failed to fetch insights for campaign_id {campaign_id}. Response: {res}")
            continue
        
        body = json.loads(res.get("body", "{}"))
        if "data" in body and body["data"]:
             all_insights.extend(body["data"])
        else:
            logger.info(f"No insights data found for campaign_id {campaign_id}.")
            
    return pd.DataFrame(all_insights)


def process_and_merge_data(df_campaigns: pd.DataFrame, df_insights: pd.DataFrame) -> pd.DataFrame:
    """Cleans, processes, and merges campaign and insights dataframes."""
    if df_insights.empty:
        return pd.DataFrame()

    # --- Flatten nested action/metric columns ---
    action_keys = ["link_click", "landing_page_view", "thruplay", "purchase"]

    for key in action_keys:
        # Ensure the column exists before trying to apply a function
        if 'actions' in df_insights.columns:
            df_insights[f"action_{key}"] = df_insights["actions"].apply(lambda x: _extract_metric(x, key))
        if 'cost_per_action_type' in df_insights.columns:
            df_insights[f"cpa_{key}"] = df_insights["cost_per_action_type"].apply(lambda x: _extract_metric(x, key))

    # ** FIX STARTS HERE **
    # The API can return outbound_clicks as a list of actions, so we must parse it.
    if 'outbound_clicks' in df_insights.columns:
        df_insights['outbound_clicks'] = df_insights['outbound_clicks'].apply(lambda x: _extract_metric(x, 'outbound_click'))
    if 'unique_outbound_clicks' in df_insights.columns:
        df_insights['unique_outbound_clicks'] = df_insights['unique_outbound_clicks'].apply(lambda x: _extract_metric(x, 'unique_outbound_click'))
    # ** FIX ENDS HERE **
            
    df_insights.drop(columns=["actions", "cost_per_action_type"], inplace=True, errors="ignore")

    # --- Merge insights with campaign metadata ---
    df_final = pd.merge(df_insights, df_campaigns, left_on="campaign_id", right_on="id", how="left", suffixes=("", "_meta"))

    # --- Data Type Conversion and Cleaning ---
    for col in ["date_start", "date_stop", "start_time", "stop_time"]:
        if col in df_final.columns:
            df_final[col] = pd.to_datetime(df_final[col], errors='coerce')

    numeric_cols = df_final.select_dtypes(include=['number']).columns
    df_final[numeric_cols] = df_final[numeric_cols].fillna(0)

    string_cols = df_final.select_dtypes(include=['object']).columns
    df_final[string_cols] = df_final[string_cols].fillna('N/A')
    
    # Replace Pandas NaT with None so Pydantic can handle it
    df_final = df_final.astype(object).where(pd.notnull(df_final), None)

    if "id" in df_final.columns:
        df_final.drop(columns=["id"], inplace=True)
    if "name" in df_final.columns and "campaign_name" in df_final.columns:
        df_final['campaign_name'] = df_final.apply(
            lambda row: row['name'] if row['campaign_name'] == 'N/A' else row['campaign_name'],
            axis=1
        )
        df_final.drop(columns=["name"], inplace=True)

    return df_final

