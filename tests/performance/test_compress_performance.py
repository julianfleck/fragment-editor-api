import time
import pytest
import concurrent.futures
from tests.test_compress import TestCompressEndpoint


@pytest.mark.performance
class TestCompressPerformance(TestCompressEndpoint):
    def test_response_time(self, client, auth_headers):
        start_time = time.time()
        response = client.post(self.ENDPOINTS['compress'], json={
            'content': "A" * 1000,  # 1000 character text
            'target_percentage': 50
        }, headers=auth_headers)
        duration = time.time() - start_time

        assert duration < 2.0  # Should respond within 2 seconds
        assert response.status_code == 200

        # Verify final percentage
        version = response.json['versions'][0]
        assert 'final_percentage' in version
        assert abs(version['final_percentage'] - 50) <= 10

    def test_concurrent_requests(self, client, auth_headers):
        def make_request():
            return client.post(self.ENDPOINTS['compress'], json={
                'content': "Test content",
                'target_percentage': 50
            }, headers=auth_headers)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in futures]

        assert all(r.status_code == 200 for r in responses)
        # Verify final percentages for all responses
        for response in responses:
            version = response.json['versions'][0]
            assert 'final_percentage' in version
            assert abs(version['final_percentage'] - 50) <= 10
