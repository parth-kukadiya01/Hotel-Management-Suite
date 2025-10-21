import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.main import app
from app.database import Base, get_db
from app.models import User, Review, SentimentType, UrgencyType

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_dashboard.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    """Create user and return auth token"""
    client.post(
        "/auth/register",
        json={
            "username": "testuser",
            "email": "test@test.com",
            "password": "testpass",
            "role": "Staff"
        }
    )
    
    response = client.post(
        "/auth/login",
        data={
            "username": "testuser",
            "password": "testpass"
        }
    )
    
    return response.json()["access_token"]


@pytest.fixture
def sample_reviews():
    """Create sample reviews in database"""
    db = TestingSessionLocal()
    
    reviews = [
        Review(
            hotel_id="hotel1",
            review_text="Great hotel!",
            author="User1",
            rating=5.0,
            review_date=datetime.now(),
            sentiment=SentimentType.POSITIVE,
            topics="Service,Cleanliness",
            urgency=UrgencyType.STANDARD
        ),
        Review(
            hotel_id="hotel1",
            review_text="Found bed bugs!",
            author="User2",
            rating=1.0,
            review_date=datetime.now(),
            sentiment=SentimentType.NEGATIVE,
            topics="Cleanliness",
            urgency=UrgencyType.CRITICAL
        ),
        Review(
            hotel_id="hotel1",
            review_text="Average stay",
            author="User3",
            rating=3.0,
            review_date=datetime.now(),
            sentiment=SentimentType.NEUTRAL,
            topics="Service,Value",
            urgency=UrgencyType.STANDARD
        ),
        Review(
            hotel_id="hotel1",
            review_text="Terrible service",
            author="User4",
            rating=2.0,
            review_date=datetime.now(),
            sentiment=SentimentType.NEGATIVE,
            topics="Service",
            urgency=UrgencyType.STANDARD
        ),
        Review(
            hotel_id="hotel1",
            review_text="Excellent location",
            author="User5",
            rating=4.5,
            review_date=datetime.now(),
            sentiment=SentimentType.POSITIVE,
            topics="Location,Value",
            urgency=UrgencyType.STANDARD
        )
    ]
    
    for review in reviews:
        db.add(review)
    
    db.commit()
    db.close()


class TestDashboardEndpoints:
    """Test suite for dashboard endpoints"""
    
    def test_dashboard_metrics_no_auth(self, client):
        """Test dashboard requires authentication"""
        response = client.get("/dashboard-metrics")
        assert response.status_code == 401
    
    def test_dashboard_metrics_empty(self, client, auth_token):
        """Test dashboard with no reviews"""
        response = client.get(
            "/dashboard-metrics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_reviews"] == 0
        assert data["critical_reviews_count"] == 0
        assert data["escalation_rate"] == 0.0
    
    def test_dashboard_metrics_with_reviews(self, client, auth_token, sample_reviews):
        """Test dashboard with sample reviews"""
        response = client.get(
            "/dashboard-metrics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check total reviews
        assert data["total_reviews"] == 5
        
        # Check sentiment distribution
        sentiment = data["sentiment_distribution"]
        assert sentiment["total_reviews"] == 5
        assert sentiment["positive_percent"] == 40.0  # 2 out of 5
        assert sentiment["negative_percent"] == 40.0  # 2 out of 5
        assert sentiment["neutral_percent"] == 20.0   # 1 out of 5
        
        # Check escalation rate (1 critical out of 5)
        assert data["escalation_rate"] == 20.0
        assert data["critical_reviews_count"] == 1
        
        # Check topic breakdown
        topics = data["topic_breakdown"]
        assert len(topics) > 0
        
        # Verify Service is most common (appears in 4 reviews)
        service_topic = next((t for t in topics if t["topic"] == "Service"), None)
        assert service_topic is not None
        assert service_topic["count"] >= 3
    
    def test_dashboard_metrics_structure(self, client, auth_token, sample_reviews):
        """Test dashboard response structure"""
        response = client.get(
            "/dashboard-metrics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = [
            "sentiment_distribution",
            "topic_breakdown",
            "escalation_rate",
            "total_reviews",
            "critical_reviews_count"
        ]
        
        for field in required_fields:
            assert field in data
        
        # Check sentiment distribution structure
        sentiment = data["sentiment_distribution"]
        assert "positive_percent" in sentiment
        assert "negative_percent" in sentiment
        assert "neutral_percent" in sentiment
        assert "total_reviews" in sentiment
        
        # Check topic breakdown structure
        if len(data["topic_breakdown"]) > 0:
            topic = data["topic_breakdown"][0]
            assert "topic" in topic
            assert "count" in topic
            assert "percentage" in topic
    
    def test_dashboard_percentages_sum_to_100(self, client, auth_token, sample_reviews):
        """Test that sentiment percentages sum to approximately 100%"""
        response = client.get(
            "/dashboard-metrics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        sentiment = data["sentiment_distribution"]
        total_percent = (
            sentiment["positive_percent"] +
            sentiment["negative_percent"] +
            sentiment["neutral_percent"]
        )
        
        # Allow for minor rounding differences
        assert abs(total_percent - 100.0) < 0.1