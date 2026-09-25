import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    FLASK_ENV = os.getenv("FLASK_ENV", "development")

    @classmethod
    def validate(cls):
        return []