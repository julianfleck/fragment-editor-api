import pytest
from tests.test_base import BaseTestCase


@pytest.mark.integration
class TestCompressIntegration(BaseTestCase):
    def test_complete_workflow(self, client, auth_headers):
        # Test a complex workflow with multiple steps
        original_text = "The Text Transformation API..."

        # 1. Compress to 50%
        compress_response = client.post(self.ENDPOINTS['compress'], json={
            'content': original_text,
            'target_percentage': 50
        }, headers=auth_headers)

        compressed = compress_response.json['versions'][0]['text']

        # 2. Split into fragments
        fragment_response = client.post('/fragment', json={
            'content': compressed
        }, headers=auth_headers)

        # 3. Expand each fragment
        for fragment in fragment_response.json['fragments']:
            expand_response = client.post('/expand', json={
                'content': fragment['text'],
                'target_percentage': 200
            }, headers=auth_headers)

            assert expand_response.status_code == 200

    @pytest.mark.parametrize('language', ['en', 'es', 'fr'])
    def test_multilingual_compression(self, client, auth_headers, language):
        # Test compression works with different languages
        texts = {
            'en': "The quick brown fox jumps over the lazy dog",
            'es': "El rápido zorro marrón salta sobre el perro perezoso",
            'fr': "Le rapide renard brun saute par-dessus le chien paresseux"
        }

        response = client.post(self.ENDPOINTS['compress'], json={
            'content': texts[language],
            'target_percentage': 50
        }, headers=auth_headers)

        assert response.status_code == 200
        # Verify output is in same language as input
        # (You might want to use a language detection library here)
