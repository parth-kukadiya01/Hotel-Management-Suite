from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import init_db
from app.routers import auth, reviews, dashboard
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")
    yield
    # Shutdown: cleanup if needed
    print("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Real-Time Guest Reputation & Escalation Engine - ML-powered hotel review analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(reviews.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "api": "running"
    }