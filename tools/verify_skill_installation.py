#!/usr/bin/env python3
"""Verify an actual single Idea ZIP, package installation and continuation using local fixtures."""
import argparse
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile

from skill_release import (INSTALLER_PATH, check, encoded, guarded, json_bytes,
                           require, sha256, zip_bytes, zip_items)
from smoke_skill_releases import smoke, unpack


class FixtureHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.server.requests.append(self.path)
        mode = self.server.mode
        if mode == 'timeout':
            time.sleep(0.2)
        if mode == '404':
            self.send_error(404)
            return
        if mode == 'redirect':
            self.send_response(302)
            self.send_header('Location', 'http://example.invalid/not-a-release')
            self.end_headers()
            return
        path = self.server.assets / self.path.rsplit('/', 1)[-1]
        if not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data[:10] if mode == 'interrupted' else data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        # Research API fixture: only the quick search route is needed for these tasks.
        if self.path != '/openapi/v2/papers/search' or self.headers.get('Authorization') != 'Bearer fixture-key':
            self.send_error(400)
            return
        payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
        self.server.api_calls.append(payload)
        names = ['old', 'shared'] if payload.get('query') == 'initial' else ['old', 'new']
        data = encoded({'data': [{'paper_id': 'local:' + n, 'title': 'Synthetic ' + n,
                                  'year': 2024, 'abstract': 'Local fixture, not a real paper.'} for n in names],
                        'meta': {'has_more': False}})
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-Request-ID', 'fixture-' + str(len(self.server.api_calls)))
        self.end_headers()
        self.wfile.write(data)


def verify(directory):
    directory = directory.resolve()
    summary = check(directory)
    manifest_data = (directory / 'release-manifest.json').read_bytes()
    manifest = json_bytes(manifest_data)
    require(manifest.get('dependency_installation') == 'explicit-package-installer-v1',
            'These assets do not contain the package installer. Rebuild from the intended source commits.')
    # A publication report covers all eight entrypoints as well as the dependency flow.
    summary = smoke(directory)
    asset_hashes = {p.name: sha256(p.read_bytes()) for p in directory.iterdir()}
    checks = []
    with tempfile.TemporaryDirectory(prefix='linxsci-install-acceptance-') as temporary:
        root = Path(temporary).resolve()
        idea = root / 'user skills' / 'linxsci-idea'
        unpack((directory / manifest['skills']['linxsci-idea']['artifact']['file']).read_bytes(), idea)
        require(not (idea / 'tests').exists() and (idea / INSTALLER_PATH).is_file(), 'Expected a standalone single Idea package.')
        environment = root / 'environment'
        created = subprocess.run([sys.executable, '-m', 'venv', str(environment)], capture_output=True, timeout=120)
        require(created.returncode == 0, 'Could not create acceptance environment.')
        binary = environment / ('Scripts' if os.name == 'nt' else 'bin')
        python = binary / ('python.exe' if os.name == 'nt' else 'python')
        env = {k: v for k, v in os.environ.items() if not k.startswith(('LINXSCI_', 'PYTHON', 'PIP_')) and k != 'VIRTUAL_ENV'}
        env.update(PATH=str(binary), PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1',
                   PYTHONUTF8='1', PIP_CONFIG_FILE=os.devnull, PIP_DISABLE_PIP_VERSION_CHECK='1',
                   LINXSCI_CONFIG_FILE=str(root / 'unused-config.json'), LINXSCI_SKILLS_DIR=str(idea.parent))
        require(shutil.which('git', path=env['PATH']) is None, 'Git must be absent from the user environment.')
        work = root / 'original research directory'
        work.mkdir()

        def run(label, arguments, expected=0):
            result = subprocess.run([str(a) for a in arguments], cwd=work, env=env, stdin=subprocess.DEVNULL,
                                    capture_output=True, text=True, timeout=60)
            require(result.returncode == expected,
                    'Installation acceptance failed: ' + label + '\n' + (result.stdout + result.stderr)[-1500:])
            checks.append({'check': label, 'exit': result.returncode})
            return result

        run('offline-sdk-install', [python, '-m', 'pip', '--isolated', 'install', '--no-index', '--no-deps',
                                    directory / manifest['sdk']['artifact']['file']])
        runtime = json.loads(run('sdk-location', [python, '-I', '-c',
            "import json,linxsci; print(json.dumps({'version':linxsci.__version__,'file':linxsci.__file__}))"]).stdout)
        require(runtime['version'] == manifest['sdk']['version'] and environment in Path(runtime['file']).resolve().parents,
                'Acceptance imported the wrong SDK or development source.')
        server = ThreadingHTTPServer(('127.0.0.1', 0), FixtureHandler)
        server.assets, server.mode, server.requests, server.api_calls = directory, 'normal', [], []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            survey = idea.parent / 'linxsci-survey'
            entry = [python, '-B', idea / 'scripts/idea.py']
            adapter = [python, '-B', idea / 'scripts/install_survey.py']
            output = work / 'initial evidence.json'
            original = ['initial', '--depth', 'quick', '--survey-dir', survey, '--output', output]
            missing = run('missing-before-install', entry + original)
            require('--assets-dir' in missing.stdout and not output.exists() and not server.api_calls,
                    'Missing dependency must not produce research evidence.')
            run('wrong-suite-rejected', adapter + ['--assets-dir', directory, '--suite-version', '99.99.99',
                                                  '--survey-dir', survey, '--yes'], 2)
            denied = run('confirmation-required', adapter + ['--assets-dir', directory, '--survey-dir', survey], 3)
            require(json.loads(denied.stdout)['status'] == 'confirmation-required' and not survey.exists(),
                    'Unapproved installation must not succeed.')
            base = 'http://127.0.0.1:' + str(server.server_port)
            url = base + '/LinxSci/linxsci-skills/releases/download/' + manifest['suite_tag'] + '/release-manifest.json'
            install_args = adapter + ['--manifest-url', url, '--suite-version', manifest['suite_version'],
                                      '--test-allow-loopback-http', '--survey-dir', survey, '--yes']
            for mode in ('404', 'timeout', 'interrupted', 'redirect'):
                server.mode = mode
                run('http-' + mode, install_args + ['--timeout', '0.05'], 2)
                require(not survey.exists(), 'Failed download left an installation.')
            server.mode = 'normal'
            asset_name = manifest['skills']['linxsci-survey']['artifact']['file']
            original_zip = (directory / asset_name).read_bytes()
            for mode in ('hash', 'size', 'corrupt', 'identity', 'malicious'):
                damaged = root / ('damaged-' + mode)
                shutil.copytree(directory, damaged)
                changed = copy.deepcopy(manifest)
                record = changed['skills']['linxsci-survey']['artifact']
                data = original_zip
                if mode == 'hash':
                    data = bytes([data[0] ^ 1]) + data[1:]
                elif mode == 'size':
                    data += b'damage'
                elif mode == 'corrupt':
                    data = b'not a zip'
                elif mode == 'identity':
                    items = zip_items(data)
                    identity = json_bytes(items['release.json'][0])
                    identity['version'] = '99.99.99'
                    items['release.json'] = (encoded(identity), 0o644)
                    data = zip_bytes(items)
                else:
                    buffer = io.BytesIO()
                    with zipfile.ZipFile(buffer, 'w') as archive:
                        archive.writestr('../escape', b'forbidden')
                    data = buffer.getvalue()
                    record['file_count'] = 1
                if mode not in ('hash', 'size'):
                    record.update(size=len(data), sha256=sha256(data))
                (damaged / asset_name).write_bytes(data)
                (damaged / 'release-manifest.json').write_bytes(encoded(changed))
                sums = {r['artifact']['file']: r['artifact']['sha256'] for r in changed['skills'].values()}
                sums['release-manifest.json'] = sha256(encoded(changed))
                (damaged / 'SHA256SUMS').write_text(''.join(h + '  ' + n + '\n' for n, h in sorted(sums.items())), encoding='utf-8')
                server.assets = damaged
                run('damaged-' + mode, install_args, 2)
                require(not survey.exists() and not (survey.parent / 'escape').exists(), 'Invalid ZIP escaped or installed.')
            server.assets = directory
            injection = """import importlib.util,sys
from pathlib import Path
from unittest.mock import patch
p=Path(sys.argv[1]); s=importlib.util.spec_from_file_location('bundled',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
with patch.object(m,'WINDOWS',False), patch.object(Path,'rename',side_effect=OSError('fixture failure')):
    raise SystemExit(m.main(sys.argv[3:],default_skill='linxsci-survey',default_requester=Path(sys.argv[2])))
"""
            run('publish-rollback', [python, '-I', '-c', injection, idea / INSTALLER_PATH, idea / 'release.json',
                                    '--assets-dir', directory, '--survey-dir', survey, '--yes'], 2)
            require(not survey.exists() and not list(survey.parent.glob('.linxsci-package-*')), 'Rollback left partial files.')
            server.requests.clear()
            installed = run('http-package-install', install_args)
            require(json.loads(installed.stdout)['status'] == 'installed' and len(server.requests) == 3,
                    'Package installation did not complete.')
            require(not (idea.parent / 'linxsci-paper').exists(), 'Conditional collaboration became recursive installation.')
            reused = run('reuse-without-download', install_args)
            require(json.loads(reused.stdout)['status'] == 'reused' and len(server.requests) == 3, 'Reuse downloaded another archive.')
            target = survey / 'scripts/survey.py'
            saved = target.read_bytes()
            target.write_bytes(saved + b'\n# retained local edit\n')
            run('local-edits-preserved', install_args, 2)
            require(target.read_bytes().endswith(b'# retained local edit\n'), 'Local modification was overwritten.')
            target.write_bytes(saved)
            incomplete = root / 'incomplete'
            incomplete.mkdir()
            (incomplete / 'note.txt').write_text('keep', encoding='utf-8')
            run('incomplete-preserved', adapter + ['--assets-dir', directory, '--survey-dir', incomplete, '--yes'], 2)
            require((incomplete / 'note.txt').read_text() == 'keep', 'Incomplete target was overwritten.')
            # Use the production HTTPS selection path with local transport substitution.
            # The child imports only the bundled module; no private source tree is required.
            official = """import importlib.util,sys
from pathlib import Path
from unittest.mock import patch
p=Path(sys.argv[1]); s=importlib.util.spec_from_file_location('bundled',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
a=Path(sys.argv[2])
def fixture_fetch(url,limit,timeout,test_http=False):
    assert not test_http
    m.validate_transport(url)
    data=(a/url.rsplit('/',1)[-1]).read_bytes()
    assert len(data)<=limit
    return data
with patch.object(m,'fetch',fixture_fetch):
    raise SystemExit(m.main(sys.argv[4:],default_skill='linxsci-survey',default_requester=Path(sys.argv[3])))
"""
            run('official-source-state', [python, '-I', '-c', official, idea / INSTALLER_PATH, directory, idea / 'release.json',
                '--manifest-url', manifest['manifest_url'], '--suite-version', manifest['suite_version'],
                '--survey-dir', root / 'official-survey', '--yes'], 0 if manifest['published'] else 2)
            env.update(LINXSCI_BASE_URL=base, LINXSCI_OPENAPI_KEY='fixture-key')
            run('original-task-resumed', entry + original)
            first = output.read_bytes()
            require(json.loads(first)['mode'] == 'idea_evidence' and len(server.api_calls) == 1, 'Original research task did not resume.')
            follow = work / 'follow-up.json'
            run('follow-up-resumed', entry + ['--previous-idea', output, '--supplement-query', 'supplement', '--depth', 'quick',
                                            '--survey-dir', survey, '--output', follow])
            require(output.read_bytes() == first and json.loads(follow.read_bytes())['follow_up']['turn'] == 2,
                    'Continuation changed earlier evidence or lost task state.')
            calls, requests = len(server.api_calls), len(server.requests)
            survey.rename(root / 'retained-survey')
            run('evidence-reuse-without-survey', entry + ['--previous-idea', output, '--follow-up', 'refine existing evidence'])
            require(len(server.api_calls) == calls and len(server.requests) == requests and not survey.exists(),
                    'Evidence reuse fetched a dependency or new research data.')
            require(not (root / 'unused-config.json').exists(), 'Acceptance changed user configuration.')
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
    return {**summary, 'schema_version': 1, 'passed': True, 'manifest_sha256': sha256(manifest_data),
            'assets_sha256': asset_hashes,
            'checks': checks, 'skips': 0, 'platform': sys.platform, 'python': sys.version.split()[0],
            'git_available': False, 'sdk': runtime['version'], 'sdk_source': 'isolated bundled wheel',
            'idea_from_single_zip': True, 'business_api': 'local synthetic fixture only',
            'public_download_tested': False, 'official_source_transport': 'local substitution',
            'limits': ['Agent discovery and SkillHub are separate acceptance steps.',
                       'Research fixture outputs are not real research results.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--report', type=Path, required=True, help='New report path outside immutable assets.')
    args = parser.parse_args()
    require(not args.report.resolve().is_relative_to(args.directory.resolve()), 'Keep reports outside immutable assets.')
    require(not args.report.exists(), 'Report already exists; choose a new path.')
    report = verify(args.directory)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8') as stream:
        stream.write(encoded(report).decode('utf-8'))
    print(json.dumps({'passed': True, 'checks': len(report['checks']), 'report': str(args.report)}, ensure_ascii=False))


if __name__ == '__main__':
    guarded(main)
