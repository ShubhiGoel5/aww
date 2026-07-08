import pytest
from unittest.mock import MagicMock
from src.services.crawler import LegalCrawler
import requests

class MockResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP Error {self.status_code}")

@pytest.fixture
def mock_requests_get(mocker):
    return mocker.patch('requests.Session.get')

def test_crawler_crawl_url_success(mock_requests_get):
    mock_requests_get.return_value = MockResponse(
        text='<html><head><title>Important Act</title></head><body>This is a legal document</body></html>'
    )
    
    crawler = LegalCrawler()
    
    res = crawler.crawl_url('https://indiankanoon.org/doc/1234/')
    assert res['success'] is True
    assert res['content'] == 'This is a legal document'
    assert res['title'] == 'Important Act'
    mock_requests_get.assert_called_once_with('https://indiankanoon.org/doc/1234/', timeout=15)

def test_discover_links_filters_non_legal_and_ssrf(mock_requests_get):
    html = '''
        <html>
            <body>
                <a href="/doc/1234/">Doc 1</a>
                <a href="https://google.com/about">Google</a>
                <a href="https://legislative.gov.in/act-of-parliament">Acts</a>
                <a href="http://127.0.0.1/admin/law">Local</a>
                <a href="http://localhost:8080/act">Local 2</a>
                <a href="http://192.168.1.5/ordinance">Local 3</a>
                <a href="file:///etc/passwd/law">File</a>
            </body>
        </html>
    '''
    mock_requests_get.return_value = MockResponse(text=html)
    
    crawler = LegalCrawler()
    
    res = crawler.discover_links('https://indiankanoon.org')
    
    # Should only keep the URLs that match legal patterns and are safe
    assert len(res) == 2
    assert 'https://indiankanoon.org/doc/1234/' in res
    assert 'https://legislative.gov.in/act-of-parliament' in res

def test_batch_crawl_mixed_results(mock_requests_get):
    # Mocking successful and failed responses based on URL
    def side_effect(url, **kwargs):
        if url == 'https://indiankanoon.org/doc/1/':
            return MockResponse(text='<html><title>Doc 1</title><body>Good content</body></html>')
        else:
            return MockResponse(text='', status_code=404)
            
    mock_requests_get.side_effect = side_effect
    
    crawler = LegalCrawler()
    
    res = crawler.batch_crawl(['https://indiankanoon.org/doc/1/', 'https://indiankanoon.org/doc/2/'])
    assert res['success'] is True
    assert res['total'] == 2
    assert res['indexed'] == 1
    assert res['errors'] == 1

def test_chunking_oversized_content():
    crawler = LegalCrawler()
    # Create 1500 character content (limit is 1000)
    content = 'A' * 600 + '\n\n' + 'B' * 600
    chunks = crawler._chunk_content(content, max_chunk_size=1000)
    assert len(chunks) == 2
    assert chunks[0] == 'A' * 600
    assert chunks[1] == 'B' * 600
