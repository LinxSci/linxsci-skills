import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/linxsci-skills/scripts"))
import cli
from scholar_client import ScholarClient, ScholarError, Response


class UnifiedCLITests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        environment = {"SCHOLAR_CONFIG_FILE": str(self.root / "config.json"),
                       "SCHOLAR_BASE_URL": "http://localhost:9000", "SCHOLAR_OPENAPI_KEY": "root-test-key"}
        self.environment = patch.dict(os.environ, environment, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_root_help_and_version_without_credentials(self):
        for arguments in ([], ["--help"], ["--version"]):
            with self.subTest(arguments=arguments):
                output = io.StringIO()
                with patch.dict(os.environ, {}, clear=True), contextlib.redirect_stdout(output):
                    if arguments:
                        with self.assertRaises(SystemExit) as result:
                            cli.main(arguments)
                        self.assertEqual(result.exception.code, 0)
                    else:
                        self.assertEqual(cli.main(arguments), 0)
                self.assertIn(cli.VERSION if arguments == ["--version"] else "search", output.getvalue())

    def test_help_and_routes_without_network(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaises(SystemExit) as result:
            cli.main(["--help"])
        self.assertEqual(result.exception.code, 0)
        self.assertIn("linxsci", output.getvalue())
        output = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), patch.object(ScholarClient, "request") as request, contextlib.redirect_stdout(output):
            self.assertEqual(cli.main(["routes"]), 0)
            self.assertEqual(len(json.loads(output.getvalue())), 34)
            request.assert_not_called()

    def test_forwarding_and_future_capability_registration(self):
        received = []
        def handler(argv, *, prog):
            received.append((argv, prog))
            return 7
        arguments = ["--output", "a file.json", "search", "-3905"]
        with patch.dict(cli.CAPABILITIES, {"test-capability": ("Only for this test", handler)}, clear=True):
            self.assertEqual(cli.main(["test-capability"] + arguments), 7)
        self.assertEqual(received, [(arguments, "linxsci test-capability")])

    def test_unknown_capability_and_missing_action(self):
        for arguments in (["patents", "search", "example"], ["scholar"], ["scholar", "search", "example"]):
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
                cli.main(arguments)
            self.assertEqual(result.exception.code, 2)

    def test_search_and_framework_error(self):
        failure = ScholarError("HTTP 502", 502,
                               {"error": {"code": -3905}, "extra": {"request-id": "root-framework"}})
        output, errors = io.StringIO(), io.StringIO()
        with patch.object(ScholarClient, "request", autospec=True, side_effect=failure) as request, contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            self.assertEqual(cli.main(["--json-errors", "--framework-request-id", "root-framework", "search", "-3905"]), 1)
            self.assertEqual(request.call_count, 1)
            self.assertEqual(request.call_args.kwargs["payload"], {"query": "-3905"})
        report = json.loads(errors.getvalue())
        self.assertEqual(report["error_code"], -3905)
        self.assertTrue(report["execution_uncertain"])
        self.assertNotIn("root-test-key", output.getvalue() + errors.getvalue())

    def test_search_commands_share_query_and_optional_body(self):
        extra = {"query": "ignored", "opaque": {"values": [1, False, None], "text": "中文"}}
        source = self.root / "search.json"
        source.write_text(json.dumps(extra, ensure_ascii=False), encoding="utf-8")
        for command, path in (("search", "/papers/search"), ("search-openalex", "/search/openalex"),
                              ("search-semantic-scholar", "/search/semantic-scholar"),
                              ("search-google-scholar", "/search/google-scholar")):
            for options in ([], ["--body", json.dumps(extra)], ["--body", "@" + str(source)]):
                with self.subTest(command=command, options=options), patch.object(ScholarClient, "request", return_value=Response(200, {}, b"{}")) as request, contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(cli.main([command, "large language models 中文"] + options), 0)
                    request.assert_called_once()
                    self.assertEqual(request.call_args.args, ("POST", path))
                    self.assertEqual(request.call_args.kwargs["payload"],
                                     {**(extra if options else {}), "query": "large language models 中文"})

    def test_search_missing_query_and_invalid_body_do_not_send(self):
        for command in ("search", "search-openalex", "search-semantic-scholar", "search-google-scholar"):
            for options in ([], ["--body", '{"query":"topic"}'], ["topic", "--body", "[]"],
                            ["topic", "--body", "null"], ["topic", "--body", "{"]):
                with self.subTest(command=command, options=options), patch.object(ScholarClient, "request") as request, contextlib.redirect_stderr(io.StringIO()):
                    try:
                        code = cli.main([command] + options)
                    except SystemExit as error:
                        code = error.code
                    self.assertEqual(code, 2)
                    request.assert_not_called()

    def test_invalid_shortcuts_do_not_send_requests(self):
        cases = [
            ["health"], ["health", "--live", "--ready"], ["health", "live", "--ready"],
            ["resolve"], ["parse-pdf"], ["author"],
            ["author", ".."], ["institution", ""], ["venue", "."],
            ["paper", "arxiv:1", "--resource", "sections"],
            ["paper", "arxiv:1", "--item-id", "unexpected"],
            ["paper", "arxiv:1", "--resource", "toc", "--item-id", "unexpected"],
            ["task", "upload"], ["recommend", "--body", "{"],
            ["batch-get", "--body", "@" + str(self.root / "missing.json")],
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments), patch.object(ScholarClient, "request") as request, contextlib.redirect_stderr(io.StringIO()):
                try:
                    code = cli.main(arguments)
                except SystemExit as error:
                    code = error.code
                self.assertEqual(code, 2)
                request.assert_not_called()

    def test_global_options_and_binary_output(self):
        output = self.root / "asset.bin"
        data = b"\x00\xffasset"
        with patch.object(ScholarClient, "request", autospec=True, return_value=Response(200, {}, data)) as request:
            self.assertEqual(cli.main(["--timeout", "12", "--output", str(output), "paper", "doi:10.1000/example", "--resource", "assets", "--item-id", "figure1"]), 0)
            self.assertEqual(request.call_args.args[0].timeout, 12)
            self.assertIn("doi:10.1000%2Fexample/assets/figure1", request.call_args.args[2])
        self.assertEqual(output.read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
