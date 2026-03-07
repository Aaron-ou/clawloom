"""
Local test configuration using SQLite
"""

from config import Settings

class LocalSettings(Settings):
    """Local development settings with SQLite"""
    DATABASE_URL: str = "sqlite:///./clawloom_test.db"
