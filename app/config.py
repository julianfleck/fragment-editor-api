import os
from datetime import timedelta


class Config:
    """Base config."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    API_TITLE = 'Text Transform API'
    API_VERSION = 'v1'

    # Rate limiting
    RATELIMIT_DEFAULT = "100/minute"
    RATELIMIT_STORAGE_URL = "memory://"

    # API Keys (replace with proper key management)
    VALID_API_KEYS = {
        'test-key': 'standard',  # tier level
        'premium-key': 'premium'
    }

    # Default to test_key for testing
    API_KEY = os.getenv('API_KEY', 'test_key')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    DEBUG = True
    TESTING = True


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}
