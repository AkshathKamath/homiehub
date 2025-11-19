from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "Recommendation Service"
    debug: bool = True

    google_application_credentials: str
    google_cloud_project: str
    vertex_ai_location: str
    gemini_model: str
    matching_service_url: str
    gcloud_json: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
