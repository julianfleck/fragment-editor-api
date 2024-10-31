class BaseTestCase:
    ENDPOINTS = {
        'compress': '/text/v1/compress/',
        'expand': '/text/v1/expand/',
        'generate': '/text/v1/generate/text'
    }

    SAMPLE_TEXT = "The Text Transformation API offers a robust set of REST endpoints that enable developers to programmatically manipulate and transform text content. The operations include expansion, summarization, and chunking."
