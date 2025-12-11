from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import numpy as np

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "User Service"
    debug: bool = True

    # Google Cloud credentials
    google_application_credentials: str
    google_cloud_project: str
    vertex_ai_location: str
    gemini_model: str
    gcloud_json: str
    
    # Matching service
    matching_service_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()

JWT_SECRET_KEY="87vYXFU9IMtt6_ydwILLYLAf2bFcVuJMma5gW4k_CH0"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=180