import asyncio
import uuid
from typing import Dict
from sqlalchemy.orm import Session
from app.services.review_ingestion import review_ingestion_service
from app.database import SessionLocal


class BackgroundTaskManager:
    
    def __init__(self):
        self.tasks: Dict[str, dict] = {}
    
    def create_task_id(self) -> str:
        return str(uuid.uuid4())
    
    async def ingest_reviews_task(self, task_id: str, hotel_id: str, limit: int, user_id: int):
        self.tasks[task_id] = {
            "status": "processing",
            "hotel_id": hotel_id,
            "message": "Fetching and analyzing reviews..."
        }
        
        try:
            # Create a new database session for this background task
            db = SessionLocal()
            
            try:
                # Fetch reviews
                reviews_data = review_ingestion_service.fetch_google_reviews(hotel_id, limit)
                
                # Process reviews through LLM
                processed_reviews = review_ingestion_service.process_reviews(
                    hotel_id=hotel_id,
                    reviews_data=reviews_data,
                    db=db,
                    user_id=user_id
                )
                
                # Update task status
                self.tasks[task_id] = {
                    "status": "completed",
                    "hotel_id": hotel_id,
                    "message": f"Successfully processed {len(processed_reviews)} reviews",
                    "reviews_count": len(processed_reviews)
                }
                
            finally:
                db.close()
                
        except Exception as e:
            self.tasks[task_id] = {
                "status": "failed",
                "hotel_id": hotel_id,
                "message": f"Error processing reviews: {str(e)}"
            }
    
    def get_task_status(self, task_id: str) -> dict:
        return self.tasks.get(task_id, {"status": "not_found", "message": "Task not found"})


# Singleton instance
background_task_manager = BackgroundTaskManager()