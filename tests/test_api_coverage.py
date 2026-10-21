"""Call every documented route through the self-contained Skill executable."""
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

from cli_cases import shortcut_cases

ROOT = Path(__file__).resolve().parents[1]


class CoverageAPI(BaseHTTPRequestHandler):
    calls = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.respond()

    def do_POST(self):
        self.respond()

    def respond(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        body = (b"\x00\xffasset\r\n" if "/assets/" in self.path else
                json.dumps({"opaque": {"method": self.command, "path": self.path}},
                           ensure_ascii=False).encode())
        self.calls.append((self.command, self.path, dict(self.headers), raw, body))
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream" if "/assets/" in self.path else "application/json")
        self.end_headers()
        self.wfile.write(body)


class SkillAPICoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), CoverageAPI)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def test_all_documented_routes_through_skill_script(self):
        self.check_routes(convenient=False)

    def test_all_documented_routes_through_shortcuts(self):
        self.check_routes(convenient=True)

    def check_routes(self, convenient):
        document = (ROOT / "Scholar-OpenAPI-v2-使用文档.md").read_text(encoding="utf-8")
        routes = re.findall(r"\| (GET|POST) \| `/openapi/v2([^`]+)` \|", document)
        self.assertEqual(len(routes), 34)
        identifiers = {"paper_id": "doi:10.1000/论文 A?#%", "task_id": "task/1",
                       "section_id": "section/方法 1", "asset_id": "figure/1",
                       "author_id": "author/1", "institution_id": "institution/1", "venue_id": "venue/1"}
        encoded = {key: quote(value, safe=":") for key, value in identifiers.items()}
        # Synthetic payload/fields check transport only; they are not API schemas.
        payload = {"opaque": {"text": "中文", "values": [1, False, None]}}
        with tempfile.TemporaryDirectory(prefix="linxsci-coverage-") as temporary:
            directory = Path(temporary)
            source = directory / "论文.pdf"
            source.write_bytes(b"%PDF-test\x00\xff")
            body_file = directory / "request.json"
            body_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            environment = dict(os.environ)
            environment.update(SCHOLAR_BASE_URL="http://127.0.0.1:" + str(self.server.server_port),
                               SCHOLAR_OPENAPI_KEY="coverage-test-key",
                               SCHOLAR_CONFIG_FILE=str(directory / "unused.json"),
                               SCHOLAR_MINERU_API_KEY="coverage-mineru-key",
                               NO_PROXY="127.0.0.1,localhost")
            cases = shortcut_cases(identifiers, body_file, source)
            self.assertEqual(set(cases), set(routes))
            for index, (method, template) in enumerate(routes):
                path = template.format(**encoded)
                is_upload = path == "/pdf/parse/upload"
                with self.subTest(method=method, path=template):
                    output_file = directory / (str(index) + ".response")
                    command = [sys.executable, str(ROOT / "skills/linxsci-skills/scripts/cli.py"),
                               "--framework-request-id", "coverage-framework",
                               "--output", str(output_file)]
                    if convenient:
                        command += cases[(method, template)] + ["--request-id", "coverage-upstream",
                                    "--param", "opaque=中文 空格", "--param", "opaque=a/b"]
                        if is_upload:
                            command += ["--field", "opaque=中文"]
                    elif is_upload:
                        command += ["upload", str(source), "--field", "opaque=中文"]
                    else:
                        command += ["request", method, path, "--request-id", "coverage-upstream",
                                    "--param", "opaque=中文 空格", "--param", "opaque=a/b"]
                        if method == "POST":
                            command += ["--body", "@" + str(body_file)]
                    before = len(CoverageAPI.calls)
                    result = subprocess.run(command, cwd=directory, env=environment, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertNotIn("coverage-test-key", result.stdout + result.stderr)
                    self.assertNotIn("coverage-mineru-key", result.stdout + result.stderr)
                    self.assertEqual(len(CoverageAPI.calls), before + 1)
                    received_method, url, headers, raw, response = CoverageAPI.calls[-1]
                    self.assertEqual(received_method, method)
                    self.assertEqual(urlsplit(url).path, "/openapi/v2" + path)
                    self.assertEqual(output_file.read_bytes(), response)
                    headers = {key.lower(): value for key, value in headers.items()}
                    self.assertEqual(headers["authorization"], "Bearer coverage-test-key")
                    self.assertEqual(headers["x-anythingright-req-id"], "coverage-framework")
                    self.assertNotIn("x-api-key", headers)
                    self.assertEqual(headers.get("x-mineru-api-key"),
                                     "coverage-mineru-key" if path.startswith("/pdf/parse") else None)
                    if convenient:
                        self.assertEqual(headers["x-request-id"], "coverage-upstream")
                        self.assertEqual(parse_qs(urlsplit(url).query), {"opaque": ["中文 空格", "a/b"]})
                    if is_upload:
                        self.assertTrue(headers["content-type"].startswith("multipart/form-data; boundary="))
                        self.assertIn(b'name="file"', raw)
                        self.assertIn(source.read_bytes(), raw)
                        self.assertIn('name="opaque"\r\n\r\n中文'.encode(), raw)
                    else:
                        self.assertEqual(headers["x-request-id"], "coverage-upstream")
                        self.assertEqual(parse_qs(urlsplit(url).query), {"opaque": ["中文 空格", "a/b"]})
                        if method == "POST":
                            self.assertEqual(headers["content-type"], "application/json")
                            self.assertEqual(json.loads(raw), {**payload, "query": "release coverage"}
                                             if convenient and path in ("/papers/search", "/search/openalex",
                                                                        "/search/semantic-scholar", "/search/google-scholar") else payload)
                        else:
                            self.assertEqual(raw, b"")


if __name__ == "__main__":
    unittest.main()
