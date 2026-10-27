"""Observable CLI output contracts, including safe handling after successful requests."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from env_helpers import isolated_environment

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/linxsci-skills/scripts"))
import cli
from client import LinxSciClient, LinxSciError, Response


class OutputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.environment = patch.dict(os.environ, isolated_environment({"LINXSCI_CONFIG_FILE": str(self.root / "config.json"),
                 "LINXSCI_BASE_URL": "http://localhost:9000", "LINXSCI_OPENAPI_KEY": "private-key"}), clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def invoke(self, args, value=None, response=None, error=None):
        if response is None:
            response = Response(200, {"Content-Type": "application/json"},
                                json.dumps(value, ensure_ascii=False).encode())
        out, err = io.StringIO(), io.StringIO()
        with patch.object(LinxSciClient, "request", return_value=response, side_effect=error) as request, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = cli.main(args)
            except SystemExit as error:
                code = error.code
        self.assertNotIn("private-key", out.getvalue() + err.getvalue())
        return code, out.getvalue(), err.getvalue(), request

    def remove_report_file(self, report):
        path = Path(report["file"])
        self.addCleanup(shutil.rmtree, path.parent)
        return path

    def test_compact_default_and_pretty_preserve_actual_data(self):
        data = {"title": "中文论文", "optional": None, "flag": False, "items": []}
        code, out, err, _ = self.invoke(["search", "topic"], data)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out.count("\n"), 1)
        self.assertIn("中文论文", out)
        self.assertEqual(json.loads(out), data)
        code, pretty, _, _ = self.invoke(["--pretty", "search", "topic"], data)
        self.assertGreater(pretty.count("\n"), 1)
        self.assertEqual(json.loads(pretty), data)

    def test_explicit_selection_limit_and_table_do_not_change_request(self):
        data = {"payload": {"a/b": {"~key": [
            {"id": "p1", "title": "One", "content": "long", "optional": None},
            {"id": "p2", "title": "Two", "content": "long", "optional": None}]}}}
        args = ["--select", "/payload/a~1b/~0key", "--fields", "id,title,optional",
                "--limit", "1", "--table", "search", "topic"]
        code, out, err, request = self.invoke(args, data)
        self.assertEqual((code, err), (0, ""))
        result = json.loads(out)
        self.assertEqual(result, {"data": {"columns": ["id", "title", "optional"],
                  "rows": [["p1", "One", None]]}, "total": 2, "returned": 1, "truncated": True})
        self.assertEqual(request.call_args.kwargs["payload"], {"query": "topic"})
        self.assertEqual(request.call_count, 1)

    def test_pointer_array_index_empty_key_and_escape_order(self):
        for pointer, value in [("/a/0", "zero"), ("/", "empty"), ("/~01", "tilde-one"), ("", {"a": ["zero"], "": "empty", "~1": "tilde-one"})]:
            code, out, _, _ = self.invoke(["--select", pointer, "meta"], {"a": ["zero"], "": "empty", "~1": "tilde-one"})
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out), value)

    def test_bad_view_preserves_completed_task_and_does_not_retry(self):
        raw = b'{"task_id":"created-task"}'
        for options in (["--select", "/missing"], ["--select", "/~2"], ["--limit", "1"],
                        ["--fields", "missing"], ["--table"]):
            with self.subTest(options=options):
                code, out, err, request = self.invoke(options + ["parse-pdf", "--body", '{}'], response=Response(200, {}, raw))
                self.assertEqual((code, out), (2, ""))
                report = json.loads(err)
                self.assertTrue(report["request_completed"])
                self.assertTrue(report["do_not_repeat"])
                self.assertEqual(self.remove_report_file(report).read_bytes(), raw)
                self.assertEqual(request.call_count, 1)

    def test_zero_limit_is_explicit_and_nulls_are_not_silently_dropped(self):
        code, out, _, _ = self.invoke(["--limit", "0", "meta"], [{"id": "p", "value": None}])
        self.assertEqual(json.loads(out), {"data": [], "total": 1, "returned": 0, "truncated": True})
        code, out, _, _ = self.invoke(["--fields", "value", "meta"], {"id": "p", "value": None})
        self.assertEqual(json.loads(out), {"value": None})

    def test_large_response_is_saved_losslessly_with_bounded_preview(self):
        raw = json.dumps({"text": "中文" * 10000}, ensure_ascii=False, indent=2).encode()
        code, out, err, _ = self.invoke(["--max-output-chars", "100", "paper", "arxiv:1", "--resource", "content"], response=Response(200, {"Content-Type": "application/json"}, raw))
        self.assertEqual((code, err), (0, ""))
        report = json.loads(out)
        self.assertEqual(report["reason"], "output_limit")
        self.assertTrue(report["truncated"])
        self.assertLessEqual(len(report["preview"]), 100)
        self.assertEqual(report["bytes"], len(raw))
        self.assertEqual(self.remove_report_file(report).read_bytes(), raw)
        self.assertLess(len(out), 1000)
        code, out, _, _ = self.invoke(["--max-output-chars", "0", "meta"], response=Response(200, {}, raw))
        self.assertEqual(json.loads(out), json.loads(raw))

    def test_binary_media_and_plain_text_have_json_output(self):
        for raw, kind in [(b'%PDF-ascii', 'application/pdf'), (b'\x00\xff', 'application/octet-stream'), (b'123', 'application/octet-stream')]:
            code, out, err, _ = self.invoke(["task", "task-1", "--result"], response=Response(200, {"Content-Type": kind}, raw))
            self.assertEqual((code, err), (0, ""))
            report = json.loads(out)
            self.assertEqual(report["reason"], "binary_response")
            self.assertEqual(self.remove_report_file(report).read_bytes(), raw)
        code, out, err, _ = self.invoke(["meta"], response=Response(200, {"Content-Type": "text/plain"}, b"hello"))
        self.assertEqual(json.loads(out), {"text": "hello"})

    def test_explicit_output_is_raw_and_summary_is_opt_in(self):
        raw = b'{ "content": "unchanged" }'
        target = self.root / "raw.json"
        for summary in (False, True):
            args = ["--output", str(target)] + (["--output-summary"] if summary else []) + ["meta"]
            code, out, err, _ = self.invoke(args, response=Response(200, {"Content-Type": "application/json"}, raw))
            self.assertEqual((code, err), (0, ""))
            self.assertEqual(target.read_bytes(), raw)
            if summary:
                self.assertEqual(json.loads(out)["file"], str(target.resolve()))
            else:
                self.assertEqual(out, "")

    def test_invalid_options_do_not_send_and_parse_errors_are_json(self):
        for options in (["--output-summary"], ["--limit", "-1"], ["--max-output-chars", "-1"],
                        ["--fields", "id,id"], ["--fields", ""],
                        ["--output", str(self.root / "x"), "--select", "/items"]):
            code, out, err, request = self.invoke(options + ["meta"])
            self.assertEqual((code, out), (2, ""))
            json.loads(err)
            request.assert_not_called()
        code, out, err, request = self.invoke(["paper"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(err)["error_code"], "invalid_arguments")
        request.assert_not_called()

    def test_read_saved_response_locally_without_key_or_network(self):
        raw = self.root / "saved.json"
        data = {"data": [{"id": "p1", "content": "x" * 20000}]}
        raw.write_text(json.dumps(data), encoding="utf-8")
        with patch.dict(os.environ, {}, clear=True):
            code, out, err, request = self.invoke(["--select", "/data", "--fields", "id", "read-output", str(raw)])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out), [{"id": "p1"}])
        request.assert_not_called()
        code, out, _, request = self.invoke(["read-output", str(raw)])
        self.assertEqual(json.loads(out)["file"], str(raw.resolve()))
        request.assert_not_called()
        self.assertEqual(json.loads(raw.read_text()), data)

    def test_output_save_failure_preserves_successful_response(self):
        raw = b'{"task_id":"already-created"}'
        code, out, err, request = self.invoke(["--output", str(self.root / "missing" / "out.json"),
               "parse-pdf", "--body", '{}'], response=Response(200, {}, raw))
        self.assertEqual((code, out), (2, ""))
        report = json.loads(err)
        self.assertTrue(report["request_completed"])
        self.assertEqual(self.remove_report_file(report).read_bytes(), raw)
        self.assertEqual(request.call_count, 1)

    def test_missing_fields_identify_failing_row_without_record_values(self):
        source = self.root / "heterogeneous.json"
        data = {"data": [{"id": "p1", "url": "first-link"},
                         {"id": "p2", "pdf_url": "private-record-value", "title": None}]}
        source.write_text(json.dumps(data), encoding="utf-8")
        args = ["--select", "/data", "--fields", "id,url", "read-output", str(source)]
        code, out, err, request = self.invoke(args)
        self.assertEqual((code, out), (2, ""))
        report = json.loads(err)
        self.assertEqual(report["error_code"], "local_error")
        self.assertEqual(report["details"], {"select": "/data", "item_index": 1,
            "missing_fields": ["url"], "available_fields": ["id", "pdf_url", "title"]})
        self.assertNotIn("private-record-value", err)
        request.assert_not_called()
        self.assertEqual(json.loads(source.read_text()), data)
        code, out, err, request = self.invoke(["--select", "/data", "--fields", "id",
                                              "read-output", str(source)])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out), [{"id": "p1"}, {"id": "p2"}])
        request.assert_not_called()

    def test_completed_request_field_error_can_be_repaired_without_retry(self):
        raw = b'{"data":[{"paper_id":"p1","pdf_url":"https://example.org/paper"}]}'
        code, out, err, request = self.invoke(["--select", "/data", "--fields", "paper_id,links,url",
            "search", "topic"], response=Response(200, {"Content-Type": "application/json"}, raw))
        self.assertEqual((code, out), (2, ""))
        report = json.loads(err)
        self.assertEqual(report["error_code"], "response_output_error")
        self.assertTrue(report["request_completed"])
        self.assertTrue(report["do_not_repeat"])
        self.assertEqual(report["details"]["missing_fields"], ["links", "url"])
        self.assertEqual(report["details"]["available_fields"], ["paper_id", "pdf_url"])
        source = self.remove_report_file(report)
        self.assertEqual(source.read_bytes(), raw)
        self.assertEqual(request.call_count, 1)
        code, out, err, request = self.invoke(["--select", "/data", "--fields", "paper_id,pdf_url",
                                              "read-output", str(source)])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out), json.loads(raw)["data"])
        request.assert_not_called()

    def test_field_diagnostics_for_single_object_and_non_object_rows(self):
        source = self.root / "types.json"
        source.write_text(json.dumps({"data": [{"id": None}, "private-record-value"]}), encoding="utf-8")
        for pointer, fields, expected in [
            ("/data/0", "url", {"select": "/data/0", "missing_fields": ["url"], "available_fields": ["id"]}),
            ("/data", "id", {"select": "/data", "item_index": 1, "expected_type": "object", "actual_type": "str"}),
        ]:
            for human in (False, True):
                with self.subTest(pointer=pointer, human=human):
                    args = (["--human-errors"] if human else []) + ["--select", pointer,
                        "--fields", fields, "read-output", str(source)]
                    code, out, err, request = self.invoke(args)
                    self.assertEqual((code, out), (2, ""))
                    details = json.loads(err.splitlines()[-1]) if human else json.loads(err)["details"]
                    self.assertEqual(details, expected)
                    self.assertNotIn("private-record-value", err)
                    request.assert_not_called()

    def test_compact_errors_keep_uncertainty_and_trace_ids(self):
        error = LinxSciError("upstream-private-content", 502, {"error": {"code": -3905}, "extra": {"request-id": "framework-id"}},
                             {"X-Request-ID": "upstream-id", "Retry-After": "20"})
        code, out, err, request = self.invoke(["upload", "sample.pdf"], error=error)
        report = json.loads(err)
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(err.count("\n"), 1)
        self.assertEqual(report["error_code"], -3905)
        self.assertTrue(report["execution_uncertain"])
        self.assertEqual(report["request_id"], "upstream-id")
        self.assertEqual(report["framework_request_id"], "framework-id")
        self.assertEqual(report["retry_after"], "20")
        self.assertNotIn("upstream-private-content", err)
        self.assertEqual(request.call_count, 1)
        _, _, err, _ = self.invoke(["meta"], error=LinxSciError("private", 401))
        self.assertNotIn("request_id", json.loads(err))
        _, _, err, _ = self.invoke(["--human-errors", "meta"], error=error)
        self.assertIn("框架请求 ID", err)
        self.assertFalse(err.startswith("{"))


if __name__ == "__main__":
    unittest.main()
