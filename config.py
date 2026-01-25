import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Settings
    api_v1_prefix: str = "/api/v1"
    
    # Google Sheets Robot Account File
    GOOGLE_SERVICE_ACCOUNT_JSON: dict
    
    # Google Sheet ID
    GOOGLE_SHEETS_ID: str

    # MailJet Email Service Keys
    MAILJET_API_KEY: str
    MAILJET_SECRET_KEY: str
    
    # Environment
    ENV: str = "testing"
    
    class Config:
        env_file = ".env"

settings = Settings()