from sqlalchemy import Column, String, Integer, DateTime, BigInteger, Numeric, ForeignKey, Text, Enum
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy import func
from database import Base
import enum

class CampaignInsight(Base):
    __tablename__ = "campaign_insights"
    __table_args__ = (UniqueConstraint('campaign_id', 'date_start', name='_campaign_date_uc'),)

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(String, index=True, nullable=False)
    campaign_name = Column(String)
    
    date_start = Column(DateTime(timezone=True), nullable=True, index=True)
    date_stop = Column(DateTime(timezone=True), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    stop_time = Column(DateTime(timezone=True), nullable=True)
    
    status = Column(String)
    effective_status = Column(String)

    spend = Column(Numeric(10, 2))
    cpc = Column(Numeric(10, 2))
    cpm = Column(Numeric(10, 2))
    
    reach = Column(BigInteger)
    impressions = Column(BigInteger)
    frequency = Column(Numeric(10, 4))
    clicks = Column(BigInteger)
    ctr = Column(Numeric(10, 4))
    unique_clicks = Column(BigInteger)
    unique_ctr = Column(Numeric(10, 4))
    
    outbound_clicks = Column(Numeric(10, 2))
    unique_outbound_clicks = Column(Numeric(10, 2))

    action_link_click = Column(Numeric(10, 2))
    action_landing_page_view = Column(Numeric(10, 2))
    action_thruplay = Column(Numeric(10, 2))
    action_purchase = Column(Numeric(10, 2))

    cpa_link_click = Column(Numeric(10, 2))
    cpa_landing_page_view = Column(Numeric(10, 2))
    cpa_thruplay = Column(Numeric(10, 2))
    cpa_purchase = Column(Numeric(10, 2))
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

class Conversation(Base):
    """Stores a single, continuous conversation session."""
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    turns = relationship("ConversationTurn", back_populates="conversation")

class FeedbackType(enum.Enum):
    positive = 1
    negative = -1
    neutral = 0

class ConversationTurn(Base):
    """Stores a single turn (a user query and a model response) within a conversation."""
    __tablename__ = "conversation_turns"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    
    user_query = Column(Text, nullable=False)
    model_response = Column(Text, nullable=False)
    
    feedback = Column(Enum(FeedbackType), default=FeedbackType.neutral)
    feedback_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="turns")