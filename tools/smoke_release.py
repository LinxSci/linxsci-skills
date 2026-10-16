#!/usr/bin/env python3
"""Exercise wheel and ZIP in isolated directories against a local fake API."""
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import venv
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


class API(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.respond()

    def do_POST(self):
        self.respond()

    def respond(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.headers.get("Authorization") != "Bearer release-smoke-key":
            self.send_response(401)
            body = {"error": {"code": "unauthorized"}}
        else:
            self.send_response(200)
            if self.path.endswith("/papers/search"):
                body = {"data": [{"id": "arxiv:2301.07041", "query": json.loads(raw)["query"]}]}
            else:
                body = {"data": {"path": self.path}}
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())


def check(directory):
    root = Path(__file__).resolve().parents[1]
    version = re.search(r'^version = "([^"]+)"', (root / "pyproject.toml").read_text(), re.MULTILINE).group(1)
    document = (root / "Scholar-OpenAPI-v2-使用文档.md").read_text(encoding="utf-8")
    routes = re.findall(r"\| (GET|POST) \| `/openapi/v2([^`]+)` \|", document)
    assert len(routes) == 34
    wheel = directory / ("linxsci_scholar_sdk-" + version + "-py3-none-any.whl")
    bundle = directory / ("linxsci-scholar-" + version + ".zip")
    server = HTTPServer(("127.0.0.1", 0), API)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = "http://127.0.0.1:" + str(server.server_port)
    try:
        with tempfile.TemporaryDirectory(prefix="linxsci-smoke-") as temporary:
            root = Path(temporary)
            env = dict(os.environ)
            for name in ("SCHOLAR_BASE_URL", "SCHOLAR_OPENAPI_KEY", "SCHOLAR_MINERU_API_KEY", "PYTHONPATH"):
                env.pop(name, None)
            env["SCHOLAR_CONFIG_FILE"] = str(root / "config.json")
            def run(command, stdin=None):
                result = subprocess.run(command, input=stdin, text=True, capture_output=True, env=env, cwd=root)
                if result.returncode:
                    raise RuntimeError("Release smoke failed: " + result.stdout + result.stderr)
                assert "release-smoke-key" not in result.stdout + result.stderr
                return result.stdout
            def check_all_routes(command):
                identifiers = {"paper_id": "doi:10.1000%2Fexample", "task_id": "task-1",
                               "section_id": "section-1", "asset_id": "asset-1", "author_id": "author-1",
                               "institution_id": "institution-1", "venue_id": "venue-1"}
                source = root / "sample.pdf"
                source.write_bytes(b"%PDF-smoke\x00")
                for method, template in routes:
                    path = template.format(**identifiers)
                    if path == "/pdf/parse/upload":
                        result = run(command + ["upload", str(source)])
                    else:
                        args = ["request", method, path]
                        if method == "POST":
                            # Synthetic request for the local fake API, not a business schema.
                            args += ["--body", '{"query":"release coverage"}']
                        result = run(command + args)
                    response = json.loads(result)
                    if path == "/papers/search":
                        assert response["data"][0]["query"] == "release coverage"
                    else:
                        assert response["data"]["path"] == "/openapi/v2" + path
            venv.EnvBuilder(with_pip=True).create(root / "venv")
            python = root / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            run([str(python), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel.resolve())])
            executable = root / "venv" / ("Scripts/linxsci.exe" if os.name == "nt" else "bin/linxsci")
            assert run([str(executable), "--version"]).strip() == version
            cli = [str(executable), "scholar"]
            run(cli + ["setup", "--api-key-stdin", "--base-url", base_url], "release-smoke-key\n")
            check_all_routes(cli)
            assert json.loads(run(cli + ["doctor", "--json"]))["ok"]
            assert json.loads(run(cli + ["search", "test topic"]))["data"][0]["query"] == "test topic"
            run(cli + ["install-skill", "--skills-dir", str(root / "wheel-skills")])
            installed = root / "wheel-skills/linxsci-scholar/scripts/cli.py"
            run([str(python), str(installed), "scholar", "doctor"])
            run([str(python), "-c", "from linxsci_scholar import ScholarClient; from scholar_client import ScholarClient as Legacy; assert Legacy is ScholarClient; print(ScholarClient().request('GET','/meta').status)"])
            with zipfile.ZipFile(bundle) as archive:
                archive.extractall(root / "bundle")
            unpacked = next((root / "bundle").iterdir())
            run([str(python), str(unpacked / "install.py"), "--no-config", "--skills-dir", str(root / "zip-skills")])
            installed = root / "zip-skills/linxsci-scholar/scripts/cli.py"
            check_all_routes([str(python), str(installed), "scholar"])
            assert len(json.loads(run([str(python), str(installed), "scholar", "routes"]))) == 34
            run([str(python), str(installed), "scholar", "doctor"])
            run([str(python), str(installed), "scholar", "paper", "doi:10.1000/example", "--resource", "toc"])
            run([str(python), str(unpacked / "install.py"), "--no-config", "--update", "--skills-dir", str(root / "zip-skills")])
            assert list((root / "linxsci-skill-backups").iterdir())
            run([str(python), str(installed), "scholar", "config", "--clear"])
            assert not (root / "config.json").exists()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    print("Fresh wheel and ZIP: all 34 routes each, install, configure, connect, SDK, update and clear passed.")


if __name__ == "__main__":
    check(Path(sys.argv[1] if len(sys.argv) > 1 else "dist").resolve())
