import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User, UserRole
from app.auth import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_reviews.db"
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
def manager_token(client):
    """Create manager user and return auth token"""
    # Register manager
    client.post(
        "/auth/register",
        json={
            "username": "manager",
            "email": "manager@test.com",
            "password": "managerpass",
            "role": "Manager"
        }
    )
    
    # Login
    response = client.post(
        "/auth/login",
        data={
            "username": "manager",
            "password": "managerpass"
        }
    )
    
    return response.json()["access_token"]


@pytest.fixture
def staff_token(client):
    """Create staff user and return auth token"""
    # Register staff
    client.post(
        "/auth/register",
        json={
            "username": "staff",
            "email": "staff@test.com",
            "password": "staffpass",
            "role": "Staff"
        }
    )
    
    # Login
    response = client.post(
        "/auth/login",
        data={
            "username": "staff",
            "password": "staffpass"
        }
    )
    
    return response.json()["access_token"]


class TestReviewEndpoints:
    """Test suite for review endpoints"""
    
    def test_ingest_reviews_success(self, client, manager_token):
        """Test successful review ingestion by manager"""
        response = client.post(
            "/ingest-reviews",
            json={
                "hotel_id": "ChIJtest123",
                "limit": 5
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert "task_id" in data
        assert data["hotel_id"] == "ChIJtest123"
    
    def test_ingest_reviews_staff_forbidden(self, client, staff_token):
        """Test that staff cannot trigger review ingestion"""
        response = client.post(
            "/ingest-reviews",
            json={
                "hotel_id": "ChIJtest123",
                "limit": 5
            },
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        
        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()
    
    def test_ingest_reviews_no_auth(self, client):
        """Test ingestion without authentication"""
        response = client.post(
            "/ingest-reviews",
            json={
                "hotel_id": "ChIJtest123",
                "limit": 5
            }
        )
        
        assert response.status_code == 401
    
    def test_ingest_reviews_invalid_limit(self, client, manager_token):
        """Test ingestion with invalid limit"""
        response = client.post(
            "/ingest-reviews",
            json={
                "hotel_id": "ChIJtest123",
                "limit": 150  # Exceeds max of 100
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_critical_reviews_staff(self, client, staff_token):
        """Test staff can view critical reviews"""
        response = client.get(
            "/critical-reviews",
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_critical_reviews_manager(self, client, manager_token):
        """Test manager can view critical reviews"""
        response = client.get(
            "/critical-reviews",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_critical_reviews_no_auth(self, client):
        """Test critical reviews requires authentication"""
        response = client.get("/critical-reviews")
        
        assert response.status_code == 401
    
    def test_get_task_status(self, client, manager_token):
        """Test getting task status"""
        # First create a task
        ingest_response = client.post(
            "/ingest-reviews",
            json={
                "hotel_id": "ChIJtest123",
                "limit": 5
            },
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        task_id = ingest_response.json()["task_id"]
        
        # Check task status
        response = client.get(
            f"/task-status/{task_id}",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_get_task_status_invalid_id(self, client, manager_token):
        """Test getting status of non-existent task"""
        response = client.get(
            "/task-status/invalid-task-id",
            headers={"Authorization": f"Bearer {manager_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_found"