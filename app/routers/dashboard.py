from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import Counter
from app.database import get_db
from app.models import User, Review, SentimentType, UrgencyType
from app.schemas import DashboardMetrics, SentimentDistribution, TopicBreakdown
from app.dependencies import get_authenticated_user

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard-metrics", response_model=DashboardMetrics)
def get_dashboard_metrics(
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
   
    total_reviews = db.query(Review).count()
    
    if total_reviews == 0:
        return DashboardMetrics(
            sentiment_distribution=SentimentDistribution(
                positive_percent=0.0,
                negative_percent=0.0,
                neutral_percent=0.0,
                total_reviews=0
            ),
            topic_breakdown=[],
            escalation_rate=0.0,
            total_reviews=0,
            critical_reviews_count=0
        )
    
    # Sentiment distribution
    sentiment_counts = db.query(
        Review.sentiment,
        func.count(Review.id).label('count')
    ).group_by(Review.sentiment).all()
    
    sentiment_dict = {
        SentimentType.POSITIVE: 0,
        SentimentType.NEGATIVE: 0,
        SentimentType.NEUTRAL: 0
    }
    
    for sentiment, count in sentiment_counts:
        if sentiment:
            sentiment_dict[sentiment] = count
    
    sentiment_distribution = SentimentDistribution(
        positive_percent=round((sentiment_dict[SentimentType.POSITIVE] / total_reviews) * 100, 2),
        negative_percent=round((sentiment_dict[SentimentType.NEGATIVE] / total_reviews) * 100, 2),
        neutral_percent=round((sentiment_dict[SentimentType.NEUTRAL] / total_reviews) * 100, 2),
        total_reviews=total_reviews
    )
    
    all_reviews = db.query(Review.topics).filter(Review.topics.isnot(None)).all()
    topic_counter = Counter()
    
    for (topics_str,) in all_reviews:
        if topics_str:
            topics = [t.strip() for t in topics_str.split(',')]
            topic_counter.update(topics)
    
    topic_breakdown = []
    for topic, count in topic_counter.most_common():
        topic_breakdown.append(
            TopicBreakdown(
                topic=topic,
                count=count,
                percentage=round((count / total_reviews) * 100, 2)
            )
        )
    
    critical_count = db.query(Review).filter(
        Review.urgency == UrgencyType.CRITICAL
    ).count()
    
    escalation_rate = round((critical_count / total_reviews) * 100, 2) if total_reviews > 0 else 0.0
    
    return DashboardMetrics(
        sentiment_distribution=sentiment_distribution,
        topic_breakdown=topic_breakdown,
        escalation_rate=escalation_rate,
        total_reviews=total_reviews,
        critical_reviews_count=critical_count
    )