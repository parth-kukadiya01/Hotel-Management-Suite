from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, Review, UrgencyType
from app.schemas import (
    IngestReviewsRequest,
    IngestReviewsResponse,
    CriticalReviewResponse
)
from app.dependencies import get_manager_user, get_authenticated_user
from app.services.background_tasks import background_task_manager

router = APIRouter(tags=["Reviews"])


@router.post("/ingest-reviews", response_model=IngestReviewsResponse)
async def ingest_reviews(
    request: IngestReviewsRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_manager_user),
    db: Session = Depends(get_db)
):
    task_id = background_task_manager.create_task_id()
    
    background_tasks.add_task(
        background_task_manager.ingest_reviews_task,
        task_id=task_id,
        hotel_id=request.hotel_id,
        limit=request.limit,
        user_id=current_user.id
    )
    
    return IngestReviewsResponse(
        status="processing",
        message=f"Review ingestion started for hotel {request.hotel_id}",
        task_id=task_id,
        hotel_id=request.hotel_id
    )


@router.get("/critical-reviews", response_model=List[CriticalReviewResponse])
def get_critical_reviews(
    current_user: User = Depends(get_authenticated_user),
    db: Session = Depends(get_db)
):
    critical_reviews = db.query(Review).filter(
        Review.urgency == UrgencyType.CRITICAL
    ).order_by(Review.processed_at.desc()).all()
    
    return critical_reviews


@router.get("/task-status/{task_id}")
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_authenticated_user)
):
    return background_task_manager.get_task_status(task_id)