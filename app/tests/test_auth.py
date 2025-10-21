import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import UserRole

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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


class TestAuthentication:
    """Test suite for authentication endpoints"""
    
    def test_register_user_success(self, client):
        """Test successful user registration"""
        response = client.post(
            "/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123",
                "role": "Staff"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["role"] == "Staff"
        assert "id" in data
    
    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username"""
        # Register first user
        client.post(
            "/auth/register",
            json={
                "username": "duplicate",
                "email": "user1@example.com",
                "password": "pass123",
                "role": "Staff"
            }
        )
        
        # Try to register with same username
        response = client.post(
            "/auth/register",
            json={
                "username": "duplicate",
                "email": "user2@example.com",
                "password": "pass456",
                "role": "Staff"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email"""
        # Register first user
        client.post(
            "/auth/register",
            json={
                "username": "user1",
                "email": "duplicate@example.com",
                "password": "pass123",
                "role": "Staff"
            }
        )
        
        # Try to register with same email
        response = client.post(
            "/auth/register",
            json={
                "username": "user2",
                "email": "duplicate@example.com",
                "password": "pass456",
                "role": "Staff"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_login_success(self, client):
        """Test successful login"""
        # Register user
        client.post(
            "/auth/register",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "password123",
                "role": "Manager"
            }
        )
        
        # Login
        response = client.post(
            "/auth/login",
            data={
                "username": "loginuser",
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client):
        """Test login with wrong password"""
        # Register user
        client.post(
            "/auth/register",
            json={
                "username": "wrongpass",
                "email": "wrong@example.com",
                "password": "correctpass",
                "role": "Staff"
            }
        )
        
        # Try login with wrong password
        response = client.post(
            "/auth/login",
            data={
                "username": "wrongpass",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post(
            "/auth/login",
            data={
                "username": "nonexistent",
                "password": "somepass"
            }
        )
        
        assert response.status_code == 401
    
    def test_register_manager_role(self, client):
        """Test registering a manager user"""
        response = client.post(
            "/auth/register",
            json={
                "username": "manager",
                "email": "manager@example.com",
                "password": "managerpass",
                "role": "Manager"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["role"] == "Manager"