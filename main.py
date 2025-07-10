import logging
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List

import crud
import models
import schemas
import facebook_api
import llm_service
import strategist_llm_service
from database import SessionLocal, AsyncSessionLocal, sync_engine, Base
from config import settings
from logging_config import setup_logging

# Setup structured logging
setup_logging()
logger = logging.getLogger(__name__)

# Create all tables in the database (including new conversation tables)
# Base.metadata.create_all(bind=sync_engine)

app = FastAPI(
    title="Campanion AI Marketing Assistant",
    description="Enhanced AI-powered marketing coach with comprehensive analytics, strategy guidance, and performance optimization.",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000", 
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# --- Database Dependencies ---
def get_db():
    """Synchronous DB session for all endpoints needing it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_async_db():
    """Asynchronous DB session for API endpoints."""
    async with AsyncSessionLocal() as session:
        yield session

# --- Background task for data synchronization ---
def sync_data_task(db: Session):
    """Enhanced background task to sync data from Facebook API to the database."""
    try:
        logger.info("🛠 Starting enhanced Facebook Ads data sync...")
        df_campaigns = facebook_api.fetch_campaigns()
        if df_campaigns.empty:
            logger.warning("⚠️ No campaigns found to sync.")
            return

        all_campaign_ids = df_campaigns["id"].tolist()
        df_insights = facebook_api.fetch_insights_in_batch(all_campaign_ids)
        df_final = facebook_api.process_and_merge_data(df_campaigns, df_insights)

        if df_final.empty or "campaign_id" not in df_final.columns:
            logger.error("❌ Data processing resulted in an empty dataframe or missing 'campaign_id'.")
            return

        insights_to_upsert = [schemas.CampaignInsightCreate(**row) for row in df_final.to_dict("records")]
        crud.upsert_campaign_insights(db, insights=insights_to_upsert)
        logger.info("✅ Enhanced data sync complete with optimization analysis.")
    except Exception as e:
        logger.exception(f"🔥 Error during enhanced background data sync task: {e}")

# -----------------------------------------------------------
# Enhanced API Routes
# -----------------------------------------------------------

@app.get("/health", response_model=schemas.HealthCheck)
def health_check():
    """Enhanced health check endpoint with system status."""
    return {"status": "ok", "version": "4.0.0", "features": ["AI Strategy", "Data Analytics", "Performance Optimization"]}

@app.post("/sync-facebook-ads/", response_model=schemas.SyncResponse, status_code=202)
async def trigger_facebook_sync(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Enhanced Facebook Ads data synchronization with performance analysis."""
    background_tasks.add_task(sync_data_task, db)
    return {"status": "success", "message": "Enhanced Facebook Ads data sync with analytics scheduled in the background."}

# --- Enhanced Pipeline 1: Advanced Data-Driven Insights ---
@app.post("/query-insights/", response_model=schemas.LLMQueryResponse)
async def query_insights_with_llm(
    request: schemas.LLMQueryRequest,
    analysis_type: str = Query("standard", description="Type of analysis: standard, forensic, trend, efficiency, creative"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Enhanced campaign data analysis with specialized analytical frameworks.
    Supports multiple analysis types: standard, forensic, trend, efficiency, creative.
    """
    logger.info(f"Received {analysis_type} analysis query: '{request.query}'")
    stmt = select(models.CampaignInsight)
    result = await db.execute(stmt)
    insights = result.scalars().all()

    if not insights:
        logger.warning("No campaign insights found in the database for analysis.")
        raise HTTPException(status_code=404, detail="No campaign insights found. Please run a sync first.")

    insights_dicts = [insight.to_dict() for insight in insights]
    logger.info(f"📊 Performing {analysis_type} analysis on {len(insights_dicts)} records.")

    llm_response = llm_service.get_insights_from_llm(
        query=request.query,
        insights_data=insights_dicts,
        analysis_type=analysis_type
    )
    return schemas.LLMQueryResponse(response=llm_response)

# --- New Advanced Analytics Endpoints ---
@app.get("/analytics/performance-summary")
async def get_performance_summary(db: AsyncSession = Depends(get_async_db)):
    """Get comprehensive performance summary with key metrics and insights."""
    stmt = select(models.CampaignInsight)
    result = await db.execute(stmt)
    insights = result.scalars().all()
    
    if not insights:
        raise HTTPException(status_code=404, detail="No campaign data available for summary.")
    
    insights_dicts = [insight.to_dict() for insight in insights]
    summary = llm_service.generate_performance_summary(insights_dicts)
    
    return {"summary": summary, "total_campaigns": len(insights_dicts)}

@app.get("/analytics/anomalies")
async def detect_performance_anomalies(db: AsyncSession = Depends(get_async_db)):
    """Detect performance anomalies and unusual patterns in campaign data."""
    stmt = select(models.CampaignInsight)
    result = await db.execute(stmt)
    insights = result.scalars().all()
    
    if not insights:
        raise HTTPException(status_code=404, detail="No campaign data available for anomaly detection.")
    
    insights_dicts = [insight.to_dict() for insight in insights]
    anomalies = llm_service.detect_anomalies(insights_dicts)
    
    return {"anomalies": anomalies, "total_detected": len(anomalies)}

@app.get("/analytics/recommendations")
async def get_optimization_recommendations(db: AsyncSession = Depends(get_async_db)):
    """Generate specific optimization recommendations based on campaign performance."""
    stmt = select(models.CampaignInsight)
    result = await db.execute(stmt)
    insights = result.scalars().all()
    
    if not insights:
        raise HTTPException(status_code=404, detail="No campaign data available for recommendations.")
    
    insights_dicts = [insight.to_dict() for insight in insights]
    recommendations = llm_service.generate_optimization_recommendations(insights_dicts)
    
    return {"recommendations": recommendations, "total_recommendations": len(recommendations)}

# --- Enhanced Pipeline 2: Advanced Conversational Strategist ---
@app.post("/ask-strategist/", response_model=schemas.StrategistQueryResponse)
async def ask_marketing_strategist(
    request: schemas.StrategistQueryRequest, 
    mode: str = Query("auto", description="Strategist mode: auto, conversation, forensic, report, creative, brainstorm, lead_quality, test_analysis, alert"),
    db: Session = Depends(get_db)
):
    """
    Enhanced marketing strategist with specialized modes and contextual intelligence.
    Auto-detects the appropriate mode based on query content, or use explicit mode.
    """
    logger.info(f"Received strategist query in {mode} mode: '{request.query}' for conversation ID: {request.conversation_id}")
    
    conversation = crud.get_or_create_conversation(db, request.conversation_id)
    
    # Reconstruct history for Gemini format
    history_from_db = []
    for turn in conversation.turns:
        history_from_db.append({"role": "user", "parts": [{"text": turn.user_query}]})
        history_from_db.append({"role": "model", "parts": [{"text": turn.model_response}]})

    learnings = crud.get_feedback_summary(db)
    
    # Auto-detect mode if set to "auto"
    if mode == "auto":
        mode = strategist_llm_service.detect_query_mode(request.query)
        logger.info(f"🎯 Auto-detected mode: {mode}")
    
    text_response, _ = await strategist_llm_service.get_strategist_response(
        query=request.query,
        history=history_from_db,
        learnings=learnings,
        mode=mode
    )

    new_turn = crud.add_turn_to_conversation(
        db=db,
        conversation_id=conversation.id,
        query=request.query,
        response=text_response
    )

    # Generate contextual suggestions
    suggestions = await strategist_llm_service.get_contextual_suggestions(request.query, history_from_db)

    return schemas.StrategistQueryResponse(
        response=text_response,
        conversation_id=conversation.id,
        turn_id=new_turn.id,
        detected_mode=mode,
        suggested_followups=suggestions
    )

# --- Enhanced Feedback System ---
@app.post("/feedback/", status_code=200)
def submit_feedback(request: schemas.FeedbackRequest, db: Session = Depends(get_db)):
    """Enhanced feedback submission with detailed analytics."""
    logger.info(f"Received {request.feedback.name} feedback for turn {request.turn_id}")
    turn = crud.update_turn_feedback(db, request.turn_id, request.feedback, request.notes)
    if not turn:
        raise HTTPException(status_code=404, detail="Conversation turn not found.")
    
    # Log detailed feedback for analytics
    feedback_details = {
        "turn_id": turn.id,
        "feedback_type": request.feedback.name,
        "query_length": len(turn.user_query),
        "response_length": len(turn.model_response),
        "has_notes": bool(request.notes)
    }
    logger.info(f"📈 Feedback analytics: {feedback_details}")
    
    return {
        "status": "success", 
        "message": f"Enhanced feedback for turn {turn.id} has been recorded and will improve future responses.",
        "analytics": feedback_details
    }

# --- New Specialized Endpoints ---
@app.post("/strategist/creative-analysis")
async def analyze_creative_performance(
    request: schemas.CreativeAnalysisRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Specialized creative performance analysis with fatigue detection."""
    stmt = select(models.CampaignInsight)
    result = await db.execute(stmt)
    insights = result.scalars().all()
    
    if not insights:
        raise HTTPException(status_code=404, detail="No campaign data available for creative analysis.")
    
    insights_dicts = [insight.to_dict() for insight in insights]
    
    creative_query = f"Analyze creative performance and ad fatigue for: {request.creative_focus}. {request.additional_context}"
    
    analysis = llm_service.get_insights_from_llm(
        query=creative_query,
        insights_data=insights_dicts,
        analysis_type="creative"
    )
    
    return {"analysis": analysis, "focus_area": request.creative_focus}

@app.post("/strategist/forensic-investigation")
async def conduct_forensic_analysis(
    request: schemas.ForensicAnalysisRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Deep-dive forensic analysis for performance issues."""
    stmt = select(models.CampaignInsight)
    result = await db.execute(stmt)
    insights = result.scalars().all()
    
    if not insights:
        raise HTTPException(status_code=404, detail="No campaign data available for forensic analysis.")
    
    insights_dicts = [insight.to_dict() for insight in insights]
    
    forensic_query = f"Conduct forensic investigation of: {request.issue_description}. Time period: {request.time_period}. Additional context: {request.additional_context}"
    
    investigation = llm_service.get_insights_from_llm(
        query=forensic_query,
        insights_data=insights_dicts,
        analysis_type="forensic"
    )
    
    # Detect related anomalies
    anomalies = llm_service.detect_anomalies(insights_dicts)
    
    return {
        "investigation": investigation, 
        "related_anomalies": anomalies,
        "issue_focus": request.issue_description
    }

@app.post("/strategist/generate-report")
async def generate_performance_report(
    request: schemas.ReportGenerationRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """Generate comprehensive performance reports for stakeholders."""
    stmt = select(models.CampaignInsight)
    result = await db.execute(stmt)
    insights = result.scalars().all()
    
    if not insights:
        raise HTTPException(status_code=404, detail="No campaign data available for report generation.")
    
    insights_dicts = [insight.to_dict() for insight in insights]
    
    report_query = f"Generate {request.report_type} performance report for {request.time_period}. Target audience: {request.target_audience}. Include: {', '.join(request.include_sections)}"
    
    report = llm_service.get_insights_from_llm(
        query=report_query,
        insights_data=insights_dicts,
        analysis_type="report"
    )
    
    # Add summary statistics
    summary = llm_service.generate_performance_summary(insights_dicts)
    
    return {
        "report": report,
        "summary_stats": summary,
        "report_metadata": {
            "type": request.report_type,
            "period": request.time_period,
            "audience": request.target_audience,
            "sections": request.include_sections
        }
    }

# --- Conversation Management ---
@app.get("/conversations/{conversation_id}/history")
def get_conversation_history(conversation_id: int, db: Session = Depends(get_db)):
    """Retrieve conversation history with analytics."""
    conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    
    history = []
    for turn in conversation.turns:
        history.append({
            "turn_id": turn.id,
            "user_query": turn.user_query,
            "model_response": turn.model_response,
            "feedback": turn.feedback.name if turn.feedback else None,
            "feedback_notes": turn.feedback_notes,
            "created_at": turn.created_at
        })
    
    return {
        "conversation_id": conversation_id,
        "total_turns": len(history),
        "history": history,
        "created_at": conversation.created_at
    }

@app.get("/analytics/feedback-insights")
def get_feedback_insights(db: Session = Depends(get_db)):
    """Get insights from user feedback patterns."""
    learnings = crud.get_feedback_summary(db, limit=10)
    
    # Get feedback statistics
    total_turns = db.query(models.ConversationTurn).count()
    positive_feedback = db.query(models.ConversationTurn).filter(
        models.ConversationTurn.feedback == models.FeedbackType.positive
    ).count()
    negative_feedback = db.query(models.ConversationTurn).filter(
        models.ConversationTurn.feedback == models.FeedbackType.negative
    ).count()
    
    feedback_rate = (positive_feedback + negative_feedback) / max(total_turns, 1) * 100
    satisfaction_rate = positive_feedback / max(positive_feedback + negative_feedback, 1) * 100
    
    return {
        "learnings": learnings,
        "statistics": {
            "total_interactions": total_turns,
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback,
            "feedback_rate": round(feedback_rate, 2),
            "satisfaction_rate": round(satisfaction_rate, 2)
        }
    }

@app.get("/", include_in_schema=False)
def root():
    """Enhanced root endpoint with feature overview."""
    return {
        "message": "Welcome to Campanion AI Marketing Assistant",
        "version": "4.0.0",
        "features": [
            "Advanced AI Strategy Guidance",
            "Forensic Performance Analysis", 
            "Creative Optimization",
            "Automated Reporting",
            "Anomaly Detection",
            "Predictive Insights"
        ],
        "documentation": "/docs"
    }