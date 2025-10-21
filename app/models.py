from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class UserRole(str, enum.Enum):
    STAFF = "Staff"
    MANAGER = "Manager"


class SentimentType(str, enum.Enum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"
    NEUTRAL = "Neutral"


class UrgencyType(str, enum.Enum):
    CRITICAL = "Critical"
    STANDARD = "Standard"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.STAFF, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    reviews = relationship("Review", back_populates="processed_by_user")


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(String(100), index=True, nullable=False)
    review_text = Column(Text, nullable=False)
    author = Column(String(100))
    rating = Column(Float)
    review_date = Column(DateTime)
    
    # LLM Analysis Results
    sentiment = Column(SQLEnum(SentimentType), nullable=True)
    topics = Column(Text, nullable=True)  # Stored as comma-separated values
    urgency = Column(SQLEnum(UrgencyType), nullable=True)
    
    # Metadata
    processed_at = Column(DateTime, default=datetime.utcnow)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationship
    processed_by_user = relationship("User", back_populates="reviews")