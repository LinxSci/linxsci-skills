#!/usr/bin/env python3
"""Verify release contents, checksums, versions and package metadata."""
import hashlib
import configparser
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(directory):
    metadata = (ROOT / 'pyproject.toml').read_text(encoding='utf-8')
    version = re.search(r'^version = "([^"]+)"', metadata, re.MULTILINE).group(1)
    for file, pattern in (
        ('skills/linxsci-skills/__init__.py', r'__version__ = "([^"]+)"'),
        ('skills/linxsci-skills/scripts/scholar.py', r'VERSION = "([^"]+)"'),
        ('skills/linxsci-skills/scripts/scholar_install.py', r'"version": "([^"]+)"'),
    ):
        assert re.search(pattern, (ROOT / file).read_text()).group(1) == version, 'Version mismatch: ' + file
    expected = {
        'SKILL.md', 'service.json', 'agents/openai.yaml', 'references/api.md', 'references/cli.md',
        '__init__.py', 'scripts/__init__.py', 'scripts/scholar.py',
        'scripts/scholar_client.py', 'scripts/scholar_config.py', 'scripts/scholar_install.py',
        'scripts/cli.py',
    }
    wheel = directory / ('linxsci_sdk-' + version + '-py3-none-any.whl')
    sdist = directory / ('linxsci_sdk-' + version + '.tar.gz')
    bundle = directory / ('linxsci-skills-' + version + '.zip')
    with zipfile.ZipFile(wheel) as archive:
        assert archive.testzip() is None
        assert {'linxsci/' + name for name in expected} <= set(archive.namelist())
        assert not any(name.startswith('linxsci_scholar/') for name in archive.namelist()), 'Old SDK module included'
        for name in expected:
            assert archive.read('linxsci/' + name) == (ROOT / 'skills/linxsci-skills' / name).read_bytes(), 'Stale packaged file: ' + name
        pkg_metadata = archive.read('linxsci_sdk-' + version + '.dist-info/METADATA').decode()
        assert 'Requires-Dist:' not in pkg_metadata, 'Runtime dependencies are expected to be empty'
        assert 'Version: ' + version in pkg_metadata
        assert 'Name: linxsci-sdk\n' in pkg_metadata
        entries = configparser.ConfigParser()
        entries.read_string(archive.read('linxsci_sdk-' + version + '.dist-info/entry_points.txt').decode())
        assert entries['console_scripts']['linxsci'] == 'linxsci.scripts.cli:main'
        assert set(entries['console_scripts']) == {'linxsci'}, 'Unexpected console entry point'
    with tarfile.open(sdist) as archive:
        assert any(name.endswith('/tools/build_release.py') for name in archive.getnames())
    with zipfile.ZipFile(bundle) as archive:
        assert archive.testzip() is None
        prefix = 'linxsci-skills-' + version + '/'
        assert {prefix + 'skills/linxsci-skills/' + name for name in expected} <= set(archive.namelist())
        assert prefix + 'install.py' in archive.namelist()
        assert prefix + 'docs/USER_GUIDE.md' in archive.namelist()
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
