import google.generativeai as genai
from config import settings
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

# Configure the Gemini API client
try:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    logger.info("✅ Successfully configured Gemini API client.")
except Exception as e:
    logger.error(f"🔥 Failed to configure Gemini API client: {e}")
    model = None

# Enhanced master prompt with comprehensive analytical capabilities
CAMPANION_MASTER_PROMPT = """
You are Campanion, an AI-powered 24x7 Virtual Media Buyer Coach and forensic data watchdog with 30 years of experience in media buying and data science. You provide clear, precise, confident, data-backed answers based strictly on the provided campaign data.

**Your Analytical Framework:**
- **Data Detective**: Identify patterns, anomalies, and insights hidden in campaign metrics
- **Performance Diagnostician**: Diagnose issues using statistical analysis and industry benchmarks
- **Strategic Advisor**: Translate data insights into actionable business recommendations
- **Trend Analyst**: Spot emerging patterns and predict performance trajectories
- **ROI Optimizer**: Focus on metrics that directly impact business outcomes

**Core Principles:**
- Answer only what is explicitly asked with data-driven confidence
- Provide evidence-based insights using the JSON data provided
- Never assume, invent, or add information beyond the available data
- Summarize only relevant data points that justify your conclusions
- Stay concise, confident, and precisely focused
- If data is insufficient, clearly state limitations
- Ground all recommendations in actual performance metrics

**Advanced Analysis Capabilities:**

1. **Performance Benchmarking**: Compare metrics against industry standards and historical performance
2. **Trend Analysis**: Identify week-over-week, month-over-month patterns and seasonality
3. **Anomaly Detection**: Flag unusual spikes, drops, or patterns that require attention
4. **Efficiency Analysis**: Calculate and optimize cost efficiency across campaigns and platforms
5. **Attribution Modeling**: Understand customer journey and multi-touch attribution
6. **Predictive Insights**: Forecast performance based on current trends and data patterns
7. **Competitive Intelligence**: Infer market conditions from performance data shifts
8. **Creative Performance**: Analyze ad fatigue, frequency caps, and creative rotation needs

**Response Framework:**
1. **Executive Summary**: Lead with clear, confident answer to the specific question
2. **Key Data Evidence**: Present the most relevant supporting metrics and calculations
3. **Performance Context**: Provide industry benchmarks or historical comparisons when relevant
4. **Actionable Insights**: Identify specific optimization opportunities
5. **Risk Assessment**: Highlight potential issues or concerns in the data
6. **Recommendations**: ONLY provide when explicitly requested using words like "suggest", "recommend", "advise", or "improve"

**Data Analysis Techniques:**
- **Statistical Analysis**: Calculate significance, confidence intervals, and correlation coefficients
- **Cohort Analysis**: Track user behavior and lifetime value patterns
- **Funnel Analysis**: Identify conversion bottlenecks and optimization opportunities
- **Segmentation**: Break down performance by audience, device, placement, and time
- **Efficiency Metrics**: ROAS, CPA efficiency, cost per acquisition by funnel stage
- **Quality Scoring**: Lead quality, engagement rates, and conversion probability

**Formatting Standards:**
- Use Markdown with clear headings and bold text for key metrics
- Present data in bullet points for easy scanning
- Include relevant calculations and percentage changes
- Highlight critical findings with **bold formatting**
- Use tables for comparative data when appropriate
- Maintain professional, confident tone throughout

**Campaign Data Analysis:**
{insights_data}

**Specific Query:**
"{query}"

**Data-Driven Response:**
"""

def get_insights_from_llm(query: str, insights_data: List[Dict], analysis_type: str = "standard") -> str:
    """
    Enhanced data analysis with specialized analytical frameworks.
    
    Args:
        query: User's natural language query
        insights_data: Campaign performance data
        analysis_type: Type of analysis (standard, forensic, trend, efficiency, etc.)
    
    Returns:
        Comprehensive data-driven analysis
    """
    if not model:
        return "LLM service is not configured. Please check the API key configuration."

    if not insights_data:
        return "No campaign data available for analysis. Please sync your campaign data first."

    # Enhanced data preprocessing
    processed_data = enhance_data_for_analysis(insights_data)
    data_json = json.dumps(processed_data, indent=2, default=str)

    # Customize prompt based on analysis type
    enhanced_prompt = CAMPANION_MASTER_PROMPT.format(
        insights_data=data_json,
        query=query
    )

    if analysis_type == "forensic":
        enhanced_prompt += "\n\n**FORENSIC ANALYSIS MODE**: Conduct deep-dive investigation with root cause analysis. Examine data patterns, identify correlations, and provide evidence-based conclusions."
    elif analysis_type == "trend":
        enhanced_prompt += "\n\n**TREND ANALYSIS MODE**: Focus on temporal patterns, seasonality, and trajectory forecasting. Identify emerging trends and predict future performance."
    elif analysis_type == "efficiency":
        enhanced_prompt += "\n\n**EFFICIENCY ANALYSIS MODE**: Optimize cost efficiency metrics. Calculate ROAS, CPA efficiency, and identify budget reallocation opportunities."
    elif analysis_type == "creative":
        enhanced_prompt += "\n\n**CREATIVE ANALYSIS MODE**: Analyze ad creative performance, frequency impact, and creative fatigue indicators. Recommend refresh strategies."

    try:
        logger.info(f"🧠 Performing {analysis_type} analysis for query: '{query}'")
        response = model.generate_content(enhanced_prompt)
        logger.info("✅ Successfully completed enhanced data analysis.")
        return response.text
    except Exception as e:
        logger.error(f"🔥 Error in LLM analysis: {e}", exc_info=True)
        return f"An error occurred during {analysis_type} analysis. Please try again or contact support."

def enhance_data_for_analysis(insights_data: List[Dict]) -> List[Dict]:
    """
    Enhance raw campaign data with calculated metrics and insights.
    
    Args:
        insights_data: Raw campaign insights data
        
    Returns:
        Enhanced data with additional calculated fields
    """
    try:
        enhanced_data = []
        
        for record in insights_data:
            enhanced_record = record.copy()
            
            # Calculate additional efficiency metrics
            if record.get('spend', 0) > 0:
                # Cost efficiency metrics
                enhanced_record['cost_per_impression'] = float(record.get('spend', 0)) / max(float(record.get('impressions', 1)), 1) * 1000
                enhanced_record['cost_per_click'] = float(record.get('spend', 0)) / max(float(record.get('clicks', 1)), 1)
                
                # ROAS calculation if purchase data available
                if record.get('action_purchase', 0) > 0:
                    # Assume average order value if not provided
                    estimated_revenue = float(record.get('action_purchase', 0)) * 50  # $50 AOV assumption
                    enhanced_record['estimated_roas'] = estimated_revenue / float(record.get('spend', 1))
                
            # Engagement quality metrics
            if record.get('impressions', 0) > 0:
                enhanced_record['engagement_rate'] = (
                    float(record.get('clicks', 0)) + 
                    float(record.get('action_link_click', 0)) + 
                    float(record.get('action_landing_page_view', 0))
                ) / float(record.get('impressions', 1)) * 100
                
            # Conversion funnel metrics
            if record.get('clicks', 0) > 0:
                enhanced_record['click_to_conversion_rate'] = (
                    float(record.get('action_purchase', 0)) / float(record.get('clicks', 1)) * 100
                )
                enhanced_record['landing_page_conversion_rate'] = (
                    float(record.get('action_landing_page_view', 0)) / float(record.get('clicks', 1)) * 100
                )
            
            # Ad fatigue indicators
            frequency = float(record.get('frequency', 0))
            if frequency > 0:
                enhanced_record['fatigue_risk'] = "High" if frequency > 4 else "Medium" if frequency > 2 else "Low"
                
            # Performance scoring
            ctr = float(record.get('ctr', 0))
            enhanced_record['ctr_performance'] = (
                "Excellent" if ctr > 2 else 
                "Good" if ctr > 1 else 
                "Average" if ctr > 0.5 else 
                "Poor"
            )
            
            # Add temporal analysis if date available
            if record.get('date_start'):
                try:
                    date_start = pd.to_datetime(record['date_start'])
                    enhanced_record['day_of_week'] = date_start.strftime('%A')
                    enhanced_record['week_of_year'] = date_start.isocalendar()[1]
                    enhanced_record['days_running'] = (datetime.now() - date_start).days
                except:
                    pass
                    
            enhanced_data.append(enhanced_record)
            
        return enhanced_data
        
    except Exception as e:
        logger.error(f"Error enhancing data: {e}")
        return insights_data  # Return original data if enhancement fails

def generate_performance_summary(insights_data: List[Dict]) -> Dict[str, Any]:
    """
    Generate comprehensive performance summary statistics.
    
    Args:
        insights_data: Campaign performance data
        
    Returns:
        Dictionary containing summary statistics and insights
    """
    try:
        if not insights_data:
            return {"error": "No data available for summary"}
        
        df = pd.DataFrame(insights_data)
        
        # Convert numeric columns
        numeric_columns = ['spend', 'impressions', 'clicks', 'ctr', 'cpc', 'cpm', 'frequency']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        summary = {
            "total_campaigns": len(df),
            "total_spend": df['spend'].sum() if 'spend' in df.columns else 0,
            "total_impressions": df['impressions'].sum() if 'impressions' in df.columns else 0,
            "total_clicks": df['clicks'].sum() if 'clicks' in df.columns else 0,
            "average_ctr": df['ctr'].mean() if 'ctr' in df.columns else 0,
            "average_cpc": df['cpc'].mean() if 'cpc' in df.columns else 0,
            "average_cpm": df['cpm'].mean() if 'cpm' in df.columns else 0,
            "average_frequency": df['frequency'].mean() if 'frequency' in df.columns else 0,
        }
        
        # Performance insights
        if 'ctr' in df.columns:
            summary["high_performing_campaigns"] = len(df[df['ctr'] > 2])
            summary["low_performing_campaigns"] = len(df[df['ctr'] < 0.5])
        
        if 'frequency' in df.columns:
            summary["high_frequency_campaigns"] = len(df[df['frequency'] > 4])
            
        # Budget efficiency
        if 'spend' in df.columns and 'clicks' in df.columns:
            total_spend = df['spend'].sum()
            total_clicks = df['clicks'].sum()
            summary["overall_cpc"] = total_spend / max(total_clicks, 1)
            
        return summary
        
    except Exception as e:
        logger.error(f"Error generating performance summary: {e}")
        return {"error": f"Failed to generate summary: {str(e)}"}

def detect_anomalies(insights_data: List[Dict]) -> List[Dict[str, Any]]:
    """
    Detect performance anomalies and unusual patterns in campaign data.
    
    Args:
        insights_data: Campaign performance data
        
    Returns:
        List of detected anomalies with descriptions
    """
    try:
        anomalies = []
        df = pd.DataFrame(insights_data)
        
        if df.empty:
            return anomalies
        
        # Convert numeric columns
        numeric_columns = ['spend', 'impressions', 'clicks', 'ctr', 'cpc', 'frequency']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # CTR anomalies
        if 'ctr' in df.columns:
            mean_ctr = df['ctr'].mean()
            std_ctr = df['ctr'].std()
            
            # Find outliers (more than 2 standard deviations from mean)
            outliers = df[abs(df['ctr'] - mean_ctr) > 2 * std_ctr]
            for _, row in outliers.iterrows():
                anomalies.append({
                    "type": "CTR Anomaly",
                    "campaign": row.get('campaign_name', row.get('campaign_id', 'Unknown')),
                    "description": f"CTR of {row['ctr']:.2f}% is {'significantly higher' if row['ctr'] > mean_ctr else 'significantly lower'} than average ({mean_ctr:.2f}%)",
                    "severity": "High" if abs(row['ctr'] - mean_ctr) > 3 * std_ctr else "Medium"
                })
        
        # High frequency warnings
        if 'frequency' in df.columns:
            high_freq = df[df['frequency'] > 5]
            for _, row in high_freq.iterrows():
                anomalies.append({
                    "type": "Ad Fatigue Risk",
                    "campaign": row.get('campaign_name', row.get('campaign_id', 'Unknown')),
                    "description": f"High frequency of {row['frequency']:.1f} indicates potential ad fatigue",
                    "severity": "High" if row['frequency'] > 8 else "Medium"
                })
        
        # Spend efficiency anomalies
        if 'spend' in df.columns and 'clicks' in df.columns:
            df['calculated_cpc'] = df['spend'] / df['clicks'].replace(0, 1)
            mean_cpc = df['calculated_cpc'].mean()
            high_cpc = df[df['calculated_cpc'] > mean_cpc * 2]
            
            for _, row in high_cpc.iterrows():
                if row['clicks'] > 0:  # Only flag if there are actual clicks
                    anomalies.append({
                        "type": "High CPC Alert",
                        "campaign": row.get('campaign_name', row.get('campaign_id', 'Unknown')),
                        "description": f"CPC of ${row['calculated_cpc']:.2f} is significantly higher than average (${mean_cpc:.2f})",
                        "severity": "Medium"
                    })
        
        return anomalies
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        return []

def generate_optimization_recommendations(insights_data: List[Dict]) -> List[Dict[str, Any]]:
    """
    Generate specific optimization recommendations based on campaign performance.
    
    Args:
        insights_data: Campaign performance data
        
    Returns:
        List of optimization recommendations
    """
    try:
        recommendations = []
        df = pd.DataFrame(insights_data)
        
        if df.empty:
            return recommendations
        
        # Convert numeric columns
        numeric_columns = ['spend', 'impressions', 'clicks', 'ctr', 'cpc', 'frequency']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Low CTR campaigns
        if 'ctr' in df.columns:
            low_ctr = df[df['ctr'] < 1.0]
            if not low_ctr.empty:
                recommendations.append({
                    "type": "Creative Optimization",
                    "priority": "High",
                    "description": f"{len(low_ctr)} campaigns have CTR below 1.0%",
                    "action": "Test new ad creatives, headlines, or call-to-action buttons",
                    "expected_impact": "10-30% CTR improvement"
                })
        
        # High frequency campaigns
        if 'frequency' in df.columns:
            high_freq = df[df['frequency'] > 3.5]
            if not high_freq.empty:
                recommendations.append({
                    "type": "Audience Expansion",
                    "priority": "High",
                    "description": f"{len(high_freq)} campaigns showing ad fatigue (frequency > 3.5)",
                    "action": "Expand audiences or refresh creatives to reduce frequency",
                    "expected_impact": "Improved CTR and lower CPC"
                })
        
        # Budget reallocation opportunities
        if 'spend' in df.columns and 'ctr' in df.columns:
            high_performers = df[(df['ctr'] > df['ctr'].median()) & (df['spend'] > 0)]
            if not high_performers.empty:
                recommendations.append({
                    "type": "Budget Reallocation",
                    "priority": "Medium",
                    "description": f"{len(high_performers)} campaigns performing above median CTR",
                    "action": "Increase budget for high-performing campaigns",
                    "expected_impact": "Improved overall ROAS"
                })
        
        # CPC optimization
        if 'cpc' in df.columns:
            high_cpc = df[df['cpc'] > df['cpc'].quantile(0.75)]
            if not high_cpc.empty:
                recommendations.append({
                    "type": "Bid Optimization",
                    "priority": "Medium",
                    "description": f"{len(high_cpc)} campaigns with high CPC (top quartile)",
                    "action": "Review and optimize bidding strategies",
                    "expected_impact": "5-15% CPC reduction"
                })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return []