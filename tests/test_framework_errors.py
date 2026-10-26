"""Contract regression tests for the revised LinxSci framework/billing errors."""
import contextlib
import io
import json
import os
import re
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch
from env_helpers import isolated_environment

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/linxsci-skills/scripts"))
from commands import error_info, main
from client import ROUTES, LinxSciClient, LinxSciError

STATUS = {-401: 401, -404: 404, -3900: 503, -3901: 429,
          -3902: 503, -3903: 502, -3904: 502, -3905: 502}


class FrameworkAPI(BaseHTTPRequestHandler):
    calls = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        self.respond()

    def do_POST(self):
        self.respond()

    def respond(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        payload = json.loads(raw) if raw else {}
        self.calls.append((self.command, self.path, dict(self.headers), payload))
        value = payload.get("query", "")
        code = int(value) if value in {str(c) for c in STATUS} else None
        if code is not None:
            self.send_response(STATUS[code])
            body = {"code": -1, "data": {}, "error": {"code": code, "msg": "never-print-secret"},
                    "extra": {"request-id": self.headers.get("X-ANYTHINGRIGHT-REQ-ID", "framework-generated"), "cost": 0.01}}
        else:
            self.send_response(200)
            body = {"data": {"unchanged": True}, "meta": {}}
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Request-ID", self.headers.get("X-Request-ID", "proxy-generated"))
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())


class FrameworkContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), FrameworkAPI)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = "http://127.0.0.1:" + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def test_routes_match_updated_document(self):
        document = (ROOT / "docs/API.md").read_text(encoding="utf-8")
        documented = re.findall(r"\| (GET|POST) \| `/openapi/v2([^`]+)` \|", document)
        self.assertEqual(len(documented), 34)
        self.assertEqual(set(ROUTES), set(documented))
        self.assertEqual(document.replace("(API.zh-CN.md)", "(api.zh-CN.md)").replace("(CLI_GUIDE.md#", "(cli.md#"),
                         (ROOT / "skills/linxsci-skills/references/api.md").read_text(encoding="utf-8"))

    def test_numeric_errors_and_two_distinct_ids(self):
        client = LinxSciClient(self.base_url, "test-key", framework_request_id="framework-client")
        for code, status in STATUS.items():
            with self.subTest(code=code):
                before = len(FrameworkAPI.calls)
                with self.assertRaises(LinxSciError) as caught:
                    client.request("POST", "/papers/search", payload={"query": str(code)}, request_id="agent-client")
                error = caught.exception
                self.assertEqual(len(FrameworkAPI.calls), before + 1)
                self.assertEqual(error.status, status)
                self.assertEqual(error.error_code, code)
                self.assertEqual(error.request_id, "agent-client")
                self.assertEqual(error.framework_request_id, "framework-client")
                self.assertEqual(error.body["extra"]["cost"], 0.01)
                self.assertEqual(error.execution_uncertain, code == -3905)
                report = error_info(error)
                self.assertEqual(report["error_code"], code)
                self.assertNotIn("never-print-secret", json.dumps(report))
                self.assertNotEqual(report["message"], "服务调用失败，请检查服务地址、网络和服务状态。")

    def test_cli_does_not_retry_finish_uncertainty(self):
        with tempfile.TemporaryDirectory() as temporary:
            environment = {"LINXSCI_BASE_URL": self.base_url, "LINXSCI_OPENAPI_KEY": "never-print-secret",
                           "LINXSCI_CONFIG_FILE": str(Path(temporary) / "unused.json")}
            output, errors = io.StringIO(), io.StringIO()
            before = len(FrameworkAPI.calls)
            with patch.dict(os.environ, isolated_environment(environment), clear=True), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                status = main(["--json-errors", "--framework-request-id", "framework-cli", "search", "-3905"])
            self.assertEqual(status, 1)
            self.assertEqual(output.getvalue(), "")
            report = json.loads(errors.getvalue())
            self.assertTrue(report["execution_uncertain"])
            self.assertEqual(report["framework_request_id"], "framework-cli")
            self.assertIn("先查询执行与计费结果", report["message"])
            self.assertEqual(len(FrameworkAPI.calls), before + 1)
            self.assertNotIn("never-print-secret", errors.getvalue())

    def test_doctor_reports_action_not_enabled(self):
        error = LinxSciError("HTTP 503", 503,
                             {"code": -1, "data": {}, "error": {"code": -3900, "msg": "never-print-secret"},
                              "extra": {"request-id": "framework-only", "cost": 0.01}})
        from commands import doctor
        output = io.StringIO()
        with patch.object(LinxSciClient, "request", side_effect=error), contextlib.redirect_stdout(output):
            status = doctor(LinxSciClient(self.base_url, "test-key"), as_json=True)
        report = json.loads(output.getvalue())
        self.assertEqual(status, 1)
        self.assertFalse(report["ok"])
        self.assertEqual(report["error_code"], -3900)
        self.assertNotIn("request_id", report)
        self.assertEqual(report["framework_request_id"], "framework-only")
        self.assertIn("未启用", report["message"])
        self.assertNotIn("never-print-secret", output.getvalue())

    def test_headers_and_per_request_override(self):
        client = LinxSciClient(self.base_url, "test-key", framework_request_id="default-framework")
        response = client.request("GET", "/meta", request_id="upstream-id", framework_request_id="override-framework")
        headers = {k.lower(): v for k, v in FrameworkAPI.calls[-1][2].items()}
        self.assertEqual(headers["authorization"], "Bearer test-key")
        self.assertEqual(headers["x-request-id"], "upstream-id")
        self.assertEqual(headers["x-anythingright-req-id"], "override-framework")
        self.assertNotIn("x-api-key", headers)
        self.assertEqual(response.json(), {"data": {"unchanged": True}, "meta": {}})
        client.search("topic")
        headers = {k.lower(): v for k, v in FrameworkAPI.calls[-1][2].items()}
        self.assertEqual(headers["x-anythingright-req-id"], "default-framework")

    def test_header_validation_before_network(self):
        client = LinxSciClient(self.base_url, "test-key")
        before = len(FrameworkAPI.calls)
        with self.assertRaises(ValueError):
            client.request("GET", "/meta", framework_request_id="bad\r\nInjected: value")
        with self.assertRaises(ValueError):
            client.request("GET", "/meta", request_id="bad\nvalue")
        self.assertEqual(len(FrameworkAPI.calls), before)

    def test_upstream_and_older_errors_still_supported(self):
        for code in ("validation_error", "asset_unavailable", "upstream_unconfigured"):
            with self.subTest(code=code):
                body = {"error": {"code": code, "message": "private-detail", "request_id": "upstream-body-id"}}
                error = LinxSciError("HTTP error", 422, body)
                self.assertEqual(error.error_code, code)
                self.assertEqual(error.request_id, "upstream-body-id")
                self.assertIsNone(error.framework_request_id)
                self.assertFalse(error.execution_uncertain)
                self.assertNotIn("private-detail", json.dumps(error_info(error)))
                self.assertEqual(error.body, body)


if __name__ == "__main__":
    unittest.main()
