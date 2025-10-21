from datetime import datetime, timedelta
import random
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import Review, UrgencyType
from app.services.llm_analyzer import llm_analyzer


class ReviewIngestionService:
    
    def fetch_google_reviews(self, hotel_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        
        sample_reviews = [
            {
                "text": "Amazing stay! The room was spotlessly clean and the staff were incredibly helpful. The location is perfect for exploring the city. Highly recommend!",
                "author": "Sarah Johnson",
                "rating": 5.0,
                "date": datetime.now() - timedelta(days=2)
            },
            {
                "text": "Found bed bugs in the room on the second night. Absolutely disgusting and unacceptable for a hotel of this price. Management was unhelpful. DO NOT STAY HERE!",
                "author": "Michael Chen",
                "rating": 1.0,
                "date": datetime.now() - timedelta(days=1)
            },
            {
                "text": "The hotel was okay. Room was clean but quite small. Breakfast was decent. Location is convenient but parking was expensive.",
                "author": "Emily Rodriguez",
                "rating": 3.0,
                "date": datetime.now() - timedelta(days=3)
            },
            {
                "text": "Terrible experience. Got food poisoning from the hotel restaurant. When I complained, the staff was rude and dismissive. This is a serious health hazard!",
                "author": "David Thompson",
                "rating": 1.0,
                "date": datetime.now() - timedelta(days=5)
            },
            {
                "text": "Lovely hotel with excellent service. The concierge helped us plan our entire itinerary. Rooms are beautifully decorated and very comfortable. Will definitely return!",
                "author": "Jennifer Lee",
                "rating": 5.0,
                "date": datetime.now() - timedelta(days=7)
            },
            {
                "text": "Good value for money. The amenities were basic but functional. Staff was friendly. Could use some renovation but overall a pleasant stay.",
                "author": "Robert Martinez",
                "rating": 4.0,
                "date": datetime.now() - timedelta(days=4)
            },
            {
                "text": "Someone broke into our room and stole valuables while we were at breakfast. Hotel security is non-existent. Police were called but hotel denied responsibility. Avoid at all costs!",
                "author": "Amanda Wilson",
                "rating": 1.0,
                "date": datetime.now() - timedelta(days=6)
            },
            {
                "text": "The location is fantastic, right in the heart of downtown. Easy walking distance to all major attractions. Room was clean and comfortable. Staff was professional.",
                "author": "Christopher Brown",
                "rating": 4.5,
                "date": datetime.now() - timedelta(days=8)
            },
            {
                "text": "Average hotel. Nothing special but nothing terrible either. The room was clean, bed was comfortable. Breakfast options were limited.",
                "author": "Lisa Anderson",
                "rating": 3.5,
                "date": datetime.now() - timedelta(days=9)
            },
            {
                "text": "Exceptional service from start to finish. The staff went above and beyond to make our anniversary special. Beautiful views and amazing amenities. Worth every penny!",
                "author": "James Taylor",
                "rating": 5.0,
                "date": datetime.now() - timedelta(days=10)
            }
        ]
        
        reviews_to_return = random.sample(sample_reviews, min(limit, len(sample_reviews)))
        return reviews_to_return
    
    def process_reviews(self, hotel_id: str, reviews_data: List[Dict[str, Any]], db: Session, user_id: int = None) -> List[Review]:
        
        processed_reviews = []
        
        for review_data in reviews_data:
            analysis = llm_analyzer.analyze_review(review_data["text"])
            
            review = Review(
                hotel_id=hotel_id,
                review_text=review_data["text"],
                author=review_data.get("author"),
                rating=review_data.get("rating"),
                review_date=review_data.get("date"),
                sentiment=analysis.sentiment,
                topics=",".join(analysis.topics),
                urgency=analysis.urgency,
                processed_by=user_id
            )
            
            db.add(review)
            processed_reviews.append(review)
        
        db.commit()
        return processed_reviews


review_ingestion_service = ReviewIngestionService()