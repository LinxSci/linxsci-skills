#!/usr/bin/env python3
"""Verify release contents, checksums, versions and package metadata."""
import hashlib
import configparser
import fnmatch
import posixpath
import re
import subprocess
import sys
import tarfile
import zipfile
from email.parser import BytesParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_public_paths(names):
    """Check all artifact formats, since Git ignores do not filter packages."""
    patterns = (
        '.env', '.env.*', '*.local.*', '*.log', '*.py[cod]', '.DS_Store', '._*',
        'Thumbs.db', 'Desktop.ini', '.linxsci-install.json', '.linxsci-stage-*',
        '*.swp', '*.swo', '*~', '.venv', '.venv-*', '.coverage', '.coverage.*',
        'test-results.txt', 'release-check.txt', 'release-smoke.txt',
    )
    private_dirs = {
        '.local', '.agents', '.codex', '.claude', '.idea', '.vscode', '__pycache__',
        '.pytest_cache', '.mypy_cache', '.ruff_cache', '.tox', '.nox', 'htmlcov',
        'linxsci-skill-backups', 'smoke',
    }
    for name in names:
        parts = name.split('/')
        assert not private_dirs.intersection(parts), 'Local directory in release: ' + name
        assert '/docs/local/' not in '/' + name + '/', 'Local notes in release: ' + name
        for part in parts:
            if part == '.env.example':
                continue
            assert not any(fnmatch.fnmatchcase(part, pattern) for pattern in patterns), 'Local file in release: ' + name


def check(directory):
    metadata = (ROOT / 'pyproject.toml').read_text(encoding='utf-8')
    version = re.search(r'^version = "([^"]+)"', metadata, re.MULTILINE).group(1)
    for file, pattern in (
        ('skills/linxsci-base/__init__.py', r'__version__ = "([^"]+)"'),
        ('skills/linxsci-base/scripts/commands.py', r'VERSION = "([^"]+)"'),
        ('skills/linxsci-base/scripts/installer.py', r'"version": "([^"]+)"'),
    ):
        assert re.search(pattern, (ROOT / file).read_text(encoding='utf-8')).group(1) == version, 'Version mismatch: ' + file
    expected = {
        'SKILL.md', 'SKILL.zh-CN.md', 'references/api.zh-CN.md', 'references/cli.zh-CN.md', 'service.json', 'agents/openai.yaml', 'references/api.md', 'references/cli.md',
        '__init__.py', 'scripts/__init__.py', 'scripts/commands.py',
        'scripts/client.py', 'scripts/config.py', 'scripts/installer.py',
        'scripts/cli.py', 'scripts/output.py', 'scripts/skill_dispatch.py',
    }
    wheel = directory / ('linxsci-' + version + '-py3-none-any.whl')
    sdist = directory / ('linxsci-' + version + '.tar.gz')
    bundle = directory / ('linxsci-base-' + version + '.zip')
    with zipfile.ZipFile(wheel) as archive:
        assert archive.testzip() is None
        check_public_paths(archive.namelist())
        assert {'linxsci/' + name for name in expected} == {
            name for name in archive.namelist() if name.startswith('linxsci/')
        }, 'Unexpected or missing wheel Skill files'
        for name in expected:
            assert archive.read('linxsci/' + name) == (ROOT / 'skills/linxsci-base' / name).read_bytes(), 'Stale packaged file: ' + name
        pkg_metadata = BytesParser().parsebytes(archive.read('linxsci-' + version + '.dist-info/METADATA'))
        assert not pkg_metadata.get_all('Requires-Dist'), 'Runtime dependencies are expected to be empty'
        assert pkg_metadata['Version'] == version
        assert pkg_metadata['Name'] == 'linxsci'
        entries = configparser.ConfigParser()
        entries.read_string(archive.read('linxsci-' + version + '.dist-info/entry_points.txt').decode())
        assert entries['console_scripts']['linxsci'] == 'linxsci.scripts.cli:main'
        assert set(entries['console_scripts']) == {'linxsci'}, 'Unexpected console entry point'
    with tarfile.open(sdist) as archive:
        source_names = archive.getnames()
        check_public_paths(source_names)
        for name in expected:
            assert any(path.endswith('/skills/linxsci-base/' + name) for path in source_names), 'Missing source Skill file: ' + name
        assert not any('/skills/linxsci-skills/' in name for name in source_names), 'Old Skill directory in source archive'
        assert any(name.endswith('/tools/build_release.py') for name in source_names)
        for name in ('RELEASING.md', 'RELEASING.zh-CN.md', 'TESTING.md', 'TESTING.zh-CN.md'):
            assert any(path.endswith('/docs/' + name) for path in source_names), 'Missing maintainer guide: ' + name
        assert not any('/WEBSITE_PUBLISHING' in name for name in source_names), 'Obsolete website plan in source archive'
    with zipfile.ZipFile(bundle) as archive:
        assert archive.testzip() is None
        prefix = 'linxsci-base-' + version + '/'
        names = set(archive.namelist())
        check_public_paths(names)
        expected_bundle = {prefix + 'skills/linxsci-base/' + name for name in expected}
        expected_bundle.update(prefix + name for name in (
            'install.py', 'Install.command', 'Install.bat', 'README.md', 'README.zh-CN.md',
        ))
        assert names == expected_bundle, 'Unexpected or missing standalone bundle files'
        assert not any(name.startswith(prefix + 'docs/') for name in names), 'Skill ZIP must not include CLI/SDK or maintainer guides'
        for language in ('', '.zh-CN'):
            guide = (ROOT / ('docs/USER_GUIDE' + language + '.md')).read_text(encoding='utf-8')
            guide = guide.replace('(USER_GUIDE.md)', '(README.md)').replace(
                '(USER_GUIDE.zh-CN.md)', '(README.zh-CN.md)')
            assert archive.read(prefix + 'README' + language + '.md').decode('utf-8') == guide, 'Stale bundled Skill guide'
        for name in expected:
            assert archive.read(prefix + 'skills/linxsci-base/' + name) == (ROOT / 'skills/linxsci-base' / name).read_bytes(), 'Stale bundled Skill file: ' + name
        # Links must work after extraction without maintainer docs from the repository.
        for name in sorted(names):
            if not name.endswith('.md'):
                continue
            document = archive.read(name).decode('utf-8')
            for target in re.findall(r'\]\(([^)]+)\)', document):
                if '://' in target or target.startswith(('#', 'mailto:')):
                    continue
                target_path = target.split('#', 1)[0]
                resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), target_path))
                assert resolved in names, 'Broken bundled link: ' + name + ' -> ' + target
        mode = archive.getinfo(prefix + 'Install.command').external_attr >> 16
        assert mode & 0o111, 'macOS launcher must be executable'
        assert not any('/.env' in name or '/config.json' in name or '/__pycache__/' in name
                       or '.linxsci-install.json' in name for name in archive.namelist())
    for line in (directory / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert Path(name).name == name
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest
    subprocess.run([sys.executable, '-m', 'twine', 'check', str(wheel), str(sdist)], check=True)
    print('Release files, packaged Skill, version consistency and checksums passed.')


if __name__ == '__main__':
    check(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'dist'))
