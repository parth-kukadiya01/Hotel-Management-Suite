from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models import UserRole, SentimentType, UrgencyType


# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    role: UserRole = UserRole.STAFF


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[UserRole] = None


# Review Schemas
class ReviewBase(BaseModel):
    hotel_id: str
    review_text: str
    author: Optional[str] = None
    rating: Optional[float] = None
    review_date: Optional[datetime] = None


class ReviewCreate(ReviewBase):
    pass


class ReviewResponse(ReviewBase):
    id: int
    sentiment: Optional[SentimentType]
    topics: Optional[str]
    urgency: Optional[UrgencyType]
    processed_at: datetime
    
    class Config:
        from_attributes = True


class CriticalReviewResponse(BaseModel):
    id: int
    hotel_id: str
    review_text: str
    author: Optional[str]
    rating: Optional[float]
    review_date: Optional[datetime]
    sentiment: Optional[SentimentType]
    topics: Optional[str]
    urgency: UrgencyType
    processed_at: datetime
    
    class Config:
        from_attributes = True


# Ingestion Request
class IngestReviewsRequest(BaseModel):
    hotel_id: str = Field(..., description="Google Place ID or hotel identifier")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Number of reviews to fetch")


class IngestReviewsResponse(BaseModel):
    status: str
    message: str
    task_id: str
    hotel_id: str


# Dashboard Metrics
class SentimentDistribution(BaseModel):
    positive_percent: float
    negative_percent: float
    neutral_percent: float
    total_reviews: int


class TopicBreakdown(BaseModel):
    topic: str
    count: int
    percentage: float


class DashboardMetrics(BaseModel):
    sentiment_distribution: SentimentDistribution
    topic_breakdown: List[TopicBreakdown]
    escalation_rate: float
    total_reviews: int
    critical_reviews_count: int


# LLM Analysis Result
class LLMAnalysisResult(BaseModel):
    sentiment: SentimentType
    topics: List[str]
    urgency: UrgencyType
    reasoning: Optional[str] = None