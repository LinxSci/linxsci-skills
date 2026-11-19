"""Exercise immutable Git inputs, deterministic artifacts and corrupted candidates."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import skill_release as release
import publish_skill_releases as publication


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = tempfile.TemporaryDirectory(prefix='linxsci-release-fixture-')
        cls.fixture_root = Path(cls.fixture.name)
        cls.recipe_template = json.loads((release.ROOT / 'release/suite.json').read_text())
        cls.license_text = (release.ROOT / 'LICENSE').read_text()
        cls.commits = {}
        for name in release.NAMES:
            repo = cls.fixture_root / name
            repo.mkdir()
            cls.git(repo, 'init', '--quiet')
            root = repo / 'skills/linxsci-base' if name == 'linxsci-base' else repo
            files = {
                'LICENSE': cls.license_text,
                'SKILL.md': '---\nname: ' + name + '\n---\n[Guide](references/guide.md)\n',
                'references/guide.md': '# Guide\n[Instructions](../SKILL.md)\n',
                cls.recipe_template['skills'][name]['entrypoint']: 'print("fixture help")\n',
                '__init__.py': '__version__ = "0.3.4"\n',
                'tests/test_example.py': '# Source only\n',
                '.env': 'PRIVATE_FIXTURE_TOKEN=secret\n',
                'docs/local/private.md': 'Private fixture note\n',
            }
            if name != 'linxsci-base':
                files['requirements.txt'] = 'linxsci==0.3.4\n'
            for filename, content in files.items():
                path = root / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            if name == 'linxsci-base':
                (repo / 'LICENSE').write_text(cls.license_text)
                (repo / 'pyproject.toml').write_text('[project]\nname = "linxsci"\nversion = "0.3.4"\n')
                (repo / 'README.md').write_text('[Base](skills/linxsci-base/SKILL.md)\n')
            cls.git(repo, 'add', '.')
            cls.git(repo, 'commit', '--quiet', '-m', 'Pinned fixture')
            cls.commits[name] = cls.git(repo, 'rev-parse', 'HEAD').strip()
        # A moved branch must never change the content selected by the old lock.
        idea = cls.fixture_root / 'linxsci-idea'
        (idea / 'references/guide.md').write_text('Newer branch content, deliberately not pinned.\n')
        cls.git(idea, 'add', '.')
        cls.git(idea, 'commit', '--quiet', '-m', 'Unselected newer commit')

    @classmethod
    def tearDownClass(cls):
        cls.fixture.cleanup()

    @staticmethod
    def git(repo, *args):
        return subprocess.check_output(['git', '-C', str(repo), '-c', 'user.name=Release Test',
            '-c', 'user.email=release-test@example.invalid', '-c', 'commit.gpgsign=false', *args],
            stderr=subprocess.PIPE, text=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='linxsci-release-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(self.fixture_root, self.root / 'repos')
        self.sources = {name: str(self.root / 'repos' / name) for name in release.NAMES}
        self.recipe = copy.deepcopy(self.recipe_template)
        self.lock = {'schema_version': 1, 'extensions': [
            {'name': name, 'path': 'skills/' + name, 'branch': 'descriptive-only',
             'commit': self.commits[name]} for name in release.NAMES[1:]]}
        self.wheel_files = {
            'linxsci/__init__.py': (b'__version__ = "0.3.4"\n', 0o644),
            'linxsci/scripts/cli.py': (b'print("fixture help")\n', 0o644),
            'linxsci-0.3.4.dist-info/METADATA': (b'Metadata-Version: 2.1\nName: linxsci\nVersion: 0.3.4\n', 0o644),
        }
        self.wheel = self.root / self.recipe['sdk']['file']
        self.write_wheel()
        self.output = self.root / 'candidate'

    def write_wheel(self):
        self.wheel.write_bytes(release.zip_bytes(self.wheel_files))
        self.recipe['sdk']['sha256'] = release.sha256(self.wheel.read_bytes())

    def build(self, output=None, *, release_mode=False):
        for filename, value in [('lock.json', self.lock), ('recipe.json', self.recipe), ('sources.json', self.sources)]:
            (self.root / filename).write_bytes(release.encoded(value))
        with contextlib.redirect_stdout(io.StringIO()):
            return release.build(self.root / 'lock.json', self.root / 'recipe.json',
                self.root / 'sources.json', self.commits['linxsci-base'], self.wheel, output or self.output,
                release_mode=release_mode)

    def refresh_sums(self):
        (self.output / 'SHA256SUMS').write_text(''.join(
            release.sha256(path.read_bytes()) + '  ' + path.name + '\n'
            for path in sorted(self.output.iterdir()) if path.name != 'SHA256SUMS'))

    def test_build_is_repeatable_pinned_and_preserves_sources(self):
        before = {name: (Path(source, '.git/index').read_bytes(),
                        self.git(source, 'rev-parse', 'HEAD')) for name, source in self.sources.items()}
        manifest = self.build()
        second = self.root / 'second'
        self.build(second)
        self.assertEqual({p.name: p.read_bytes() for p in self.output.iterdir()},
                         {p.name: p.read_bytes() for p in second.iterdir()})
        self.assertEqual(release.check(self.output)['assets'], 14)
        for name, source in self.sources.items():
            self.assertEqual(before[name], (Path(source, '.git/index').read_bytes(),
                                           self.git(source, 'rev-parse', 'HEAD')))
        idea = release.zip_items((self.output / manifest['skills']['linxsci-idea']['artifact']['file']).read_bytes())
        self.assertIn(b'# Guide', idea['references/guide.md'][0])
        self.assertNotIn('tests/test_example.py', idea)
        self.assertIn('SKILL.md', idea)
        source = release.zip_items((self.output / manifest['bundles']['source']).read_bytes())
        self.assertTrue(any(name.endswith('/linxsci-idea/tests/test_example.py') for name in source))
        self.assertFalse(any('.env' in name or '/docs/local/' in name or '/.git/' in name for name in source))
        self.assertEqual(manifest['skills']['linxsci-idea']['skill_dependencies'][0],
                         {'name': 'linxsci-survey', 'kind': 'feature', 'when': 'fresh-evidence'})
        shared = (release.ROOT / 'tools/skill_install.py').read_bytes()
        self.assertEqual(idea[release.INSTALLER_PATH][0], shared)
        self.assertEqual(manifest['skills']['linxsci-idea']['generated_files'], {
            release.INSTALLER_PATH: {'build_input': release.INSTALLER_INPUT, 'sha256': release.sha256(shared)}})
        extracted = self.root / 'standalone-idea'
        extracted.mkdir()
        for name, (data, mode) in idea.items():
            target = extracted / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        helped = subprocess.run([sys.executable, '-B', '-I', str(extracted / release.INSTALLER_PATH), '--help'],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(helped.returncode, 0, helped.stderr)
        self.assertIn('--manifest-url', helped.stdout)

    def test_source_cannot_shadow_generated_installer(self):
        repo = Path(self.sources['linxsci-idea'])
        (repo / release.INSTALLER_PATH).write_text('# conflicting source\n')
        self.git(repo, 'add', '.')
        self.git(repo, 'commit', '--quiet', '-m', 'Conflicting installer fixture')
        row = next(r for r in self.lock['extensions'] if r['name'] == 'linxsci-idea')
        row['commit'] = self.git(repo, 'rev-parse', 'HEAD').strip()
        with self.assertRaisesRegex(release.ReleaseError, 'conflicts with source'):
            self.build()

    def test_license_travels_with_every_distribution_without_rewriting_sdk(self):
        manifest = self.build()
        notice = self.license_text.encode()
        self.assertEqual((self.output / 'LICENSE').read_bytes(), notice)
        self.assertEqual(manifest['license']['artifact']['sha256'], release.sha256(notice))
        self.assertEqual((self.output / self.wheel.name).read_bytes(), self.wheel.read_bytes())
        for name, record in manifest['skills'].items():
            files = release.zip_items((self.output / record['artifact']['file']).read_bytes())
            with self.subTest(skill=name):
                self.assertEqual(files['LICENSE'][0], notice)
                self.assertEqual(record['license'], {'spdx': 'MIT', 'file': 'LICENSE'})
                self.assertIn(b'[MIT License](LICENSE)', files['PACKAGE.md'][0])
        full = release.zip_items((self.output / manifest['bundles']['full']).read_bytes())
        source = release.zip_items((self.output / manifest['bundles']['source']).read_bytes())
        prefix = 'linxsci-skills-' + manifest['suite_version'] + '-source/'
        self.assertEqual(full['LICENSE'][0], notice)
        self.assertEqual(source[prefix + 'LICENSE'][0], notice)
        for name in release.NAMES:
            self.assertEqual(source[prefix + 'skills/' + name + '/LICENSE'][0], notice)

    def test_missing_or_different_skill_license_rejects_fixed_source(self):
        repo = Path(self.sources['linxsci-idea'])
        row = next(r for r in self.lock['extensions'] if r['name'] == 'linxsci-idea')
        for notice in (None, 'Different terms\n'):
            if notice is None:
                (repo / 'LICENSE').unlink()
            else:
                (repo / 'LICENSE').write_text(notice)
            self.git(repo, 'add', '-A')
            self.git(repo, 'commit', '--quiet', '-m', 'Invalid license fixture')
            row['commit'] = self.git(repo, 'rev-parse', 'HEAD').strip()
            with self.subTest(notice=notice), self.assertRaisesRegex(release.ReleaseError, 'Skill LICENSE'):
                self.build()
            self.assertFalse(self.output.exists())

    def test_license_artifact_cannot_be_replaced_with_only_new_checksums(self):
        self.build()
        (self.output / 'LICENSE').write_text(self.license_text + '\nChanged terms\n')
        self.refresh_sums()
        with self.assertRaisesRegex(release.ReleaseError, 'License artifact mismatch'):
            release.check(self.output)

    def test_final_build_requires_license(self):
        self.recipe.update(status='release', suite_version='0.0.1')
        self.recipe.pop('license')
        with self.assertRaisesRegex(release.ReleaseError, 'explicit license'):
            self.build(release_mode=True)
        self.assertFalse(self.output.exists())

    def test_legacy_candidate_without_license_metadata_remains_checkable(self):
        self.recipe.pop('license')
        self.build()
        self.assertEqual(release.check(self.output)['assets'], 13)

    def test_final_assets_have_consistent_state_and_are_reproducible(self):
        self.recipe.update(status='release', suite_version='0.0.1')
        manifest = self.build(release_mode=True)
        checked = release.check(self.output)
        self.assertEqual((checked['status'], checked['published']), ('release', True))
        for name, record in manifest['skills'].items():
            self.assertEqual(record['status'], 'release')
            files = release.zip_items((self.output / record['artifact']['file']).read_bytes())
            self.assertEqual(json.loads(files['release.json'][0])['status'], 'release')
        second = self.root / 'final-repeat'
        self.build(second, release_mode=True)
        self.assertEqual({p.name: p.read_bytes() for p in self.output.iterdir()},
                         {p.name: p.read_bytes() for p in second.iterdir()})

    def test_final_mode_requires_matching_recipe_and_stable_version(self):
        with self.assertRaisesRegex(release.ReleaseError, 'candidate recipe'):
            self.build(release_mode=True)
        self.recipe.update(status='release', suite_version='0.0.1')
        with self.assertRaisesRegex(release.ReleaseError, 'requires --release'):
            self.build()
        self.recipe['suite_version'] = '0.0.1-rc.1'
        with self.assertRaisesRegex(release.ReleaseError, 'stable suite version'):
            self.build(release_mode=True)
        self.assertFalse(self.output.exists())

    def test_manifest_state_cannot_be_changed_without_repacking(self):
        manifest = self.build()
        for status, published in (('candidate', True), ('release', False), ('unknown', False)):
            value = dict(manifest, status=status, published=published)
            (self.output / 'release-manifest.json').write_bytes(release.encoded(value))
            self.refresh_sums()
            with self.subTest(status=status), self.assertRaisesRegex(release.ReleaseError, 'publication state'):
                release.check(self.output)
        # Even a valid outer state cannot replace the package and embedded identities.
        value = dict(manifest, status='release', published=True)
        (self.output / 'release-manifest.json').write_bytes(release.encoded(value))
        self.refresh_sums()
        with self.assertRaises(release.ReleaseError):
            release.check(self.output)

    def publication_fixture(self):
        self.recipe.update(status='release', suite_version='0.0.1')
        self.build(release_mode=True)
        # This synthetic report tests the publication gate; it is not real acceptance evidence.
        report = dict(schema_version=1, passed=True, skips=0, suite_version='0.0.1', status='release',
                      idea_from_single_zip=True, git_available=False,
                      smoke_checks=35,
                      assets_sha256={p.name: release.sha256(p.read_bytes()) for p in self.output.iterdir()},
                      manifest_sha256=release.sha256((self.output / 'release-manifest.json').read_bytes()),
                      checks=[{'check': name, 'exit': 0} for name in publication.REQUIRED_CHECKS])
        path = self.root / 'synthetic-report.json'
        path.write_bytes(release.encoded(report))
        notes = self.root / 'notes.md'
        notes.write_text('# Local publication test fixture\n', encoding='utf-8')
        return path, notes

    def test_publication_plan_is_offline_and_rejects_stale_or_incomplete_reports(self):
        report, notes = self.publication_fixture()
        with patch.object(publication, 'run_gh', side_effect=AssertionError('Unexpected network')):
            value = publication.plan(self.output, report, notes)
        self.assertFalse(value['uploaded'])
        self.assertIn('--draft', value['upload_draft_argv'])
        self.assertIn('--latest=false', value['publish_argv'])
        original = json.loads(report.read_bytes())
        for update in ({'manifest_sha256': '0' * 64}, {'assets_sha256': {}}, {'smoke_checks': 0},
                       {'skips': 1}, {'checks': []}, {'passed': False}):
            report.write_bytes(release.encoded(dict(original, **update)))
            with self.subTest(update=update), self.assertRaises(release.ReleaseError):
                publication.plan(self.output, report, notes)

    def test_publication_checks_tag_and_never_modifies_a_published_release(self):
        report, notes = self.publication_fixture()
        value = publication.plan(self.output, report, notes)
        with patch.object(publication, 'run_gh', return_value='f' * 40) as gh:
            with self.assertRaisesRegex(release.ReleaseError, 'tag does not resolve'):
                publication.execute(value, 'publish')
            self.assertEqual(gh.call_count, 1)
        with patch.object(publication, 'run_gh', side_effect=[value['base_commit'], json.dumps({
                'tagName': value['tag'], 'isDraft': False, 'assets': []})]) as gh:
            with self.assertRaisesRegex(release.ReleaseError, 'Published releases are never modified'):
                publication.execute(value, 'publish')
            self.assertEqual(gh.call_count, 2)

    def test_publication_downloads_and_checks_remote_bytes_before_publish(self):
        report, notes = self.publication_fixture()
        value = publication.plan(self.output, report, notes)
        calls = []
        corrupt = [True]
        def gh(args):
            calls.append(args)
            if args[1] == 'api':
                return value['base_commit']
            if args[1:3] == ['release', 'view']:
                return json.dumps({'tagName': value['tag'], 'isDraft': True,
                                   'assets': [{'name': n} for n in value['files']]})
            if args[1:3] == ['release', 'download']:
                root = Path(args[args.index('--dir') + 1])
                for source in self.output.iterdir():
                    shutil.copy2(source, root / source.name)
                if corrupt[0]:
                    (root / 'SHA256SUMS').write_bytes(b'wrong remote bytes')
            return ''
        with patch.object(publication, 'run_gh', side_effect=gh):
            with self.assertRaisesRegex(release.ReleaseError, 'bytes differ'):
                publication.execute(value, 'publish')
            self.assertFalse(any(a[1:3] == ['release', 'edit'] for a in calls))
            calls.clear()
            corrupt[0] = False
            done = publication.execute(value, 'publish')
        self.assertFalse(done['draft'])
        self.assertFalse(done['public_download_verified'])
        self.assertEqual(calls[-1], value['publish_argv'])

    def test_dirty_source_rejected_without_touching_index(self):
        repo = Path(self.sources['linxsci-idea'])
        index = (repo / '.git/index').read_bytes()
        (repo / 'uncommitted.txt').write_text('Keep me')
        with self.assertRaisesRegex(release.ReleaseError, 'uncommitted'):
            self.build()
        self.assertEqual(index, (repo / '.git/index').read_bytes())
        self.assertEqual((repo / 'uncommitted.txt').read_text(), 'Keep me')
        self.assertFalse(self.output.exists())

    def test_file_url_does_not_bypass_dirty_check(self):
        repo = Path(self.sources['linxsci-base'])
        relocated = self.root / 'base source % encoded'
        repo.rename(relocated)
        repo = relocated
        index = (repo / '.git/index').read_bytes()
        (repo / 'uncommitted.txt').write_text('Keep me')
        self.sources['linxsci-base'] = repo.as_uri()
        with self.assertRaisesRegex(release.ReleaseError, 'uncommitted'):
            self.build()
        self.assertEqual(index, (repo / '.git/index').read_bytes())
        self.assertEqual((repo / 'uncommitted.txt').read_text(), 'Keep me')
        self.assertFalse(self.output.exists())

    def test_clean_file_url_with_escaped_path_fetches_fixed_commit(self):
        repo = Path(self.sources['linxsci-base'])
        relocated = self.root / 'base source % encoded'
        repo.rename(relocated)
        files = release.fetch_tree(relocated.as_uri(), self.commits['linxsci-base'],
                                   self.root / 'clean-file-url-checkout')
        self.assertEqual(files['LICENSE'][0], self.license_text.encode())
        self.assertEqual(files['skills/linxsci-base/scripts/cli.py'][0], b'print("fixture help")\n')

    def test_checkout_line_endings_do_not_change_git_blob_inputs(self):
        git = release.git

        def autocrlf(repo, *args, **kwargs):
            return git(repo, '-c', 'core.autocrlf=true', *args, **kwargs)

        checkout = self.root / 'crlf-checkout'
        with patch.object(release, 'git', side_effect=autocrlf):
            files = release.fetch_tree(self.sources['linxsci-base'], self.commits['linxsci-base'], checkout)
        path = 'skills/linxsci-base/scripts/cli.py'
        self.assertEqual(files[path][0], b'print("fixture help")\n')
        self.assertIn(b'\r\n', (checkout / path).read_bytes())

    def test_unavailable_commit_leaves_no_candidate(self):
        self.lock['extensions'][0]['commit'] = '0' * 40
        with self.assertRaisesRegex(release.ReleaseError, 'commit is unavailable'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_ref_name_is_not_a_commit_pin(self):
        self.lock['extensions'][0]['commit'] = 'main'
        with self.assertRaisesRegex(release.ReleaseError, 'SHA'):
            self.build()

    def test_existing_output_is_never_overwritten(self):
        self.output.mkdir()
        sentinel = self.output / 'keep.txt'
        sentinel.write_bytes(b'existing candidate')
        with self.assertRaisesRegex(release.ReleaseError, 'already exists'):
            self.build()
        self.assertEqual(sentinel.read_bytes(), b'existing candidate')

    def test_wrong_wheel_checksum_fails_before_fetch(self):
        self.wheel.write_bytes(b'wrong wheel')
        with self.assertRaisesRegex(release.ReleaseError, 'checksum'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_wheel_must_match_pinned_sdk_source(self):
        self.wheel_files['linxsci/scripts/cli.py'] = (b'print("changed SDK")\n', 0o644)
        self.write_wheel()
        with self.assertRaisesRegex(release.ReleaseError, 'pinned base source'):
            self.build()

    def test_wheel_metadata_version_is_checked(self):
        self.wheel_files['linxsci-0.3.4.dist-info/METADATA'] = (b'Name: linxsci\nVersion: 9.9.9\n', 0o644)
        self.write_wheel()
        with self.assertRaisesRegex(release.ReleaseError, 'version'):
            self.build()

    def test_private_source_address_is_not_distributed(self):
        repo = Path(self.sources['linxsci-idea'])
        (repo / 'references/private.md').write_text(self.sources['linxsci-survey'])
        self.git(repo, 'add', '.')
        self.git(repo, 'commit', '--quiet', '-m', 'Private contamination fixture')
        self.lock['extensions'][0]['commit'] = self.git(repo, 'rev-parse', 'HEAD').strip()
        with self.assertRaisesRegex(release.ReleaseError, 'Private source data'):
            self.build()
        self.assertFalse(self.output.exists())

    def test_unsafe_and_conflicting_zip_members_are_rejected(self):
        cases = [('.. /bad', '../escape'), ('absolute', '/escape'), ('drive', 'C:/escape'),
                 ('backslash', 'a\\escape'), ('control', 'a\nfile'), ('nested-private', 'snapshot/docs/local/secret')]
        for label, path in cases:
            with self.subTest(label=label), self.assertRaises(release.ReleaseError):
                release.zip_bytes({path: (b'x', 0o644)})
        for paths in [('A.md', 'a.md'), ('path', 'path/child')]:
            with self.subTest(paths=paths), self.assertRaises(release.ReleaseError):
                release.zip_bytes({p: (b'x', 0o644) for p in paths})
        for mode in (stat.S_IFLNK, stat.S_IFIFO):
            output = io.BytesIO()
            with zipfile.ZipFile(output, 'w') as archive:
                entry = zipfile.ZipInfo('link')
                entry.create_system = 3
                entry.external_attr = (mode | 0o777) << 16
                archive.writestr(entry, b'target')
            with self.assertRaises(release.ReleaseError):
                release.zip_items(output.getvalue())
        output = io.BytesIO()
        with warnings.catch_warnings(), zipfile.ZipFile(output, 'w') as archive:
            warnings.simplefilter('ignore', UserWarning)
            archive.writestr('same', b'first')
            archive.writestr('same', b'second')
        with self.assertRaisesRegex(release.ReleaseError, 'Duplicate'):
            release.zip_items(output.getvalue())

    def test_missing_relative_resource_is_rejected(self):
        with self.assertRaisesRegex(release.ReleaseError, 'Broken relative link'):
            release.markdown_links({'SKILL.md': (b'[Required](references/missing.md)', 0o644)})

    def test_changed_single_zip_is_rejected(self):
        manifest = self.build()
        target = self.output / manifest['skills']['linxsci-idea']['artifact']['file']
        target.write_bytes(target.read_bytes() + b'tampered')
        with self.assertRaisesRegex(release.ReleaseError, 'Checksum mismatch'):
            release.check(self.output)
        self.refresh_sums()
        with self.assertRaisesRegex(release.ReleaseError, 'hash/size mismatch'):
            release.check(self.output)

    def test_full_and_source_must_match_singles_even_with_new_checksums(self):
        manifest = self.build()
        for kind, pattern, error in [('full', 'skills/linxsci-idea/references/guide.md', 'Expanded Skill'),
                                      ('source', '/skills/linxsci-idea/references/guide.md', 'Source snapshot differs')]:
            path = self.output / manifest['bundles'][kind]
            original = path.read_bytes()
            files = release.zip_items(original)
            key = next(key for key in files if key.endswith(pattern))
            files[key] = (b'Changed content\n', 0o644)
            path.write_bytes(release.zip_bytes(files))
            self.refresh_sums()
            with self.assertRaisesRegex(release.ReleaseError, error):
                release.check(self.output)
            path.write_bytes(original)
            self.refresh_sums()


if __name__ == '__main__':
    unittest.main()
