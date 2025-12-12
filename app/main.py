from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
        await FirestoreConnection.initialize()
        logger.info("All connections initialized")
    except Exception as e:
        logger.error(f"Startup failed: {str(e)}", exc_info=True)
        # Don't raise exception - allow app to start even if Firestore fails
        logger.warning("Continuing startup despite Firestore connection failure")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down...")
    try:
        await FirestoreConnection.close()
        logger.info("All connections closed")
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}", exc_info=True)

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="User and Rooms service",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for testing
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"service": "User and rooms Service", "version": "1.0.0"}

from app.api import users
app.include_router(users.router)

from app.api import rooms
app.include_router(rooms.router)

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

