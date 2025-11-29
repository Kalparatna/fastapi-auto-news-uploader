from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # MongoDB Configuration
    MONGO_STRING: str
    MONGODB_DATABASE: str = "cricket_news_bot"
    
    # Telegram Bot Configuration
    BOT_TOKEN: str
    CHAT_ID: str
    
    # ESPN RSS Configuration
    ESPN_RSS_URL: str = "https://www.espncricinfo.com/rss/content/story/feeds/0.xml"
    
    # Scheduler Configuration
    ENABLE_SCHEDULER: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env file

@lru_cache()
def get_settings():
    return Settings()
