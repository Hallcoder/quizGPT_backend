from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import quiz, upload
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    description="AI-powered quiz generation API",
    version="1.0.0"
)

logger.info(f"Starting {settings.APP_NAME}")
logger.info(f"Debug mode: {settings.DEBUG}")
logger.info(f"Allowed origins: {settings.ALLOWED_ORIGINS}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to QuizGPT API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    from app.core.database import engine

    # Check database connection
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_status = "connected"
        logger.info("Database health check: OK")
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"Database health check failed: {str(e)}")

    return {
        "status": "healthy",
        "database": db_status
    }
