import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Config:
    SITE_NAME = "Harsh Website"
    DATA_DIR = BASE_DIR / "data"

    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "harsh_website")
    SECRET_KEY = os.getenv("SECRET_KEY")

    @classmethod
    def validate(cls):
        """Fail at boot rather than on the first query."""
        if not cls.MONGO_URI:
            raise RuntimeError("MONGO_URI is not set. Add it to .env")
        if not cls.SECRET_KEY:
            raise RuntimeError("SECRET_KEY is not set. Add it to .env")
