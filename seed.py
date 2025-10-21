from sqlalchemy.orm import Session
from datetime import datetime
from app.database import SessionLocal
from app.models import User, Review, UserRole, SentimentType, UrgencyType
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)



def seed_data():
    db: Session = SessionLocal()

    # Clear existing data (optional)
    db.query(Review).delete()
    db.query(User).delete()

    # --- USERS ---
    users = [
        User(
            username="manager_john",
            email="john.manager@hotel.com",
            hashed_password=get_password_hash("SecurePass123!"),
            role=UserRole.MANAGER,
        ),
        User(
            username="staff_emma",
            email="emma.staff@hotel.com",
            hashed_password=get_password_hash("Staff@2024"),
            role=UserRole.STAFF,
        ),
    ]

    db.add_all(users)
    db.commit()

    # Fetch manager ID for reviews
    manager = db.query(User).filter_by(username="manager_john").first()

    # --- REVIEWS ---
    reviews = [
        Review(
            hotel_id="H001",
            review_text="The room was spotless and the staff were incredibly helpful.",
            author="Alice",
            rating=4.8,
            review_date=datetime(2025, 10, 10),
            sentiment=SentimentType.POSITIVE,
            topics="Cleanliness, Service",
            urgency=UrgencyType.STANDARD,
            processed_by=manager.id,
        ),
        Review(
            hotel_id="H002",
            review_text="Air conditioning was broken, and the food was disappointing.",
            author="Michael",
            rating=2.1,
            review_date=datetime(2025, 10, 8),
            sentiment=SentimentType.NEGATIVE,
            topics="Maintenance, Food",
            urgency=UrgencyType.CRITICAL,
            processed_by=manager.id,
        ),
        Review(
            hotel_id="H003",
            review_text="Average stay, nothing special but nothing terrible either.",
            author="Priya",
            rating=3.0,
            review_date=datetime(2025, 10, 12),
            sentiment=SentimentType.NEUTRAL,
            topics="Comfort",
            urgency=UrgencyType.STANDARD,
            processed_by=manager.id,
        ),
    ]

    db.add_all(reviews)
    db.commit()

    print("✅ Seed data inserted successfully!")


if __name__ == "__main__":
    seed_data()
