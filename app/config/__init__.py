import os


class Config:
    # Name of the API shown in documentation/OpenAPI spec
    API_TITLE = "Text Transform API"
    # Current version of the API
    API_VERSION = "1.0.0"

    # Master key used for cryptographic operations (sessions, tokens, etc.)
    # Should be changed in production using environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change')

    # Set of valid API keys that clients can use to authenticate requests
    # Defaults to a single test key in base config
    API_KEYS = set([os.environ.get('DEV_API_KEY', 'test-key')])

    # Global debug flag - affects logging, error messages, etc.
    DEBUG = False


class DevelopmentConfig(Config):
    # Development environment: Enable debug mode for detailed error messages
    # and hot reloading
    DEBUG = True


class ProductionConfig(Config):
    # Production environment: Disable debug for security
    DEBUG = False

    # Override API_KEYS to load from environment variable
    # Format: VALID_API_KEYS="key1,key2,key3"
    # Strips whitespace and ignores empty keys
    API_KEYS = set(
        key.strip()
        for key in os.environ.get('VALID_API_KEYS', '').split(',')
        if key.strip()
    )


class TestingConfig(Config):
    # Testing environment: Used during automated tests
    TESTING = True
    DEBUG = True


# Dictionary to easily select config based on environment name
# 'default' is used if no environment is specified
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
