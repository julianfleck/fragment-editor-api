import os

class Config:
    API_TITLE = "Text Transform API"
    API_VERSION = "1.0.0"
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    DEBUG = True

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 