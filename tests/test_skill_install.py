"""Package installation against real candidate ZIPs or explicit synthetic fixtures."""
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import skill_install as install
import skill_release as release


def synthetic_assets(root):
    """No Git provenance is claimed by this explicitly named test suite."""
    recipe = json.loads((release.ROOT / 'release/suite.json').read_text())
    recipe['suite_version'] = '0.0.0-test.1'
    url = install.canonical(recipe['suite_version'])
    records = {}
    for name in release.NAMES:
        spec = recipe['skills'][name]
        tree = {'SKILL.md': (('---\nname: ' + name + '\n---\n').encode(), 0o644),
                spec['entrypoint']: (b'import argparse\nargparse.ArgumentParser().parse_args()\n', 0o644)}
        if recipe.get('license'):
            tree['LICENSE'] = ((release.ROOT / 'LICENSE').read_bytes(), 0o644)
        if name != 'linxsci-base':
            tree['requirements.txt'] = (b'linxsci==0.3.4\n', 0o644)
        if name == 'linxsci-survey':
            tree['scripts/survey_workflow.py'] = (b'def prepare_survey(): pass\ndef record(): pass\ndef paper_path(): pass\n', 0o644)
        main_tree = {'skills/linxsci-base/' + k: v for k, v in tree.items()}
        if 'LICENSE' in tree:
            main_tree['LICENSE'] = tree['LICENSE']
        files, identity = release.make_skill(name, tree, main_tree,
                                             '0' * 40, recipe, url + 'release-manifest.json')
        filename = name + ('-skill-' if name == 'linxsci-base' else '-') + recipe['suite_version'] + '.zip'
        data = release.zip_bytes(files)
        (root / filename).write_bytes(data)
        records[name] = {k: v for k, v in identity.items() if k != 'files'}
        records[name]['artifact'] = dict(release.artifact(filename, data, url.rstrip('/')), file_count=len(files))
    return {'schema_version': 1, 'status': 'candidate', 'published': False, 'suite_version': recipe['suite_version'],
            'suite_tag': 'suite-v' + recipe['suite_version'], 'manifest_url': url + 'release-manifest.json',
            'sources': {name: '0' * 40 for name in release.NAMES}, 'sdk': recipe['sdk'], 'skills': records}


class AssetsHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        self.server.requests.append(self.path)
        if self.server.mode == 'timeout':
            time.sleep(0.2)
        if self.server.mode == '404':
            self.send_error(404)
            return
        if self.server.mode == 'redirect':
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
            self.wfile.write(data[:10] if self.server.mode == 'interrupted' else data)
        except (BrokenPipeError, ConnectionResetError):
            pass


class InstallTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='linxsci-install-test-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.assets = self.root / 'assets'
        candidate = Path(os.environ.get('LINXSCI_INSTALL_TEST_ASSETS') or release.ROOT / 'dist/suite-0.1.0-rc.1')
        if candidate.is_dir():
            shutil.copytree(candidate, self.assets)
            self.manifest = json.loads((self.assets / 'release-manifest.json').read_text())
        else:
            self.assets.mkdir()
            self.manifest = synthetic_assets(self.assets)
            self.save_manifest()
        self.target = self.root / 'installed skills' / 'linxsci-survey'

    def save_manifest(self):
        (self.assets / 'release-manifest.json').write_bytes(release.encoded(self.manifest))
        sums = {record['artifact']['file']: record['artifact']['sha256'] for record in self.manifest['skills'].values()}
        sums['release-manifest.json'] = install.digest((self.assets / 'release-manifest.json').read_bytes())
        (self.assets / 'SHA256SUMS').write_text(''.join(value + '  ' + name + '\n' for name, value in sorted(sums.items())))

    def run_install(self, **kwargs):
        options = {'assets_dir': self.assets, 'yes': True}
        options.update(kwargs)
        return install.install('linxsci-survey', self.target, **options)

    def archive(self):
        return self.assets / self.manifest['skills']['linxsci-survey']['artifact']['file']

    def change_zip(self, mutate):
        record = self.manifest['skills']['linxsci-survey']
        files = release.zip_items(self.archive().read_bytes())
        mutate(files)
        data = release.zip_bytes(files)
        self.archive().write_bytes(data)
        record['artifact'].update(size=len(data), sha256=install.digest(data), file_count=len(files))
        self.save_manifest()

    def http(self, mode='normal'):
        server = ThreadingHTTPServer(('127.0.0.1', 0), AssetsHandler)
        server.assets, server.mode, server.requests = self.assets, mode, []
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        def close():
            server.shutdown(); thread.join(); server.server_close()
        self.addCleanup(close)
        url = 'http://127.0.0.1:' + str(server.server_port) + '/LinxSci/linxsci-skills/releases/download/' + self.manifest['suite_tag'] + '/release-manifest.json'
        return server, {'assets_dir': None, 'manifest_url': url, 'suite_version': self.manifest['suite_version'], 'test_http': True}

    def test_real_zip_installs_without_git_and_reuses_without_download(self):
        with patch.dict(os.environ, {'PATH': ''}):
            first = self.run_install()
            with patch.object(install.Source, 'read', side_effect=AssertionError('unexpected download')):
                second = self.run_install(assets_dir=None)
        self.assertEqual((first['status'], second['status']), ('installed', 'reused'))
        self.assertFalse((self.target / '.git').exists())
        self.assertFalse((self.target.parent / 'linxsci-paper').exists())
        self.assertEqual(list(self.target.parent.glob('.linxsci-package-*')), [])

    def test_same_suite_requester_is_required(self):
        requester = self.root / 'requester.json'
        identity = {k: v for k, v in self.manifest['skills']['linxsci-idea'].items() if k != 'artifact'}
        requester.write_bytes(release.encoded(identity))
        self.assertEqual(self.run_install(requester=requester)['status'], 'installed')
        identity['suite_version'] = identity['version'] = '9.9.9'
        requester.write_bytes(release.encoded(identity))
        with self.assertRaisesRegex(install.InstallError, 'version mismatch'):
            self.run_install(requester=requester)

    def test_same_version_requester_cannot_select_different_source(self):
        requester = self.root / 'requester.json'
        identity = copy.deepcopy({k: v for k, v in self.manifest['skills']['linxsci-idea'].items() if k != 'artifact'})
        identity['source']['commit'] = 'f' * 40
        requester.write_bytes(release.encoded(identity))
        with self.assertRaisesRegex(install.InstallError, 'Requester identity/source'):
            self.run_install(requester=requester)
        self.assertFalse(self.target.exists())

    def test_declined_noninteractive_does_not_read_or_write(self):
        with patch.object(install.Source, 'read', side_effect=AssertionError('not authorized')):
            self.assertEqual(self.run_install(yes=False)['status'], 'confirmation-required')
        self.assertFalse(self.target.parent.exists())

    def test_http_install_and_receipt_reuse_without_http(self):
        server, options = self.http()
        self.assertEqual(self.run_install(**options)['status'], 'installed')
        self.assertEqual(len(server.requests), 3)
        self.assertEqual(self.run_install(**options)['status'], 'reused')
        self.assertEqual(len(server.requests), 3)

    def test_http_requires_explicit_test_flag(self):
        _, options = self.http()
        options['test_http'] = False
        with self.assertRaises(install.InstallError):
            self.run_install(**options)
        self.assertFalse(self.target.exists())

    def test_unpublished_candidate_rejected_as_public_release(self):
        manifest = release.encoded(self.manifest)
        with patch.object(install, 'fetch', return_value=manifest):
            with self.assertRaisesRegex(install.InstallError, 'not publicly released'):
                install.Source(manifest_url=self.manifest['manifest_url'], version=self.manifest['suite_version'])

    def test_fixed_official_manifest_uses_matching_release_assets(self):
        # Exercise production URL selection without contacting a real Release.
        version = '0.0.1'
        root = install.canonical(version)
        self.manifest.update(suite_version=version, suite_tag='suite-v' + version,
                             manifest_url=root + 'release-manifest.json', status='release')
        for name, record in self.manifest['skills'].items():
            old = self.assets / record['artifact']['file']
            files = release.zip_items(old.read_bytes())
            identity = json.loads(files['release.json'][0])
            identity.update(status='release', version=version, suite_version=version,
                            suite_tag='suite-v' + version, manifest_url=root + 'release-manifest.json')
            files['release.json'] = (release.encoded(identity), 0o644)
            data = release.zip_bytes(files)
            filename = name + ('-skill-' if name == 'linxsci-base' else '-') + version + '.zip'
            (self.assets / filename).write_bytes(data)
            record.update({k: v for k, v in identity.items() if k != 'files'})
            record['artifact'] = dict(release.artifact(filename, data, root.rstrip('/')), file_count=len(files))
        self.manifest['published'] = True
        self.save_manifest()
        requested = []
        def fixture_fetch(url, limit, timeout, test_http=False):
            self.assertFalse(test_http)
            install.validate_transport(url)
            requested.append(url)
            return (self.assets / url.rsplit('/', 1)[-1]).read_bytes()
        with patch.object(install, 'fetch', side_effect=fixture_fetch):
            result = self.run_install(assets_dir=None, manifest_url=self.manifest['manifest_url'],
                                      suite_version=self.manifest['suite_version'])
        self.assertEqual(result['status'], 'installed')
        root = install.canonical(self.manifest['suite_version'])
        self.assertEqual(requested, [root + 'release-manifest.json', root + 'SHA256SUMS',
                                     self.manifest['skills']['linxsci-survey']['artifact']['url']])

    def test_bad_remote_source_and_nonfixed_version_are_rejected(self):
        for url in ('https://example.invalid/release-manifest.json', 'https://github.com/LinxSci/linxsci-skills/releases/latest',
                    'https://user:password@github.com/LinxSci/linxsci-skills/releases/download/suite-v0.1.0/release-manifest.json'):
            with self.subTest(url=url), self.assertRaises(install.InstallError):
                self.run_install(assets_dir=None, manifest_url=url, suite_version='0.1.0')
        with self.assertRaises(install.InstallError):
            self.run_install(suite_version='latest')

    def test_http_404_timeout_interruption_redirect_leave_no_install(self):
        for mode in ('404', 'timeout', 'interrupted', 'redirect'):
            with self.subTest(mode=mode):
                server, options = self.http(mode)
                with self.assertRaises(install.InstallError):
                    self.run_install(**options, timeout=0.05)
                self.assertFalse(self.target.exists())
                self.assertGreaterEqual(len(server.requests), 1)

    def test_wrong_checksum_and_size(self):
        original = self.archive().read_bytes()
        for damaged in (original + b'corrupt', bytes([original[0] ^ 1]) + original[1:]):
            self.archive().write_bytes(damaged)
            with self.assertRaises(install.InstallError):
                self.run_install()
        self.assertFalse(self.target.exists())

    def test_corrupt_zip_with_matching_outer_hash(self):
        self.archive().write_bytes(b'not a ZIP')
        record = self.manifest['skills']['linxsci-survey']['artifact']
        record.update(size=9, sha256=install.digest(b'not a ZIP'))
        self.save_manifest()
        with self.assertRaisesRegex(install.InstallError, 'ZIP'):
            self.run_install()

    def test_package_inventory_and_identity_are_verified(self):
        self.change_zip(lambda files: files.__setitem__('SKILL.md', (b'changed identity', 0o644)))
        with self.assertRaisesRegex(install.InstallError, 'changed'):
            self.run_install()

    def test_metadata_version_mismatch(self):
        def mutate(files):
            value = json.loads(files['release.json'][0]); value['version'] = '9.9.9'
            files['release.json'] = (release.encoded(value), 0o644)
        self.change_zip(mutate)
        with self.assertRaisesRegex(install.InstallError, 'identity/version'):
            self.run_install()

    def test_manifest_identity_version_and_source_checks(self):
        original = copy.deepcopy(self.manifest)
        for field, value in [('suite_tag', 'latest'), ('manifest_url', 'https://example.invalid/manifest'), ('suite_version', '9.9.9')]:
            self.manifest = copy.deepcopy(original); self.manifest[field] = value; self.save_manifest()
            with self.subTest(field=field), self.assertRaises(install.InstallError):
                self.run_install()

    def test_malicious_paths_symlinks_duplicates_and_expansion_are_rejected(self):
        record = copy.deepcopy(self.manifest['skills']['linxsci-survey'])
        for filename, mode in [('../escape', stat.S_IFREG), ('C:/escape', stat.S_IFREG), ('a\\b', stat.S_IFREG),
                               ('/escape', stat.S_IFREG), ('link', stat.S_IFLNK), ('CON.txt', stat.S_IFREG),
                               ('.git/config', stat.S_IFREG), ('space. /x', stat.S_IFREG)]:
            raw = io.BytesIO()
            with zipfile.ZipFile(raw, 'w') as archive:
                info = zipfile.ZipInfo(filename); info.external_attr = (mode | 0o644) << 16
                archive.writestr(info, b'bad')
            data = raw.getvalue()
            record['artifact'].update(size=len(data), sha256=install.digest(data), file_count=1)
            with self.subTest(filename=filename), self.assertRaises(install.InstallError):
                install.unpack(data, record)
        for names in [('same', 'same'), ('same', 'SAME'), ('parent', 'parent/child')]:
            raw = io.BytesIO()
            with warnings.catch_warnings(), zipfile.ZipFile(raw, 'w') as archive:
                warnings.simplefilter('ignore', UserWarning)
                for name in names:
                    archive.writestr(name, b'bad')
            data = raw.getvalue()
            record['artifact'].update(size=len(data), sha256=install.digest(data), file_count=2)
            with self.subTest(names=names), self.assertRaisesRegex(install.InstallError, 'conflict'):
                install.unpack(data, record)
        real = self.manifest['skills']['linxsci-survey']
        with patch.object(install, 'MAX_EXPANDED', 1), self.assertRaisesRegex(install.InstallError, 'expanded size'):
            install.unpack(self.archive().read_bytes(), real)
        self.assertFalse((self.root / 'escape').exists())

    def test_malformed_metadata_and_receipts_are_rejected(self):
        self.manifest['skills']['linxsci-survey']['python_requirements'] = [None]
        self.save_manifest()
        with self.assertRaises(install.InstallError):
            self.run_install()
        self.assertFalse(self.target.exists())
        self.target.mkdir(parents=True)
        (self.target / install.RECEIPT).write_text('[]')
        with self.assertRaisesRegex(install.InstallError, 'receipt'):
            self.run_install(assets_dir=None)

    def test_existing_edits_extra_files_and_incomplete_directory_are_preserved(self):
        self.run_install()
        entry = self.target / 'scripts/survey.py'
        entry.write_bytes(entry.read_bytes() + b'\n# local edit\n')
        extra = self.target / 'my-note.txt'; extra.write_text('keep')
        with self.assertRaises(install.InstallError):
            self.run_install()
        self.assertIn(b'# local edit', entry.read_bytes())
        self.assertEqual(extra.read_text(), 'keep')
        shutil.rmtree(self.target)
        self.target.mkdir(); extra.write_text('incomplete but mine')
        with self.assertRaises(install.InstallError):
            self.run_install()
        self.assertEqual(extra.read_text(), 'incomplete but mine')

    def test_manual_verified_copy_can_be_reused(self):
        self.run_install()
        (self.target / install.RECEIPT).unlink()
        self.assertEqual(self.run_install()['status'], 'reused')
        self.assertFalse((self.target / install.RECEIPT).exists())

    def test_python_and_sdk_constraints_fail_without_changing_environment(self):
        with patch.object(install.sys, 'version_info', (3, 8)):
            with self.assertRaisesRegex(install.InstallError, 'Python'):
                self.run_install()
        with patch.object(install.importlib.metadata, 'version', return_value='0.3.3'):
            with self.assertRaisesRegex(install.InstallError, 'dependency mismatch'):
                self.run_install()
        self.assertFalse(self.target.parent.exists())

    def test_compatibility_failure_and_concurrent_target_are_preserved(self):
        with patch.object(install, 'validate_runtime', side_effect=install.InstallError('incompatible')):
            with self.assertRaises(install.InstallError):
                self.run_install()
        self.assertFalse(self.target.exists())
        original = install.validate_runtime
        def race(folder, record, timeout):
            original(folder, record, timeout)
            self.target.mkdir()
            (self.target / 'other-writer.txt').write_text('keep')
        with patch.object(install, 'validate_runtime', side_effect=race):
            with self.assertRaises(FileExistsError):
                self.run_install()
        self.assertEqual((self.target / 'other-writer.txt').read_text(), 'keep')
        self.assertEqual(list(self.target.parent.glob('.linxsci-package-*')), [])

    def test_failed_publish_rolls_back_own_reservation(self):
        with patch.object(install, 'WINDOWS', False), \
                patch.object(Path, 'rename', side_effect=OSError('simulated disk failure')):
            with self.assertRaises(OSError):
                self.run_install()
        self.assertFalse(self.target.exists())
        self.assertEqual(list(self.target.parent.glob('.linxsci-package-*')), [])

    def test_windows_install_and_reuse_without_rename(self):
        with patch.object(install, 'WINDOWS', True), \
                patch.object(Path, 'rename', side_effect=AssertionError('Windows must copy files')):
            self.assertEqual(self.run_install()['status'], 'installed')
            self.assertEqual(self.run_install(assets_dir=None)['status'], 'reused')
        self.assertTrue((self.target / install.RECEIPT).is_file())

    def test_inconsistent_publication_state_is_rejected(self):
        for status, published in (('candidate', True), ('release', False), ('unknown', False)):
            with self.subTest(status=status, published=published):
                manifest = copy.deepcopy(self.manifest)
                manifest.update(status=status, published=published)
                with self.assertRaisesRegex(install.InstallError, 'publication state'):
                    install.validate_manifest(manifest)

    def test_windows_partial_copy_failure_rolls_back(self):
        original = Path.open
        count = [0]
        def fail(path, *args, **kwargs):
            if args and args[0] == 'xb':
                count[0] += 1
                if count[0] == 3:
                    raise OSError('simulated partial write')
            return original(path, *args, **kwargs)
        with patch.object(install, 'WINDOWS', True), patch.object(Path, 'open', fail):
            with self.assertRaises(OSError):
                self.run_install()
        self.assertFalse(self.target.exists())


if __name__ == '__main__':
    unittest.main()
