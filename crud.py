from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import func, desc, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import models
import schemas
import logging

logger = logging.getLogger(__name__)

def upsert_campaign_insights(db: Session, insights: List[schemas.CampaignInsightCreate]):
    """Enhanced bulk upsert for campaign insights with performance tracking."""

    if not insights:
        logger.info("🚫 No insights to upsert. Skipping database operation.")
        return

    now = datetime.utcnow()
    insights_dicts = [
        {**i.model_dump(exclude_unset=True), "synced_at": now}
        for i in insights
    ]

    valid_insights = [d for d in insights_dicts if 'campaign_id' in d and 'date_start' in d]
    if not valid_insights:
        logger.warning("⚠️ No valid records to upsert after filtering.")
        return

    table = models.CampaignInsight.__table__
    stmt = insert(table).values(valid_insights)

    update_cols = {
        c.name: getattr(stmt.excluded, c.name)
        for c in table.columns
        if c.name not in ["id", "campaign_id", "date_start", "synced_at"]
    }
    update_cols["synced_at"] = func.now()

    on_conflict_stmt = stmt.on_conflict_do_update(
        index_elements=["campaign_id", "date_start"],
        set_=update_cols
    )

    try:
        result = db.execute(on_conflict_stmt)
        db.commit()
        logger.info(f"✅ Successfully upserted {len(valid_insights)} records.")
        return {"upserted_count": len(valid_insights), "status": "success"}
    except Exception as e:
        logger.error("🔥 Database upsert failed:", exc_info=True)
        db.rollback()
        raise

def get_or_create_conversation(db: Session, conversation_id: Optional[int] = None) -> models.Conversation:
    """Enhanced conversation management with analytics tracking."""
    if conversation_id:
        conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
        if conversation:
            return conversation
    
    new_conversation = models.Conversation()
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    logger.info(f"📝 Created new conversation with ID: {new_conversation.id}")
    return new_conversation

def add_turn_to_conversation(db: Session, conversation_id: int, query: str, response: str) -> models.ConversationTurn:
    """Enhanced turn management with performance metrics tracking."""
    turn = models.ConversationTurn(
        conversation_id=conversation_id,
        user_query=query,
        model_response=response
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)
    
    # Log analytics data
    logger.info(f"💬 Added turn {turn.id} to conversation {conversation_id} - Query length: {len(query)}, Response length: {len(response)}")
    return turn

def update_turn_feedback(db: Session, turn_id: int, feedback: schemas.FeedbackType, notes: Optional[str]) -> Optional[models.ConversationTurn]:
    """Enhanced feedback tracking with detailed analytics."""
    turn = db.query(models.ConversationTurn).filter(models.ConversationTurn.id == turn_id).first()
    if turn:
        turn.feedback = feedback
        turn.feedback_notes = notes
        turn.feedback_timestamp = datetime.utcnow()
        db.commit()
        db.refresh(turn)
        
        # Log feedback analytics
        logger.info(f"👍👎 Feedback recorded for turn {turn_id}: {feedback.name} - Notes: {bool(notes)}")
        return turn
    return None

def get_feedback_summary(db: Session, limit: int = 5) -> str:
    """Enhanced feedback analysis with trend identification."""
    positive_feedback = db.query(models.ConversationTurn).filter(
        models.ConversationTurn.feedback == models.FeedbackType.positive
    ).order_by(desc(models.ConversationTurn.created_at)).limit(limit).all()
    
    negative_feedback = db.query(models.ConversationTurn).filter(
        models.ConversationTurn.feedback == models.FeedbackType.negative
    ).order_by(desc(models.ConversationTurn.created_at)).limit(limit).all()
    
    learnings = "### Enhanced Learning Insights from User Feedback:\n"
    
    if positive_feedback:
        learnings += "#### ✅ Successful Response Patterns (replicate these approaches):\n"
        for turn in positive_feedback:
            query_preview = turn.user_query[:80] + "..." if len(turn.user_query) > 80 else turn.user_query
            response_preview = turn.model_response[:100] + "..." if len(turn.model_response) > 100 else turn.model_response
            learnings += f"- **Query**: '{query_preview}'\n"
            learnings += f"  **Successful Response Style**: '{response_preview}'\n"
            if turn.feedback_notes:
                learnings += f"  **User Notes**: {turn.feedback_notes}\n"
            learnings += "\n"
            
    if negative_feedback:
        learnings += "#### ❌ Response Patterns to Avoid:\n"
        for turn in negative_feedback:
            query_preview = turn.user_query[:80] + "..." if len(turn.user_query) > 80 else turn.user_query
            response_preview = turn.model_response[:100] + "..." if len(turn.model_response) > 100 else turn.model_response
            learnings += f"- **Query**: '{query_preview}'\n"
            learnings += f"  **Problematic Response**: '{response_preview}'\n"
            if turn.feedback_notes:
                learnings += f"  **User Feedback**: {turn.feedback_notes}\n"
            learnings += "\n"

    if not positive_feedback and not negative_feedback:
        return ""

    # Add summary statistics
    total_feedback = len(positive_feedback) + len(negative_feedback)
    satisfaction_rate = len(positive_feedback) / total_feedback * 100 if total_feedback > 0 else 0
    learnings += f"\n#### 📊 Feedback Analytics:\n"
    learnings += f"- Recent satisfaction rate: {satisfaction_rate:.1f}%\n"
    learnings += f"- Total feedback samples analyzed: {total_feedback}\n"

    return learnings

# Enhanced analytics functions
def get_conversation_analytics(db: Session, days: int = 30) -> Dict[str, Any]:
    """Get comprehensive conversation analytics."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    total_conversations = db.query(models.Conversation).filter(
        models.Conversation.created_at >= cutoff_date
    ).count()
    
    total_turns = db.query(models.ConversationTurn).join(models.Conversation).filter(
        models.Conversation.created_at >= cutoff_date
    ).count()
    
    feedback_stats = db.query(
        models.ConversationTurn.feedback,
        func.count(models.ConversationTurn.id)
    ).join(models.Conversation).filter(
        models.Conversation.created_at >= cutoff_date,
        models.ConversationTurn.feedback.isnot(None)
    ).group_by(models.ConversationTurn.feedback).all()
    
    # Calculate average turns per conversation
    avg_turns = total_turns / max(total_conversations, 1)
    
    # Process feedback statistics
    feedback_breakdown = {feedback.name: count for feedback, count in feedback_stats}
    total_feedback = sum(feedback_breakdown.values())
    satisfaction_rate = feedback_breakdown.get('positive', 0) / max(total_feedback, 1) * 100
    
    return {
        "period_days": days,
        "total_conversations": total_conversations,
        "total_turns": total_turns,
        "average_turns_per_conversation": round(avg_turns, 2),
        "feedback_breakdown": feedback_breakdown,
        "total_feedback_received": total_feedback,
        "satisfaction_rate": round(satisfaction_rate, 2),
        "feedback_participation_rate": round(total_feedback / max(total_turns, 1) * 100, 2)
    }

def get_performance_insights(db: Session, days: int = 7) -> List[Dict[str, Any]]:
    """Get recent campaign performance insights."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    insights = db.query(models.CampaignInsight).filter(
        models.CampaignInsight.date_start >= cutoff_date
    ).order_by(desc(models.CampaignInsight.date_start)).all()
    
    return [insight.to_dict() for insight in insights]

def get_top_performing_campaigns(db: Session, metric: str = "ctr", limit: int = 10) -> List[Dict[str, Any]]:
    """Get top performing campaigns by specified metric."""
    query = db.query(models.CampaignInsight)
    
    if metric == "ctr":
        query = query.order_by(desc(models.CampaignInsight.ctr))
    elif metric == "roas":
        # Calculate ROAS if we have purchase data
        query = query.filter(
            models.CampaignInsight.action_purchase > 0,
            models.CampaignInsight.spend > 0
        ).order_by(desc(models.CampaignInsight.action_purchase))
    elif metric == "efficiency":
        query = query.order_by(models.CampaignInsight.cpc.asc())
    else:
        query = query.order_by(desc(getattr(models.CampaignInsight, metric, models.CampaignInsight.ctr)))
    
    campaigns = query.limit(limit).all()
    return [campaign.to_dict() for campaign in campaigns]

def detect_campaign_anomalies(db: Session, threshold_multiplier: float = 2.0) -> List[Dict[str, Any]]:
    """Detect campaigns with anomalous performance."""
    anomalies = []
    
    # Get recent campaign data
    recent_insights = db.query(models.CampaignInsight).filter(
        models.CampaignInsight.date_start >= datetime.utcnow() - timedelta(days=30)
    ).all()
    
    if not recent_insights:
        return anomalies
    
    # Calculate metrics for anomaly detection
    metrics = ['ctr', 'cpc', 'frequency']
    for metric in metrics:
        values = [getattr(insight, metric) for insight in recent_insights if getattr(insight, metric, 0) > 0]
        if not values:
            continue
            
        mean_value = sum(values) / len(values)
        variance = sum((x - mean_value) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        
        # Find outliers
        for insight in recent_insights:
            value = getattr(insight, metric, 0)
            if value > 0 and abs(value - mean_value) > threshold_multiplier * std_dev:
                anomalies.append({
                    "campaign_id": insight.campaign_id,
                    "campaign_name": insight.campaign_name,
                    "metric": metric,
                    "value": float(value),
                    "mean": round(mean_value, 4),
                    "deviation": round(abs(value - mean_value) / std_dev, 2),
                    "severity": "High" if abs(value - mean_value) > 3 * std_dev else "Medium",
                    "date": insight.date_start
                })
    
    return anomalies

def get_campaign_trends(db: Session, campaign_id: str, days: int = 30) -> Dict[str, List]:
    """Get performance trends for a specific campaign."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    insights = db.query(models.CampaignInsight).filter(
        models.CampaignInsight.campaign_id == campaign_id,
        models.CampaignInsight.date_start >= cutoff_date
    ).order_by(models.CampaignInsight.date_start).all()
    
    trends = {
        "dates": [],
        "spend": [],
        "impressions": [],
        "clicks": [],
        "ctr": [],
        "cpc": [],
        "conversions": []
    }
    
    for insight in insights:
        trends["dates"].append(insight.date_start.isoformat() if insight.date_start else None)
        trends["spend"].append(float(insight.spend or 0))
        trends["impressions"].append(int(insight.impressions or 0))
        trends["clicks"].append(int(insight.clicks or 0))
        trends["ctr"].append(float(insight.ctr or 0))
        trends["cpc"].append(float(insight.cpc or 0))
        trends["conversions"].append(float(insight.action_purchase or 0))
    
    return trends

def get_budget_utilization(db: Session, days: int = 7) -> Dict[str, Any]:
    """Analyze budget utilization across campaigns."""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    campaign_spend = db.query(
        models.CampaignInsight.campaign_id,
        models.CampaignInsight.campaign_name,
        func.sum(models.CampaignInsight.spend).label('total_spend'),
        func.avg(models.CampaignInsight.ctr).label('avg_ctr'),
        func.sum(models.CampaignInsight.clicks).label('total_clicks')
    ).filter(
        models.CampaignInsight.date_start >= cutoff_date
    ).group_by(
        models.CampaignInsight.campaign_id,
        models.CampaignInsight.campaign_name
    ).all()
    
    total_spend = sum(row.total_spend or 0 for row in campaign_spend)
    
    budget_analysis = []
    for row in campaign_spend:
        spend_share = (row.total_spend or 0) / max(total_spend, 1) * 100
        efficiency_score = (row.avg_ctr or 0) * (row.total_clicks or 0) / max(row.total_spend or 1, 1)
        
        budget_analysis.append({
            "campaign_id": row.campaign_id,
            "campaign_name": row.campaign_name,
            "total_spend": float(row.total_spend or 0),
            "spend_share_percent": round(spend_share, 2),
            "avg_ctr": round(float(row.avg_ctr or 0), 4),
            "total_clicks": int(row.total_clicks or 0),
            "efficiency_score": round(efficiency_score, 4)
        })
    
    # Sort by efficiency score
    budget_analysis.sort(key=lambda x: x["efficiency_score"], reverse=True)
    
    return {
        "total_spend": float(total_spend),
        "period_days": days,
        "campaign_breakdown": budget_analysis,
        "top_performing_campaign": budget_analysis[0] if budget_analysis else None,
        "recommendations": generate_budget_recommendations(budget_analysis)
    }

def generate_budget_recommendations(budget_analysis: List[Dict]) -> List[str]:
    """Generate budget optimization recommendations."""
    recommendations = []
    
    if not budget_analysis:
        return ["No campaign data available for budget analysis."]
    
    # Find top and bottom performers
    top_performers = [c for c in budget_analysis[:3] if c["efficiency_score"] > 0]
    bottom_performers = [c for c in budget_analysis[-3:] if c["efficiency_score"] < budget_analysis[0]["efficiency_score"] * 0.5]
    
    if top_performers:
        recommendations.append(f"🔥 Scale budget for top performer: {top_performers[0]['campaign_name']} (Efficiency: {top_performers[0]['efficiency_score']:.2f})")
    
    if bottom_performers:
        recommendations.append(f"⚠️ Review budget allocation for: {bottom_performers[-1]['campaign_name']} (Low efficiency: {bottom_performers[-1]['efficiency_score']:.2f})")
    
    # Budget concentration analysis
    total_campaigns = len(budget_analysis)
    top_3_spend_share = sum(c["spend_share_percent"] for c in budget_analysis[:3])
    
    if top_3_spend_share > 80:
        recommendations.append("📊 Budget is highly concentrated - consider diversifying across more campaigns")
    elif top_3_spend_share < 50:
        recommendations.append("💡 Budget is well-distributed - consider consolidating to top performers")
    
    return recommendations

# Enhanced search and filtering
def search_conversations(db: Session, query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search conversations by query content."""
    turns = db.query(models.ConversationTurn).filter(
        or_(
            models.ConversationTurn.user_query.ilike(f"%{query}%"),
            models.ConversationTurn.model_response.ilike(f"%{query}%")
        )
    ).order_by(desc(models.ConversationTurn.created_at)).limit(limit).all()
    
    return [{
        "turn_id": turn.id,
        "conversation_id": turn.conversation_id,
        "user_query": turn.user_query,
        "model_response": turn.model_response[:200] + "..." if len(turn.model_response) > 200 else turn.model_response,
        "created_at": turn.created_at,
        "feedback": turn.feedback.name if turn.feedback else None
    } for turn in turns]

def get_frequent_queries(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Get most frequently asked query patterns."""
    # This is a simplified version - in production, you'd want more sophisticated pattern matching
    query_words = db.query(
        func.unnest(func.string_to_array(models.ConversationTurn.user_query, ' ')).label('word'),
    ).filter(
        func.length(models.ConversationTurn.user_query) > 10
    ).subquery()
    
    # Count word frequency (simplified approach)
    word_counts = db.query(
        query_words.c.word,
        func.count(query_words.c.word).label('frequency')
    ).group_by(query_words.c.word).order_by(desc('frequency')).limit(limit).all()
    
    return [{"word": word, "frequency": freq} for word, freq in word_counts if len(word) > 3]