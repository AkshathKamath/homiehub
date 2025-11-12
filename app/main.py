from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import sys

from app.db.firestore import FirestoreConnection
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Application starting...")
    try:
        FirestoreConnection.initialize()
        logger.info("All connections initialized")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}", exc_info=True)
        raise
    
    yield
    
    # Shutdown
    logger.info("Application shutting down...")
    try:
        FirestoreConnection.close()
        logger.info("All connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}", exc_info=True)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="User and Rooms service",
    lifespan=lifespan
)

@app.get("/")
def root():
    return {"service": "User and rooms Service", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    firestore_healthy = FirestoreConnection.health_check()
    if not firestore_healthy:
        return {"status": "unhealthy", "firestore": "down"}, 503
    return {"status": "healthy", "firestore": "up"}

from app.api import users
app.include_router(users.router)

from app.api import rooms
app.include_router(rooms.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=4000, reload=True)

