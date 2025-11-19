from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "LLM Agent Service"
    debug: bool = True

    # Google Cloud credentials (using standard names)
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