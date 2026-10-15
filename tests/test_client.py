import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/linxsci-scholar/scripts'))
from scholar_client import ScholarClient, ScholarError, ROUTES
from scholar import main


class Handler(BaseHTTPRequestHandler):
    calls = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.handle_call()

    def do_POST(self):
        self.handle_call()

    def handle_call(self):
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        self.calls.append((self.command, self.path, dict(self.headers), body))
        if self.path.endswith('/usage'):
            self.send_response(429)
            self.send_header('Retry-After', '15')
            self.send_header('X-Request-ID', 'test-error')
            self.end_headers()
            self.wfile.write(b'{"error":{"code":"limited"}}')
        elif self.path.endswith('/health/live'):
            self.send_response(302)
            self.send_header('Location', '/openapi/v2/meta')
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"data":{"opaque":true},"meta":{}}')


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.client = ScholarClient('http://127.0.0.1:' + str(cls.server.server_port), 'test-key')

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def test_search_and_auth(self):
        result = self.client.search('图神经网络')
        method, path, headers, raw = Handler.calls[-1]
        self.assertEqual((method, path), ('POST', '/openapi/v2/papers/search'))
        self.assertEqual(headers['Authorization'], 'Bearer test-key')
        self.assertTrue(headers.get('X-Request-Id'))
        self.assertEqual(json.loads(raw), {'query': '图神经网络'})
        self.assertEqual(result.json()['data'], {'opaque': True})

    def test_doi_and_queries(self):
        self.client.paper('doi:10.1000/example', 'citations', query={'x': ['a', 'b']})
        self.assertEqual(Handler.calls[-1][1], '/openapi/v2/papers/doi:10.1000%2Fexample/citations?x=a&x=b')

    def test_upload(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / '论文.pdf'
            source.write_bytes(b'%PDF-test\x00')
            self.client.upload_pdf(source, fields={'mode': 'actual-contract-value'}, mineru_key='mineru-test')
        method, path, headers, body = Handler.calls[-1]
        self.assertEqual(path, '/openapi/v2/pdf/parse/upload')
        self.assertIn(b'name="file"', body)
        self.assertIn(b'%PDF-test\x00', body)
        self.assertIn(b'actual-contract-value', body)
        self.assertEqual(headers['X-Mineru-Api-Key'], 'mineru-test')
        self.assertTrue(headers['Content-Type'].startswith('multipart/form-data; boundary='))

    def test_error_preserved_without_retry(self):
        before = len(Handler.calls)
        with self.assertRaises(ScholarError) as caught:
            self.client.request('GET', '/usage')
        self.assertEqual(len(Handler.calls), before + 1)
        self.assertEqual(caught.exception.status, 429)
        self.assertEqual(caught.exception.body['error']['code'], 'limited')
        self.assertEqual(caught.exception.headers['Retry-After'], '15')

    def test_redirect_not_followed(self):
        before = len(Handler.calls)
        with self.assertRaises(ScholarError) as caught:
            self.client.request('GET', '/health/live')
        self.assertEqual(caught.exception.status, 302)
        self.assertEqual(len(Handler.calls), before + 1)

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            ScholarClient('https://example.com/openapi/v2', 'key')
        with self.assertRaises(ValueError):
            self.client.paper('2301.07041')
        with self.assertRaises(ValueError):
            self.client.pdf_task('upload')
        with self.assertRaises(ValueError):
            self.client.request('POST', '/meta', payload={})
        with self.assertRaises(ValueError):
            self.client.request('GET', '/meta', mineru_key='key')
        with self.assertRaises(ValueError):
            self.client.paper('arxiv:123', 'sections')

    def test_all_routes(self):
        values = {'paper_id': 'arxiv:123', 'task_id': 'task-1', 'section_id': 's1',
                  'asset_id': 'a1', 'author_id': 'u1', 'institution_id': 'i1', 'venue_id': 'v1'}
        self.assertEqual(len(ROUTES), 34)
        for method, template in ROUTES:
            path = template.format(**values)
            if path in ('/usage', '/health/live', '/pdf/parse/upload'):
                continue
            with self.subTest(path=path):
                self.assertEqual(self.client.request(method, path, payload={'opaque': 1} if method == 'POST' else None).status, 200)


if __name__ == '__main__':
    unittest.main()
