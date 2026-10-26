#!/usr/bin/env python3
"""Exercise wheel and ZIP in isolated directories against a local fake API."""
import argparse
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
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from cli_cases import shortcut_cases


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


def check(directory, uv=None):
    root = Path(__file__).resolve().parents[1]
    version = re.search(r'^version = "([^"]+)"', (root / "pyproject.toml").read_text(), re.MULTILINE).group(1)
    document = (root / "docs/API.md").read_text(encoding="utf-8")
    routes = re.findall(r"\| (GET|POST) \| `/openapi/v2([^`]+)` \|", document)
    assert len(routes) == 34
    wheel = directory / ("linxsci-" + version + "-py3-none-any.whl")
    bundle = directory / ("linxsci-skills-" + version + ".zip")
    server = HTTPServer(("127.0.0.1", 0), API)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = "http://127.0.0.1:" + str(server.server_port)
    try:
        with tempfile.TemporaryDirectory(prefix="linxsci-smoke-") as temporary:
            root = Path(temporary)
            env = dict(os.environ)
            for name in ("LINXSCI_BASE_URL", "LINXSCI_OPENAPI_KEY", "LINXSCI_MINERU_API_KEY", "PYTHONPATH"):
                env.pop(name, None)
            env["LINXSCI_CONFIG_FILE"] = str(root / "config.json")
            def run(command, stdin=None):
                result = subprocess.run(command, input=stdin, text=True, capture_output=True, env=env, cwd=root)
                if result.returncode:
                    raise RuntimeError("Release smoke failed: " + result.stdout + result.stderr)
                assert "release-smoke-key" not in result.stdout + result.stderr
                return result.stdout
            def check_all_routes(command):
                identifiers = {"paper_id": "doi:10.1000/example", "task_id": "task/1",
                               "section_id": "section-1", "asset_id": "asset-1", "author_id": "author/1",
                               "institution_id": "institution/1", "venue_id": "venue/1"}
                encoded = {key: quote(value, safe=":") for key, value in identifiers.items()}
                source = root / "sample.pdf"
                source.write_bytes(b"%PDF-smoke\x00")
                body_file = root / "synthetic-request.json"
                body_file.write_text('{"query":"release coverage"}', encoding="utf-8")
                cases = shortcut_cases(identifiers, body_file, source)
                assert set(cases) == set(routes)
                for method, template in routes:
                    path = template.format(**encoded)
                    response = json.loads(run(command + cases[(method, template)]))
                    if path == "/papers/search":
                        assert response["data"][0]["query"] == "release coverage"
                    else:
                        assert response["data"]["path"] == "/openapi/v2" + path
            venv.EnvBuilder(with_pip=True).create(root / "venv")
            python = root / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            run([str(python), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel.resolve())])
            executable = root / "venv" / ("Scripts/linxsci.exe" if os.name == "nt" else "bin/linxsci")
            assert run([str(executable), "--version"]).strip() == version
            cli = [str(executable)]
            run(cli + ["setup", "--api-key-stdin", "--base-url", base_url], "release-smoke-key\n")
            check_all_routes(cli)
            assert json.loads(run(cli + ["doctor", "--json"]))["ok"]
            assert json.loads(run(cli + ["search", "test topic"]))["data"][0]["query"] == "test topic"
            run(cli + ["install-skill", "--skills-dir", str(root / "wheel-skills")])
            installed = root / "wheel-skills/linxsci-skills/scripts/cli.py"
            run([str(python), str(installed), "doctor"])
            run([str(python), "-c", "from linxsci import LinxSciClient; print(LinxSciClient().request('GET','/meta').status)"])
            with zipfile.ZipFile(bundle) as archive:
                archive.extractall(root / "bundle")
            unpacked = next((root / "bundle").iterdir())
            run([str(python), str(unpacked / "install.py"), "--no-config", "--skills-dir", str(root / "zip-skills")])
            installed = root / "zip-skills/linxsci-skills/scripts/cli.py"
            check_all_routes([str(python), str(installed)])
            assert len(json.loads(run([str(python), str(installed), "routes"]))) == 34
            run([str(python), str(installed), "doctor"])
            run([str(python), str(installed), "paper", "doi:10.1000/example", "--resource", "toc"])
            run([str(python), str(unpacked / "install.py"), "--no-config", "--update", "--skills-dir", str(root / "zip-skills")])
            assert list((root / "linxsci-skill-backups").iterdir())
            if uv:
                env.update(UV_TOOL_DIR=str(root / "uv-tools"), UV_TOOL_BIN_DIR=str(root / "uv-bin"),
                           UV_CACHE_DIR=str(root / "uv-cache"), UV_PYTHON_DOWNLOADS="never")
                run([uv, "tool", "install", "--offline", "--python", str(python), str(wheel.resolve())])
                uv_executable = root / "uv-bin" / ("linxsci.exe" if os.name == "nt" else "linxsci")
                assert run([str(uv_executable), "--version"]).strip() == version
                uv_cli = [str(uv_executable)]
                check_all_routes(uv_cli)
                run(uv_cli + ["install-skill", "--skills-dir", str(root / "uv-skills")])
                uv_skill = root / "uv-skills/linxsci-skills/scripts/cli.py"
                assert json.loads(run([str(python), str(uv_skill), "search", "uv topic"]))["data"][0]["query"] == "uv topic"
                run(uv_cli + ["install-skill", "--skills-dir", str(root / "uv-skills"), "--update"])
                run([uv, "tool", "uninstall", "linxsci"])
                assert not uv_executable.exists()
            run([str(python), str(installed), "config", "--clear"])
            assert not (root / "config.json").exists()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    print("Fresh wheel and ZIP: all 34 convenience routes each, install, configure, connect, SDK, update and clear passed.")
    if uv:
        print("uv tool install: all 34 convenience routes, bundled Skill install/update and tool uninstall passed in isolated directories.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", default="dist", type=Path)
    parser.add_argument("--uv", metavar="EXECUTABLE", help="Also verify an isolated uv tool installation using this executable")
    args = parser.parse_args()
    check(args.directory.resolve(), uv=args.uv)
