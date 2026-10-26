#!/usr/bin/env python3
"""Verify release contents, checksums, versions and package metadata."""
import hashlib
import configparser
import posixpath
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
        ('skills/linxsci-skills/scripts/commands.py', r'VERSION = "([^"]+)"'),
        ('skills/linxsci-skills/scripts/installer.py', r'"version": "([^"]+)"'),
    ):
        assert re.search(pattern, (ROOT / file).read_text(encoding='utf-8')).group(1) == version, 'Version mismatch: ' + file
    expected = {
        'SKILL.md', 'SKILL.zh-CN.md', 'references/api.zh-CN.md', 'references/cli.zh-CN.md', 'service.json', 'agents/openai.yaml', 'references/api.md', 'references/cli.md',
        '__init__.py', 'scripts/__init__.py', 'scripts/commands.py',
        'scripts/client.py', 'scripts/config.py', 'scripts/installer.py',
        'scripts/cli.py', 'scripts/output.py',
    }
    wheel = directory / ('linxsci-' + version + '-py3-none-any.whl')
    sdist = directory / ('linxsci-' + version + '.tar.gz')
    bundle = directory / ('linxsci-skills-' + version + '.zip')
    with zipfile.ZipFile(wheel) as archive:
        assert archive.testzip() is None
        assert {'linxsci/' + name for name in expected} <= set(archive.namelist())
        for name in expected:
            assert archive.read('linxsci/' + name) == (ROOT / 'skills/linxsci-skills' / name).read_bytes(), 'Stale packaged file: ' + name
        pkg_metadata = archive.read('linxsci-' + version + '.dist-info/METADATA').decode()
        assert 'Requires-Dist:' not in pkg_metadata, 'Runtime dependencies are expected to be empty'
        assert 'Version: ' + version in pkg_metadata
        assert 'Name: linxsci\n' in pkg_metadata
        entries = configparser.ConfigParser()
        entries.read_string(archive.read('linxsci-' + version + '.dist-info/entry_points.txt').decode())
        assert entries['console_scripts']['linxsci'] == 'linxsci.scripts.cli:main'
        assert set(entries['console_scripts']) == {'linxsci'}, 'Unexpected console entry point'
    with tarfile.open(sdist) as archive:
        source_names = archive.getnames()
        assert any(name.endswith('/tools/build_release.py') for name in source_names)
        for name in ('RELEASING.md', 'RELEASING.zh-CN.md', 'TESTING.md', 'TESTING.zh-CN.md'):
            assert any(path.endswith('/docs/' + name) for path in source_names), 'Missing maintainer guide: ' + name
        assert not any('/WEBSITE_PUBLISHING' in name for name in source_names), 'Obsolete website plan in source archive'
    with zipfile.ZipFile(bundle) as archive:
        assert archive.testzip() is None
        prefix = 'linxsci-skills-' + version + '/'
        assert {prefix + 'skills/linxsci-skills/' + name for name in expected} <= set(archive.namelist())
        assert prefix + 'install.py' in archive.namelist()
        names = set(archive.namelist())
        assert not any(name.startswith(prefix + 'docs/') for name in names), 'Skill ZIP must not include CLI/SDK or maintainer guides'
        for language in ('', '.zh-CN'):
            guide = (ROOT / ('docs/USER_GUIDE' + language + '.md')).read_text(encoding='utf-8')
            guide = guide.replace('(USER_GUIDE.md)', '(README.md)').replace(
                '(USER_GUIDE.zh-CN.md)', '(README.zh-CN.md)')
            assert archive.read(prefix + 'README' + language + '.md').decode('utf-8') == guide, 'Stale bundled Skill guide'
        for name in expected:
            assert archive.read(prefix + 'skills/linxsci-skills/' + name) == (ROOT / 'skills/linxsci-skills' / name).read_bytes(), 'Stale bundled Skill file: ' + name
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
