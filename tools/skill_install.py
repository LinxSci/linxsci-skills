"""Install one verified LinxSci Release package; Python standard library only.

The release builder copies these exact bytes to scripts/linxsci_release_install.py.
No Git, SDK download, dependency recursion or business API calls occur here.
"""
import argparse
import hashlib
from http.client import HTTPException
import importlib.metadata
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import socket
import stat
import subprocess
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import zipfile
import zlib

NAMES = ('linxsci-base', 'linxsci-idea', 'linxsci-survey', 'linxsci-paper-qa',
         'linxsci-paper', 'linxsci-ppt', 'linxsci-reproduce', 'linxsci-xiaohongshu')
PUBLIC_ROOT = 'https://github.com/LinxSci/linxsci-skills/releases/download/'
VERSION = re.compile(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:\.[0-9A-Za-z]+)*)?\Z')
SHA = re.compile(r'[0-9a-f]{64}\Z')
RECEIPT = '.linxsci-release-install.json'
MAX_MANIFEST = 2 * 1024 * 1024
MAX_ZIP = 128 * 1024 * 1024
MAX_EXPANDED = 512 * 1024 * 1024
WINDOWS = sys.platform == 'win32'


class InstallError(ValueError):
    pass


def require(value, message):
    if not value:
        raise InstallError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def json_data(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key.')
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=pairs)
    except (UnicodeError, ValueError) as error:
        raise InstallError('Invalid JSON metadata.') from error


def safe_path(name):
    require(isinstance(name, str) and name and '\\' not in name and ':' not in name
            and not name.startswith('/') and not any(ord(c) < 32 for c in name), 'Unsafe package path.')
    parts = name.split('/')
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
    require(all(p not in ('', '.', '..') and not p.endswith((' ', '.'))
                and p.split('.')[0].upper() not in reserved for p in parts), 'Unsafe package path.')
    require(not any(p.casefold() in ('.git', '.gitmodules', '.env', RECEIPT) for p in parts),
            'Private or reserved package path.')
    return name


def canonical(version):
    require(isinstance(version, str) and VERSION.fullmatch(version), 'A fixed suite version is required.')
    return PUBLIC_ROOT + 'suite-v' + version + '/'


def validate_manifest(manifest, version=None):
    require(isinstance(manifest, dict) and manifest.get('schema_version') == 1, 'Unsupported manifest schema.')
    actual = manifest.get('suite_version')
    root = canonical(actual)
    require(version is None or version == actual, 'Suite version mismatch.')
    require(manifest.get('suite_tag') == 'suite-v' + actual
            and manifest.get('manifest_url') == root + 'release-manifest.json', 'Wrong manifest identity/source.')
    require(type(manifest.get('published')) is bool, 'Missing publication state.')
    require(manifest.get('status') in ('candidate', 'release')
            and manifest['published'] == (manifest['status'] == 'release'), 'Invalid publication state.')
    if manifest['status'] == 'release':
        require(re.fullmatch(r'\d+\.\d+\.\d+', actual), 'Final releases require a stable suite version.')
    require(isinstance(manifest.get('skills'), dict) and set(manifest['skills']) == set(NAMES), 'Incomplete suite manifest.')
    require(isinstance(manifest.get('sources'), dict) and set(manifest['sources']) == set(NAMES), 'Missing source identities.')
    sdk = manifest.get('sdk')
    require(isinstance(sdk, dict) and isinstance(sdk.get('version'), str)
            and re.fullmatch(r'\d+\.\d+\.\d+', sdk['version'])
            and sdk.get('name', 'linxsci') == 'linxsci', 'Invalid SDK identity.')
    for name, record in manifest['skills'].items():
        require(isinstance(record, dict), 'Invalid Skill record.')
        filename = name + ('-skill-' if name == 'linxsci-base' else '-') + actual + '.zip'
        asset = record.get('artifact', {})
        source = record.get('source', {})
        require(isinstance(asset, dict) and isinstance(source, dict), 'Invalid artifact/source record.')
        require(record.get('status') == manifest['status']
                and record.get('name') == name and record.get('version') == actual
                and record.get('suite_version') == actual and record.get('suite_tag') == manifest['suite_tag']
                and record.get('manifest_url') == manifest['manifest_url'], 'Skill identity/version mismatch.')
        require(isinstance(source.get('commit'), str) and re.fullmatch(r'[0-9a-f]{40}', source['commit'])
                and source['commit'] == manifest['sources'][name]
                and source.get('path') == ('skills/linxsci-base' if name == 'linxsci-base' else '.'), 'Source commit mismatch.')
        require(asset.get('file') == filename and asset.get('url') == root + filename, 'Wrong package asset/source.')
        require(type(asset.get('size')) is int and 0 < asset['size'] <= MAX_ZIP
                and isinstance(asset.get('sha256'), str) and SHA.fullmatch(asset['sha256'])
                and type(asset.get('file_count')) is int and 1 <= asset['file_count'] <= 20000, 'Invalid asset size/hash/count.')
        entry = safe_path(record.get('entrypoint'))
        require(entry.startswith('scripts/') and entry.endswith('.py'), 'Invalid entrypoint.')
        require(record.get('python_requires') in ('>=3.9', '>=3.10'), 'Unsupported Python constraint.')
        require(isinstance(record.get('python_requirements'), list)
                and all(isinstance(r, str) for r in record['python_requirements']), 'Missing or invalid Python requirements.')
        require(record.get('sdk_requirement') == (None if name == 'linxsci-base' else 'linxsci==' + manifest['sdk']['version']),
                'SDK constraint mismatch.')
        require(isinstance(record.get('skill_dependencies', []), list), 'Invalid dependency list.')
        for dep in record.get('skill_dependencies', []):
            require(isinstance(dep, dict) and dep.get('name') in NAMES and dep['name'] != name
                    and dep.get('kind') in ('feature', 'workflow') and isinstance(dep.get('when'), str) and dep['when'],
                    'Invalid conditional dependency.')
    return manifest


def validate_transport(url, test_http=False, redirect=False):
    parsed = urlsplit(url)
    require(not parsed.username and not parsed.password and not parsed.fragment, 'Credentials/fragments are not allowed in source URLs.')
    if test_http:
        require(parsed.scheme == 'http' and parsed.hostname in ('127.0.0.1', '::1'),
                'Test HTTP is restricted to a literal loopback address.')
    else:
        allowed = {'github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com'} if redirect else {'github.com'}
        require(parsed.scheme == 'https' and parsed.hostname in allowed and parsed.port in (None, 443),
                'Only the official HTTPS Release source is supported.')
        if not redirect:
            require(not parsed.query, 'Source URL must not contain a query.')


def fetch(url, limit, timeout, test_http=False):
    validate_transport(url, test_http)
    class Redirects(HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, target):
            validate_transport(target, test_http, redirect=True)
            return super().redirect_request(request, fp, code, msg, headers, target)
    try:
        with build_opener(Redirects()).open(Request(url, headers={'User-Agent': 'LinxSci-package-installer/1'}), timeout=timeout) as response:
            length = response.headers.get('Content-Length')
            if length is not None:
                require(length.isdigit() and int(length) <= limit, 'Download exceeds the allowed size.')
            chunks, size = [], 0
            while True:
                chunk = response.read(min(64 * 1024, limit + 1 - size))
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
                require(size <= limit, 'Download exceeds the allowed size.')
            require(length is None or size == int(length), 'Interrupted download: size mismatch.')
            return b''.join(chunks)
    except HTTPError as error:
        raise InstallError('Release download failed: HTTP ' + str(error.code)) from None
    except (URLError, TimeoutError, socket.timeout, OSError, HTTPException) as error:
        raise InstallError('Release download failed or timed out; no package was installed.') from error


class Source:
    def __init__(self, assets_dir=None, manifest_url=None, version=None, timeout=30, test_http=False):
        require(math.isfinite(timeout) and timeout > 0, 'Timeout must be positive and finite.')
        require(bool(assets_dir) != bool(manifest_url), 'Specify exactly one of --assets-dir or --manifest-url.')
        self.assets = Path(assets_dir).expanduser().resolve() if assets_dir else None
        self.url, self.timeout, self.test_http = manifest_url, timeout, test_http
        if self.assets:
            require(not test_http and self.assets.is_dir(), 'Local asset directory is unavailable.')
        else:
            require(version is not None, '--suite-version is required for a public manifest.')
            validate_transport(manifest_url, test_http)
            expected = canonical(version) + 'release-manifest.json'
            require(manifest_url == expected or (test_http and urlsplit(manifest_url).path == urlsplit(expected).path
                    and not urlsplit(manifest_url).query), 'Use the fixed suite manifest URL, not latest or a branch.')
        raw = self.read('release-manifest.json', MAX_MANIFEST)
        self.manifest = validate_manifest(json_data(raw), version)
        self.manifest_hash = digest(raw)
        require(self.assets or test_http or self.manifest['published'], 'This suite is not publicly released; provide local assets.')
        sums = self.read('SHA256SUMS', MAX_MANIFEST).decode('utf-8')
        self.sums = {}
        for line in sums.splitlines():
            fields = line.split('  ', 1)
            require(len(fields) == 2 and SHA.fullmatch(fields[0]), 'Invalid SHA256SUMS.')
            name = safe_path(fields[1])
            require('/' not in name and name not in self.sums, 'Invalid checksum asset.')
            self.sums[name] = fields[0]
        require(self.sums.get('release-manifest.json') == digest(raw), 'Manifest checksum mismatch.')
        for record in self.manifest['skills'].values():
            asset = record['artifact']
            require(self.sums.get(asset['file']) == asset['sha256'], 'Manifest/checksum disagreement.')

    def read(self, name, limit):
        safe_path(name)
        require('/' not in name, 'Expected an asset filename.')
        if self.assets:
            path = self.assets / name
            require(not path.is_symlink() and path.is_file(), 'Local asset missing: ' + name)
            require(path.stat().st_size <= limit, 'Local asset too large.')
            with path.open('rb') as stream:
                data = stream.read(limit + 1)
            require(len(data) <= limit, 'Local asset too large.')
            return data
        return fetch(self.url.rsplit('/', 1)[0] + '/' + name, limit, self.timeout, self.test_http)


def check_environment(record):
    minimum = tuple(int(p) for p in record['python_requires'][2:].split('.'))
    require(sys.version_info[:2] >= minimum, 'Python ' + record['python_requires'] + ' is required.')
    requirements = record['python_requirements']
    require(record['sdk_requirement'] is None or record['sdk_requirement'] in requirements, 'Missing SDK requirement.')
    # Only the explicit numeric constraints used by current LinxSci packages are supported.
    for requirement in requirements:
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)((?:(?:==|>=|<=|>|<)\d+(?:\.\d+)*)(?:,(?:==|>=|<=|>|<)\d+(?:\.\d+)*)*)', requirement)
        require(match is not None, 'Unsupported Python requirement: ' + str(requirement))
        try:
            installed = importlib.metadata.version(match[1])
        except importlib.metadata.PackageNotFoundError:
            raise InstallError('Missing Python dependency: ' + requirement + '. Prepare this interpreter explicitly; no environment was changed.') from None
        require(re.fullmatch(r'\d+(?:\.\d+)*', installed), 'Unsupported installed version: ' + match[1])
        def version(value):
            parts = tuple(int(p) for p in value.split('.'))
            return parts + (0,) * (8 - len(parts))
        actual = version(installed)
        for op, needed in re.findall(r'(==|>=|<=|>|<)(\d+(?:\.\d+)*)', match[2]):
            expected = version(needed)
            ok = {'==': actual == expected, '>=': actual >= expected, '<=': actual <= expected,
                  '>': actual > expected, '<': actual < expected}[op]
            require(ok, 'Python dependency mismatch: ' + requirement + '; found ' + installed + '. No environment was changed.')


def unpack(data, record):
    asset = record['artifact']
    require(len(data) == asset['size'] and digest(data) == asset['sha256'], 'Package size/SHA256 mismatch.')
    files, folded = {}, set()
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            require(len(entries) == asset['file_count'] and sum(i.file_size for i in entries) <= MAX_EXPANDED,
                    'Package count/expanded size mismatch.')
            for info in entries:
                name = safe_path(info.filename)
                require(name.casefold() not in folded and not info.is_dir(), 'Duplicate/conflicting package entry.')
                folded.add(name.casefold())
                mode = info.external_attr >> 16
                require(stat.S_IFMT(mode) in (0, stat.S_IFREG) and not info.flag_bits & 1, 'Package links/special/encrypted files are forbidden.')
                files[name] = (archive.read(info), 0o755 if mode & 0o111 else 0o644)
            for name in files:
                require(all(str(p).casefold() not in folded for p in PurePosixPath(name).parents if str(p) != '.'),
                        'Package file/directory conflict.')
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError, OSError, zlib.error) as error:
        raise InstallError('Invalid or damaged ZIP package.') from error
    validate_files(files, record)
    return files


def validate_files(files, record):
    require('release.json' in files and 'SKILL.md' in files and record['entrypoint'] in files, 'Missing package metadata or entrypoint.')
    identity = json_data(files['release.json'][0])
    require(isinstance(identity, dict), 'Invalid package identity.')
    inventory = identity.get('files')
    require(isinstance(inventory, dict), 'Missing package file inventory.')
    require({k: v for k, v in identity.items() if k != 'files'} == {k: v for k, v in record.items() if k != 'artifact'},
            'Package identity/version does not match manifest.')
    require(set(files) == set(inventory) | {'release.json'}, 'Package inventory contains missing or extra files.')
    for name, info in inventory.items():
        safe_path(name)
        data, mode = files[name]
        require(info == {'sha256': digest(data), 'size': len(data), 'mode': mode}, 'Package file changed: ' + name)
    require(re.search(r'^name:\s*' + re.escape(record['name']) + r'\s*$', files['SKILL.md'][0].decode(), re.M), 'SKILL.md identity mismatch.')
    requirements = [line.strip() for line in files.get('requirements.txt', (b'', 0))[0].decode().splitlines()
                    if line.strip() and not line.lstrip().startswith('#')]
    require(requirements == record['python_requirements'], 'Requirements file differs from metadata.')
    if record['name'] == 'linxsci-survey':
        require('scripts/survey_workflow.py' in files and 'scripts/survey.py' in files, 'Survey workflow files are missing.')
    return identity


def directory_files(folder):
    files = {}
    for path in folder.rglob('*'):
        require(not path.is_symlink(), 'Installed directory contains a symlink; preserved unchanged.')
        if path.is_dir():
            continue
        require(path.is_file(), 'Installed directory contains a special file.')
        relative = path.relative_to(folder).as_posix()
        if relative == RECEIPT or ('__pycache__' in path.relative_to(folder).parts and path.suffix == '.pyc'):
            continue
        safe_path(relative)
        files[relative] = (path.read_bytes(), 0o755 if path.stat().st_mode & 0o111 else 0o644)
    return files


def validate_runtime(folder, record, timeout=30):
    env = {k: v for k, v in os.environ.items() if not k.startswith('LINXSCI_') and k not in ('PYTHONPATH', 'PYTHONHOME')}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    # Isolated mode ignores PYTHONUTF8; set it explicitly for captured Unicode help.
    commands = [[sys.executable, '-B', '-I', '-X', 'utf8', '-c',
        "import runpy,sys; from pathlib import Path; p=Path(sys.argv[1]); "
        "sys.path.insert(0,str(p.parent)); sys.argv=[str(p),'--help']; runpy.run_path(str(p),run_name='__main__')",
        str(folder / record['entrypoint'])]]
    if record['name'] == 'linxsci-survey':
        commands.append([sys.executable, '-B', '-I', '-X', 'utf8', '-c',
            "import importlib.util,sys; from pathlib import Path; p=Path(sys.argv[1])/'scripts/survey_workflow.py'; "
            "s=importlib.util.spec_from_file_location('survey_install_check',p); m=importlib.util.module_from_spec(s); "
            "s.loader.exec_module(m); assert all(callable(getattr(m,n,None)) for n in ('prepare_survey','record','paper_path'))", str(folder)])
    for command in commands:
        try:
            result = subprocess.run(command, cwd=folder, env=env, stdin=subprocess.DEVNULL,
                                    capture_output=True, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise InstallError('Package compatibility check failed or timed out.') from error
        require(result.returncode == 0, 'Package help/workflow compatibility check failed; destination preserved.')


def destination_path(value, name):
    folder = Path(value).expanduser() if value else Path(os.environ.get('LINXSCI_SKILLS_DIR') or Path.home() / '.agents/skills') / name
    require(folder.is_absolute(), 'Destination and LINXSCI_SKILLS_DIR must be absolute paths.')
    require(not any(p.is_symlink() for p in (folder, *folder.parents)), 'Symlink destinations are not supported; use the actual directory.')
    return folder


def requester_version(requester, name, version):
    if requester is None:
        return version
    require(requester.is_file() and not requester.is_symlink(), 'Requester release.json is unavailable.')
    identity = json_data(requester.read_bytes())
    require(isinstance(identity, dict) and identity.get('name') == 'linxsci-idea'
            and name == 'linxsci-survey', 'Wrong dependency requester.')
    actual = identity.get('suite_version')
    canonical(actual)
    require(identity.get('version') == actual and (version is None or version == actual), 'Requester suite version mismatch.')
    require({'name': 'linxsci-survey', 'kind': 'feature', 'when': 'fresh-evidence'} in identity.get('skill_dependencies', []),
            'Requester does not declare the fresh-evidence dependency.')
    return actual


def check_requester(requester, manifest):
    if requester is not None:
        identity = json_data(Path(requester).read_bytes())
        require(isinstance(identity, dict)
                and {k: v for k, v in identity.items() if k != 'files'} ==
                    {k: v for k, v in manifest['skills']['linxsci-idea'].items() if k != 'artifact'},
                'Requester identity/source differs from the selected suite.')


def install(name, destination=None, *, assets_dir=None, manifest_url=None, suite_version=None,
            requester=None, yes=False, timeout=30, test_http=False):
    require(name in NAMES, 'Unknown Skill.')
    require(math.isfinite(timeout) and timeout > 0, 'Timeout must be positive and finite.')
    require(not (assets_dir and manifest_url), 'Choose one package source.')
    require(not test_http or bool(manifest_url), 'Test HTTP requires a loopback manifest URL.')
    version = requester_version(Path(requester) if requester else None, name, suite_version)
    if version is not None:
        canonical(version)
    folder = destination_path(destination, name)
    if not yes and not folder.exists():
        return {'status': 'confirmation-required', 'name': name, 'destination': str(folder),
                'suite_version': version, 'message': '未安装。确认具体来源、版本和目录后使用 --yes；原任务尚未继续。'}
    source = None
    if folder.exists():
        require(folder.is_dir(), 'Destination is not a directory; preserved unchanged.')
        receipt_path = folder / RECEIPT
        if receipt_path.is_file() and not receipt_path.is_symlink():
            receipt = json_data(receipt_path.read_bytes())
            require(isinstance(receipt, dict), 'Invalid installation receipt.')
            manifest = validate_manifest(receipt.get('manifest'), version)
            require(receipt.get('schema_version') == 1 and receipt.get('name') == name
                    and receipt.get('manifest_sha256') == digest(encoded(manifest))
                    and receipt.get('asset_sha256') == manifest['skills'][name]['artifact']['sha256'],
                    'Invalid installation receipt.')
            if manifest_url:
                validate_transport(manifest_url, test_http)
                require(manifest_url == manifest['manifest_url'] or (test_http and urlsplit(manifest_url).path == urlsplit(manifest['manifest_url']).path),
                        'Requested source differs from installed suite.')
            if assets_dir:
                # Read local identity, but do not download an already installed archive.
                source = Source(assets_dir=assets_dir, version=version, timeout=timeout)
                require(source.manifest['skills'][name] == manifest['skills'][name], 'Installed package differs from selected manifest.')
        else:
            require(assets_dir or manifest_url, 'Existing directory has no verified receipt; provide its fixed manifest. Nothing was overwritten.')
            source = Source(assets_dir, manifest_url, version, timeout, test_http)
            manifest = source.manifest
        record = manifest['skills'][name]
        check_requester(requester, manifest)
        check_environment(record)
        validate_files(directory_files(folder), record)
        validate_runtime(folder, record, timeout)
        validate_files(directory_files(folder), record)
        return {'status': 'reused', 'name': name, 'suite_version': manifest['suite_version'],
                'source_commit': record['source']['commit'], 'destination': str(folder), 'downloaded': False}
    require(assets_dir or manifest_url, 'No package source. Supply --assets-dir, or a fixed --manifest-url and --suite-version.')
    source = Source(assets_dir, manifest_url, version, timeout, test_http)
    manifest, record = source.manifest, source.manifest['skills'][name]
    check_requester(requester, manifest)
    check_environment(record)
    data = source.read(record['artifact']['file'], record['artifact']['size'])
    files = unpack(data, record)
    folder.parent.mkdir(parents=True, exist_ok=True)
    destination_path(folder, name)
    with tempfile.TemporaryDirectory(prefix='.linxsci-package-', dir=folder.parent) as temporary:
        staged = Path(temporary) / name
        staged.mkdir()
        for path, (content, mode) in files.items():
            target = staged / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            target.chmod(mode)
        validate_runtime(staged, record, timeout)
        validate_files(directory_files(staged), record)
        receipt = {'schema_version': 1, 'name': name, 'manifest': manifest,
                   'manifest_sha256': digest(encoded(manifest)), 'asset_sha256': record['artifact']['sha256']}
        (staged / RECEIPT).write_bytes(encoded(receipt))
        publish(staged, folder)
    return {'status': 'installed', 'name': name, 'suite_version': manifest['suite_version'],
            'source_commit': record['source']['commit'], 'destination': str(folder), 'downloaded': not bool(assets_dir),
            'message': '安装检查通过；由 Agent 按原参数、原工作目录和输出位置继续任务。'}


def publish(staged, folder):
    """Reserve a new target; never replace an existing or concurrently created copy."""
    folder.mkdir()  # Exclusive reservation, including against another installer.
    identity = folder.stat()
    created = {}
    try:
        if not WINDOWS:
            # POSIX rename replaces our own empty reservation atomically. A concurrent
            # writer making it nonempty causes failure instead of data replacement.
            current = folder.stat()
            require((current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino), 'Destination changed during installation.')
            staged.rename(folder)
        else:
            # Windows cannot rename over a reserved directory. Publish its receipt last.
            paths = sorted(p for p in staged.rglob('*') if p.is_file() and p.name != RECEIPT)
            paths.append(staged / RECEIPT)
            for child in paths:
                target = folder / child.relative_to(staged)
                target.parent.mkdir(parents=True, exist_ok=True)
                require(not any(p.is_symlink() for p in (target, *target.parents)), 'Destination changed during installation.')
                with target.open('xb') as stream:
                    created[target] = None
                    stream.write(child.read_bytes())
                target.chmod(child.stat().st_mode & 0o777)
                created[target] = digest(target.read_bytes())
    except BaseException:
        if folder.exists() and not folder.is_symlink():
            current = folder.stat()
            if (current.st_dev, current.st_ino) == (identity.st_dev, identity.st_ino):
                # Never remove content another process placed in the reservation.
                for path, expected in created.items():
                    if path.is_file() and not path.is_symlink() and (expected is None or digest(path.read_bytes()) == expected):
                        path.unlink()
                for path in sorted(folder.rglob('*'), key=lambda p: len(p.parts), reverse=True):
                    if path.is_dir() and not path.is_symlink() and not any(path.iterdir()):
                        path.rmdir()
                if not any(folder.iterdir()):
                    folder.rmdir()
        raise


def main(argv=None, *, default_skill=None, default_requester=None):
    parser = argparse.ArgumentParser(description=__doc__)
    if default_skill is None:
        parser.add_argument('--skill', choices=NAMES, required=True)
    parser.add_argument('--assets-dir', type=Path, help='Maintainer-provided local asset directory containing manifest, SHA256SUMS and ZIPs.')
    parser.add_argument('--manifest-url', help='Fixed official suite release-manifest.json URL.')
    parser.add_argument('--suite-version', help='Exact suite version; required for public downloads.')
    parser.add_argument('--destination', '--survey-dir', dest='destination', type=Path, help='Absolute complete Skill directory, not its parent.')
    parser.add_argument('--yes', action='store_true', help='Reuse explicit installation authorization; no interactive prompt.')
    parser.add_argument('--timeout', type=float, default=30, help='Download/validation timeout in seconds (default 30).')
    parser.add_argument('--test-allow-loopback-http', action='store_true', help='TEST ONLY: allow literal loopback HTTP fixture instead of published HTTPS assets.')
    args = parser.parse_args(argv)
    name = default_skill or args.skill
    try:
        folder = destination_path(args.destination, name)
        yes = args.yes
        if not yes and not folder.exists() and sys.stdin.isatty():
            print('目标：' + str(folder) + '\n来源：' + str(args.assets_dir or args.manifest_url or '未指定')
                  + '\n版本：' + str(args.suite_version or '所选固定清单 / 调用方元数据'), file=sys.stderr)
            try:
                yes = input('是否安装？[y/N] ').strip().lower() in ('y', 'yes', '是', '安装')
            except EOFError:
                yes = False
            if not yes:
                print(json.dumps({'status': 'cancelled', 'name': name, 'destination': str(folder)}, ensure_ascii=False))
                return 3
        result = install(name, args.destination, assets_dir=args.assets_dir, manifest_url=args.manifest_url,
                         suite_version=args.suite_version, requester=default_requester, yes=yes,
                         timeout=args.timeout, test_http=args.test_allow_loopback_http)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result['status'] in ('installed', 'reused') else 3
    except (InstallError, OSError, ValueError, KeyError, TypeError, UnicodeError) as error:
        detail = str(error) if isinstance(error, InstallError) else 'Invalid or unavailable package input/destination; existing files preserved.'
        print(json.dumps({'status': 'failed', 'name': name, 'message': detail}, ensure_ascii=False), file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print(json.dumps({'status': 'cancelled', 'name': name}), file=sys.stderr)
        return 130


if __name__ == '__main__':
    raise SystemExit(main())
