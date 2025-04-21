from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Language Detection Service"
    
    # WebSocket Settings
    WS_PING_INTERVAL: int = 20
    WS_PING_TIMEOUT: int = 20
    
    # Translation Settings
    SUPPORTED_LANGUAGES: List[str] = ["en", "es", "fr"]
    DEFAULT_SOURCE_LANG: str = "en"
    DEFAULT_TARGET_LANG: str = "es"
    
    # RabbitMQ Settings
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/?heartbeat=30"
    TRANSLATION_QUEUE: str = "translation_queue"
    DETECTION_QUEUE: str = "detection_queue"
    STATUS_QUEUE: str = "status_queue"
    # RESPONSE_QUEUE: str = "response_queue"
    
    # HuggingFace Settings
    # HUGGINGFACE_MODEL_URL: str = "https://api-inference.huggingface.co/models/Helsinki-NLP/opus-mt-{src}-{tgt}"
    HUGGINGFACE_MODEL_URL: str = "https://api-inference.huggingface.co/models/facebook/nllb-200-1.3B"
    # HUGGINGFACE_TOKEN : str = "hf_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"  # Replace with your actual token
    # HUGGINGFACE_MODEL_URL: str = "https://api-inference.huggingface.co/models/acebook/nllb-200-1.3B"

    # Languages Currently Supported
    # AVAILABLE_LANGUAGES = {"en-fr", "en-de", "en-ar", "ar-en", "de-en", "fr-en"}

    # Redis Settings
    # REDIS_HOST: str = "localhost"
    # REDIS_PORT: int = 6379
    # # REDIS_PASSWORD: str = "your_redis_password"  # Uncomment if using password authentication
    # REDIS_URL: str = "redis://localhost:6379/"  # Example URL format
    # REDIS_DB: int = 0
    # Redis Cache Settings
    # REDIS_CACHE_TIMEOUT: int = 60
    
    
    # class Config:
    #     case_sensitive = True
    #     env_file = ".env"

settings = Settings()
