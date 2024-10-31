import pytest
from tests.test_base import BaseTestCase
from app import create_app
from app.config.prompts_compression import COMPRESS_SINGLE, COMPRESS_FIXED, COMPRESS_STAGGERED
import time


@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers():
    return {'Authorization': 'Bearer test_key'}


@pytest.mark.unit
class TestCompressEndpoint(BaseTestCase):
    # Test data
    SAMPLE_TEXT = "The Text Transformation API offers a robust set of REST endpoints that enable developers to programmatically manipulate and transform text content. The operations include expansion, summarization, and chunking."

    @pytest.fixture(autouse=True)
    def setup(self):
        # Add delay between tests to avoid rate limits
        time.sleep(0.5)

    @pytest.mark.unit
    def test_single_version_compression(self, client, auth_headers):
        response = client.post(self.ENDPOINTS['compress'], json={
            'content': self.SAMPLE_TEXT,
            'target_percentage': 40
        }, headers=auth_headers)

        assert response.status_code == 200
        data = response.json

        # Test response structure
        assert data['type'] == 'cohesive'
        assert len(data['versions']) == 1

        version = data['versions'][0]
        assert 'text' in version
        assert 'final_percentage' in version
        assert isinstance(version['final_percentage'], float)

        # Test compression quality
        compressed_text = version['text']
        target_percentage = 40
        assert abs(version['final_percentage'] -
                   target_percentage) <= 10  # 10% margin

        # Test readability and meaning preservation
        assert 'API' in compressed_text
        assert 'endpoints' in compressed_text
        assert compressed_text.endswith('.')

    @pytest.mark.unit
    def test_fixed_multiple_versions(self, client, auth_headers):
        response = client.post(self.ENDPOINTS['compress'], json={
            'content': self.SAMPLE_TEXT,
            'target_percentage': 50,
            'versions': 3
        }, headers=auth_headers)

        assert response.status_code == 200
        data = response.json
        assert len(data['versions']) == 3
        # All versions same length
        assert len(set(len(v['text']) for v in data['versions'])) == 1
        assert data['metadata']['mode'] == 'fixed'

    @pytest.mark.unit
    def test_staggered_with_steps(self, client, auth_headers):
        response = client.post(self.ENDPOINTS['compress'], json={
            'content': self.SAMPLE_TEXT,
            'target_percentage': 40,
            'steps_percentage': 10
        }, headers=auth_headers)

        data = response.json
        versions = data['versions']
        # Check decreasing length
        lengths = [len(v['text']) for v in versions]
        assert lengths == sorted(lengths, reverse=True)
        assert data['metadata']['mode'] == 'staggered'

    @pytest.mark.unit
    def test_staggered_custom_range(self, client, auth_headers):
        response = client.post(self.ENDPOINTS['compress'], json={
            'content': self.SAMPLE_TEXT,
            'start_percentage': 60,
            'target_percentage': 40,
            'versions': 5
        }, headers=auth_headers)

        data = response.json
        percentages = data['metadata']['target_percentages']
        assert percentages == [60, 55, 50, 45, 40]

    @pytest.mark.unit
    def test_array_input(self, client, auth_headers):
        response = client.post(self.ENDPOINTS['compress'], json={
            'content': [
                "The Text Transformation API offers REST endpoints",
                "These endpoints enable text manipulation",
                "Operations include various transformations"
            ],
            'target_percentage': 50,
            'versions': 2
        }, headers=auth_headers)

        data = response.json
        assert data['type'] == 'fragments'
        assert len(data['fragments']) == 3

        for fragment in data['fragments']:
            assert len(fragment['versions']) == 2
            for version in fragment['versions']:
                assert 'text' in version
                assert 'final_percentage' in version
                assert isinstance(version['final_percentage'], float)
                # Check if compression is roughly within target
                assert abs(version['final_percentage'] - 50) <= 10

    @pytest.mark.unit
    @pytest.mark.parametrize('invalid_input', [
        {'content': "text", 'target_percentage': 150},  # Invalid percentage
        {'content': "text", 'steps_percentage': -10},   # Negative steps
        {'content': "text", 'versions': 10},            # Too many versions
        {'content': "", 'target_percentage': 50},       # Empty content
        {'target_percentage': 50},                      # Missing content
    ])
    def test_invalid_inputs(self, client, auth_headers, invalid_input):
        response = client.post(
            self.ENDPOINTS['compress'], json=invalid_input, headers=auth_headers)
        assert response.status_code == 400
        assert 'error' in response.json

    @pytest.mark.unit
    def test_length_validation(self, client, auth_headers):
        """Test if compressed versions roughly match target percentages"""
        response = client.post(self.ENDPOINTS['compress'], json={
            'content': self.SAMPLE_TEXT,
            'target_percentage': 50,
            'versions': 1
        }, headers=auth_headers)

        data = response.json
        original_length = len(self.SAMPLE_TEXT)
        compressed_length = len(data['versions'][0]['text'])
        # Allow 10% margin of error
        assert abs(compressed_length/original_length - 0.5) <= 0.1
