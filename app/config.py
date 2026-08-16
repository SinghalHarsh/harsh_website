import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Config:
    SITE_NAME = "Harsh Website"
    DATA_DIR = BASE_DIR / "data"

    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "harsh_website")

    # A random key beats the old hardcoded default: sessions simply do not
    # survive a restart when the env var is missing, rather than every
    # deployment sharing a publicly known key.
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)

    @classmethod
    def validate(cls):
        """Fail at boot rather than on the first query."""
        if not cls.MONGO_URI:
            raise RuntimeError("MONGO_URI is not set. Add it to the environment.")
