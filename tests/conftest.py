import os
import sys
import pytest
from dotenv import load_dotenv
from app import create_app

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()
    assert os.getenv('GROQ_API_KEY'), "GROQ_API_KEY must be set in .env file"


@pytest.fixture
def app():
    app = create_app('testing')
    return app


@pytest.fixture
def client(app):
    app.config['TESTING'] = True
    app.config['API_KEY'] = 'test_key'
    return app.test_client()


@pytest.fixture
def auth_headers():
    return {
        'Authorization': 'Bearer test_key',
        'Content-Type': 'application/json'
    }


class BaseTestCase:
    ENDPOINTS = {
        'compress': '/text/v1/compress/',
        'expand': '/text/v1/expand/',
        'fragment': '/text/v1/fragment/'
    }
