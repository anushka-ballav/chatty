from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from models import FeedbackType

# Enhanced base model for campaign insights
class CampaignInsightBase(BaseModel):
    campaign_id: str
    campaign_name: Optional[str] = None
    date_start: Optional[datetime] = None
    date_stop: Optional[datetime] = None
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    status: Optional[str] = None
    effective_status: Optional[str] = None
    spend: Optional[Decimal] = Decimal('0.0')
    reach: Optional[int] = 0
    impressions: Optional[int] = 0
    frequency: Optional[Decimal] = Decimal('0.0')
    clicks: Optional[int] = 0
    cpc: Optional[Decimal] = Decimal('0.0')
    cpm: Optional[Decimal] = Decimal('0.0')
    ctr: Optional[Decimal] = Decimal('0.0')
    unique_clicks: Optional[int] = 0
    unique_ctr: Optional[Decimal] = Decimal('0.0')
    outbound_clicks: Optional[Decimal] = Decimal('0.0')
    unique_outbound_clicks: Optional[Decimal] = Decimal('0.0')
    action_link_click: Optional[Decimal] = Decimal('0.0')
    action_landing_page_view: Optional[Decimal] = Decimal('0.0')
    action_thruplay: Optional[Decimal] = Decimal('0.0')
    action_purchase: Optional[Decimal] = Decimal('0.0')
    cpa_link_click: Optional[Decimal] = Decimal('0.0')
    cpa_landing_page_view: Optional[Decimal] = Decimal('0.0')
    cpa_thruplay: Optional[Decimal] = Decimal('0.0')
    cpa_purchase: Optional[Decimal] = Decimal('0.0')

    class Config:
        from_attributes = True

# Schema for creating new insight records
class CampaignInsightCreate(CampaignInsightBase):
    pass

# Schema for reading insight records (includes the DB id)
class CampaignInsight(CampaignInsightBase):
    id: int

# Enhanced response schemas
class SyncResponse(BaseModel):
    status: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

class HealthCheck(BaseModel):
    status: str
    version: Optional[str] = None
    features: Optional[List[str]] = None

# Enhanced LLM query schemas
class LLMQueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    analysis_preferences: Optional[Dict[str, str]] = None

class LLMQueryResponse(BaseModel):
    response: str
    analysis_type: Optional[str] = None
    confidence_score: Optional[float] = None
    data_points_analyzed: Optional[int] = None

# Enhanced strategist schemas
class StrategistQueryRequest(BaseModel):
    query: str
    conversation_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = None
    preferred_language: Optional[str] = "en"

class StrategistQueryResponse(BaseModel):
    response: str
    conversation_id: int
    turn_id: int
    detected_mode: Optional[str] = None
    suggested_followups: Optional[List[str]] = None
    confidence_score: Optional[float] = None

# Enhanced feedback schemas
class FeedbackRequest(BaseModel):
    turn_id: int
    feedback: FeedbackType
    notes: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

# New specialized analysis schemas
class CreativeAnalysisRequest(BaseModel):
    creative_focus: str = Field(..., description="Specific creative element to analyze (e.g., 'video ads', 'carousel ads', 'headline performance')")
    time_period: Optional[str] = "last_30_days"
    additional_context: Optional[str] = None

class ForensicAnalysisRequest(BaseModel):
    issue_description: str = Field(..., description="Description of the performance issue to investigate")
    time_period: str = Field(..., description="Time period when the issue occurred")
    suspected_causes: Optional[List[str]] = None
    additional_context: Optional[str] = None

class ReportGenerationRequest(BaseModel):
    report_type: str = Field(..., description="Type of report: 'executive', 'detailed', 'weekly', 'monthly'")
    time_period: str = Field(..., description="Reporting period")
    target_audience: str = Field(..., description="Report audience: 'executives', 'marketing_team', 'client'")
    include_sections: List[str] = Field(default=['performance', 'insights', 'recommendations'], description="Sections to include in report")
    custom_metrics: Optional[List[str]] = None

# Analytics and insights schemas
class PerformanceSummary(BaseModel):
    total_campaigns: int
    total_spend: float
    total_impressions: int
    total_clicks: int
    average_ctr: float
    average_cpc: float
    average_cpm: float
    average_frequency: float
    high_performing_campaigns: Optional[int] = None
    low_performing_campaigns: Optional[int] = None
    overall_efficiency_score: Optional[float] = None

class AnomalyDetection(BaseModel):
    anomaly_type: str
    campaign_id: str
    campaign_name: Optional[str] = None
    description: str
    severity: str  # "High", "Medium", "Low"
    detected_at: datetime
    confidence_score: Optional[float] = None

class OptimizationRecommendation(BaseModel):
    recommendation_type: str
    priority: str  # "High", "Medium", "Low"
    description: str
    action: str
    expected_impact: str
    confidence_score: Optional[float] = None
    effort_required: Optional[str] = None

# Conversation and history schemas
class ConversationTurn(BaseModel):
    turn_id: int
    user_query: str
    model_response: str
    feedback: Optional[str] = None
    feedback_notes: Optional[str] = None
    created_at: datetime
    response_time: Optional[float] = None

class ConversationHistory(BaseModel):
    conversation_id: int
    total_turns: int
    history: List[ConversationTurn]
    created_at: datetime
    last_activity: datetime

# Advanced analytics schemas
class TrendAnalysis(BaseModel):
    metric_name: str
    time_series_data: List[Dict[str, Any]]
    trend_direction: str  # "increasing", "decreasing", "stable", "volatile"
    seasonal_patterns: Optional[List[str]] = None
    forecast: Optional[List[Dict[str, Any]]] = None

class CompetitiveInsight(BaseModel):
    insight_type: str
    description: str
    confidence_level: str
    supporting_data: Dict[str, Any]
    actionable_recommendation: str

class CreativePerformanceAnalysis(BaseModel):
    creative_id: str
    creative_type: str
    performance_score: float
    fatigue_level: str  # "Low", "Medium", "High"
    refresh_recommendation: str
    optimal_frequency: Optional[float] = None

# Alert and notification schemas
class AlertConfiguration(BaseModel):
    alert_type: str
    threshold_value: float
    comparison_operator: str  # "greater_than", "less_than", "equals"
    notification_channels: List[str]
    is_active: bool = True

class AlertNotification(BaseModel):
    alert_id: str
    alert_type: str
    campaign_id: str
    metric_name: str
    current_value: float
    threshold_value: float
    severity: str
    message: str
    triggered_at: datetime
    auto_resolved: bool = False

# Lead quality analysis schemas
class LeadQualityAnalysis(BaseModel):
    total_leads: int
    duplicate_leads: int
    suspicious_leads: int
    quality_score: float
    recommendations: List[str]
    validation_rules_applied: List[str]

class LeadValidationRule(BaseModel):
    rule_name: str
    rule_type: str  # "email_format", "phone_format", "duplicate_check", "domain_check"
    is_active: bool = True
    parameters: Dict[str, Any]

# A/B testing schemas
class ABTestConfiguration(BaseModel):
    test_name: str
    variant_a: Dict[str, Any]
    variant_b: Dict[str, Any]
    success_metric: str
    minimum_sample_size: int
    confidence_level: float = 0.95
    test_duration_days: int

class ABTestResults(BaseModel):
    test_name: str
    variant_a_performance: Dict[str, float]
    variant_b_performance: Dict[str, float]
    winner: Optional[str] = None
    confidence_level: float
    statistical_significance: bool
    recommendation: str
    test_summary: str

# Platform integration schemas
class FacebookAdsConfig(BaseModel):
    ad_account_id: str
    access_token: str
    api_version: str = "v18.0"
    sync_frequency: str = "daily"
    metrics_to_sync: List[str]

class GoogleAdsConfig(BaseModel):
    customer_id: str
    developer_token: str
    client_id: str
    client_secret: str
    refresh_token: str
    sync_frequency: str = "daily"

# Reporting and export schemas
class ReportExportRequest(BaseModel):
    report_id: str
    export_format: str  # "pdf", "excel", "csv", "json"
    include_charts: bool = True
    email_recipients: Optional[List[str]] = None

class ScheduledReport(BaseModel):
    report_name: str
    report_type: str
    schedule_frequency: str  # "daily", "weekly", "monthly"
    recipients: List[str]
    is_active: bool = True
    last_sent: Optional[datetime] = None
    next_scheduled: Optional[datetime] = None

# User preferences and settings schemas
class UserPreferences(BaseModel):
    preferred_language: str = "en"
    timezone: str = "UTC"
    notification_preferences: Dict[str, bool]
    dashboard_layout: Dict[str, Any]
    analysis_depth: str = "standard"  # "basic", "standard", "advanced"

class SystemConfiguration(BaseModel):
    auto_sync_enabled: bool = True
    alert_thresholds: Dict[str, float]
    ai_model_preferences: Dict[str, str]
    data_retention_days: int = 365
    performance_optimization_enabled: bool = True