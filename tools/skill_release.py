"""Build candidate or final Skill assets from immutable commits; never upload them."""
import argparse
from email.parser import BytesParser
import fnmatch
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import stat
import subprocess
import tempfile
from urllib.parse import unquote, urlsplit
from urllib.request import url2pathname
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('linxsci-base', 'linxsci-idea', 'linxsci-survey', 'linxsci-paper-qa',
         'linxsci-paper', 'linxsci-ppt', 'linxsci-reproduce', 'linxsci-xiaohongshu')
TOOL_FILES = ('skill_release.py', 'build_skill_releases.py', 'check_skill_releases.py',
              'smoke_skill_releases.py', 'skill_install.py', 'verify_skill_installation.py',
              'publish_skill_releases.py')
INSTALLER_PATH = 'scripts/linxsci_release_install.py'
INSTALLER_INPUT = 'tools/skill_install.py'
SHA = re.compile(r'[0-9a-f]{40}\Z')
VERSION = re.compile(r'\d+\.\d+\.\d+(?:-[0-9A-Za-z]+(?:\.[0-9A-Za-z]+)*)?\Z')
EXCLUDED = ('.git', '.gitmodules', '.local', '.local-backups', '.agents', '.codex',
            '.claude', '.idea', '.vscode', '.venv*', 'venv', '__pycache__', '.pytest_cache',
            '.mypy_cache', '.ruff_cache', 'node_modules', '*.egg-info', '.eggs',
            'build', 'dist', '.env', '.env.*', '*.local.*', '*.pyc', '*.pyo', '*.log',
            '.DS_Store', '._*', 'Thumbs.db', 'Desktop.ini', '.linxsci-install.json',
            '.coverage*', '*.swp', '*.swo', '*~')
SINGLE_DIRS = {'scripts', 'references', 'agents', 'assets', 'tools'}
SINGLE_FILES = {'SKILL.md', 'SKILL.zh-CN.md', 'README.md', 'README.zh-CN.md',
                '__init__.py', 'service.json', 'requirements.txt', 'LICENSE', 'NOTICE'}


class ReleaseError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise ReleaseError(message)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key.')
            result[key] = value
        return result
    try:
        return json.loads(data, object_pairs_hook=pairs)
    except (ValueError, UnicodeError):
        raise ReleaseError('Invalid JSON input.') from None


def public_path(name):
    require(isinstance(name, str) and name and '\\' not in name and ':' not in name,
            'Unsafe archive path.')
    require(not any(ord(c) < 32 or ord(c) == 127 for c in name), 'Unsafe archive path.')
    require(not name.startswith('/') and name == posixpath.normpath(name), 'Unsafe archive path.')
    require(all(part not in ('', '.', '..') and not part.endswith((' ', '.'))
                for part in name.split('/')), 'Unsafe archive path.')
    return name


def excluded(name):
    for part in name.split('/'):
        if part == '.env.example':
            continue
        if any(fnmatch.fnmatchcase(part, pattern) for pattern in EXCLUDED):
            return True
    parts = name.split('/')
    return any(parts[i:i + 2] == ['docs', 'local'] for i in range(len(parts) - 1))


def validate_items(items):
    seen = set()
    for name, (data, mode) in items.items():
        public_path(name)
        require(not excluded(name), 'Private or generated file in archive: ' + name)
        require(name.casefold() not in seen, 'Conflicting archive paths.')
        seen.add(name.casefold())
        require(mode in (0o644, 0o755), 'Unsupported file mode.')
        require(isinstance(data, bytes), 'Invalid archive content.')
    for name in items:
        for parent in PurePosixPath(name).parents:
            if str(parent) != '.':
                require(str(parent).casefold() not in seen, 'File/directory archive conflict.')


def markdown_links(items):
    for name, (data, _) in items.items():
        if not name.endswith('.md'):
            continue
        try:
            text = data.decode('utf-8')
        except UnicodeError:
            raise ReleaseError('Invalid Markdown encoding: ' + name) from None
        for target in re.findall(r'\]\(([^)]+)\)', text):
            target = target.strip().split(' "', 1)[0].strip('<>')
            if urlsplit(target).scheme or target.startswith(('#', '//')):
                continue
            relative = unquote(target.split('#', 1)[0])
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), relative))
            require(resolved in items or any(p.startswith(resolved.rstrip('/') + '/') for p in items),
                    'Broken relative link: ' + name + ' -> ' + target)


def zip_bytes(items):
    validate_items(items)
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, (data, mode) in sorted(items.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | mode) << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()


def zip_items(data):
    result = {}
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            require(len(archive.infolist()) <= 20000, 'Too many archive entries.')
            require(sum(p.file_size for p in archive.infolist()) <= 512 * 1024 * 1024,
                    'Archive is too large.')
            for info in archive.infolist():
                require(not info.is_dir(), 'Unexpected archive directory entry.')
                require(info.filename not in result, 'Duplicate archive entry.')
                filemode = info.external_attr >> 16
                require(stat.S_IFMT(filemode) in (0, stat.S_IFREG), 'Archive links and special files are not allowed.')
                mode = 0o755 if filemode & 0o111 else 0o644
                result[info.filename] = (archive.read(info), mode)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError):
        raise ReleaseError('Invalid ZIP archive.') from None
    validate_items(result)
    return result


def git(repo, *arguments, env=None, input=None):
    try:
        process = subprocess.run(['git', '-C', str(repo), *arguments], capture_output=True,
                                 env=env, input=input, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        raise ReleaseError('Git operation unavailable or timed out; private details suppressed.') from None
    if process.returncode:
        if any(term in process.stderr.lower() for term in
               (b'resolve', b'network', b'connect', b'permission denied', b'authentication')):
            raise ReleaseError('Git network/authentication operation failed; private details suppressed.')
        raise ReleaseError('Git ' + arguments[0] + ' failed; private details suppressed.')
    return process.stdout


def check_local_source(source):
    # File URLs contain /C:/... on Windows; unquoting alone is not a native path.
    local = Path(url2pathname(urlsplit(source).path) if source.startswith('file://') else source)
    if not local.is_dir():
        return
    if git(local, 'rev-parse', '--is-bare-repository').strip() == b'true':
        return
    metadata = Path(os.fsdecode(git(local, 'rev-parse', '--git-dir').strip()))
    if not metadata.is_absolute():
        metadata = local / metadata
    with tempfile.TemporaryDirectory(prefix='linxsci-read-index-') as temp:
        index = Path(temp) / 'index'
        if (metadata / 'index').exists():
            shutil.copy2(metadata / 'index', index)
        env = os.environ.copy()
        env['GIT_INDEX_FILE'] = str(index)
        env['GIT_OPTIONAL_LOCKS'] = '0'
        require(not git(local, 'status', '--porcelain', '--untracked-files=all', env=env).strip(),
                'Local source repository has uncommitted files; use a committed remote source.')


def fetch_tree(source, commit, destination):
    require(isinstance(source, str) and source and not source.startswith('-')
            and not any(c in source for c in '\n\r\0'), 'Invalid private source mapping.')
    require(SHA.fullmatch(commit), 'Source commits must be full SHA-1 values.')
    check_local_source(source)
    destination.mkdir()
    git(destination, 'init', '--quiet')
    try:
        git(destination, 'fetch', '--quiet', '--no-tags', source, commit)
    except ReleaseError as error:
        if 'network/authentication' in str(error) or 'timed out' in str(error):
            raise
        # Some servers reject fetching an unadvertised SHA, even if it is an
        # ancestor of a branch. Fetch advertised refs, then still require the pin.
        git(destination, 'fetch', '--quiet', '--no-tags', source,
            '+refs/heads/*:refs/remotes/source/*', '+refs/tags/*:refs/tags/*')
        try:
            require(git(destination, 'cat-file', '-t', commit).strip() == b'commit',
                    'Pinned source object is not a commit.')
        except ReleaseError:
            raise ReleaseError('Pinned source commit is unavailable from repository refs.') from None
    git(destination, 'checkout', '--quiet', '--detach', commit)
    require(git(destination, 'rev-parse', 'HEAD').decode().strip() == commit, 'Wrong fetched commit.')
    require(not git(destination, 'status', '--porcelain', '--untracked-files=all').strip(),
            'Fetched repository is dirty.')
    entries = []
    for record in git(destination, 'ls-tree', '-r', '-z', 'HEAD').split(b'\0'):
        if not record:
            continue
        header, raw_name = record.split(b'\t', 1)
        mode, kind, object_id = header.split()
        name = os.fsdecode(raw_name)
        public_path(name)
        if excluded(name):
            continue
        require(kind == b'blob' and mode in (b'100644', b'100755'),
                'Source contains a link or nested repository: ' + name)
        entries.append((name, mode, object_id))
    # Read Git blobs, not checkout bytes: global line-ending conversions or
    # smudge filters must not change a fixed-commit distribution.
    raw = git(destination, 'cat-file', '--batch', input=b''.join(oid + b'\n' for _, _, oid in entries))
    files, offset = {}, 0
    for name, mode, object_id in entries:
        end = raw.index(b'\n', offset)
        actual_id, kind, size = raw[offset:end].split()
        require(actual_id == object_id and kind == b'blob', 'Unexpected Git blob response.')
        size = int(size)
        content = raw[end + 1:end + 1 + size]
        require(len(content) == size, 'Incomplete Git blob response.')
        files[name] = (content, int(mode, 8) & 0o777)
        offset = end + size + 2
    validate_items(files)
    return files


def validate_config(lock, recipe, base_commit, sources):
    require(isinstance(lock, dict) and lock.get('schema_version') == 1, 'Unsupported lock schema.')
    rows = lock.get('extensions', [])
    require(isinstance(rows, list) and len(rows) == 7, 'Expected seven extension commits.')
    require(all(isinstance(row, dict) for row in rows), 'Invalid extension record.')
    require({row.get('name') for row in rows} == set(NAMES[1:]), 'Wrong extension names.')
    for row in rows:
        require(row.get('path') == 'skills/' + row['name'], 'Unexpected extension path.')
        require(isinstance(row.get('commit'), str) and SHA.fullmatch(row['commit']), 'Invalid extension SHA.')
    require(isinstance(base_commit, str) and SHA.fullmatch(base_commit), 'Base commit must be a full SHA.')
    require(isinstance(recipe, dict) and recipe.get('schema_version') == 1, 'Unsupported recipe schema.')
    require(isinstance(recipe.get('suite_version'), str) and VERSION.fullmatch(recipe['suite_version']), 'Invalid suite version.')
    require(recipe.get('status') in ('candidate', 'release'), 'Unsupported recipe status.')
    if recipe['status'] == 'release':
        require(re.fullmatch(r'\d+\.\d+\.\d+', recipe['suite_version']),
                'Final releases require a stable suite version.')
    require(recipe.get('github_repository') == 'LinxSci/linxsci-skills', 'Unexpected public release repository.')
    if 'license' in recipe:
        require(recipe['license'] == {'spdx': 'MIT', 'file': 'LICENSE'}, 'Unsupported suite license.')
    require(set(recipe.get('skills', {})) == set(NAMES), 'Recipe must describe all eight Skills.')
    require(isinstance(sources, dict) and set(sources) == set(NAMES), 'Private mapping must contain all eight source repositories.')
    require(all(isinstance(value, str) and value and not value.startswith('-')
                and not any(c in value for c in '\n\r\0') for value in sources.values()),
            'Invalid private source mapping.')
    sdk = recipe.get('sdk', {})
    require(sdk.get('name') == 'linxsci' and isinstance(sdk.get('version'), str)
            and re.fullmatch(r'\d+\.\d+\.\d+', sdk['version']), 'Invalid SDK identity.')
    require(sdk.get('file') == 'linxsci-' + sdk['version'] + '-py3-none-any.whl', 'Invalid SDK asset name.')
    require(re.fullmatch(r'[a-f0-9]{64}', sdk.get('sha256', '')), 'SDK checksum is required.')
    for name, spec in recipe['skills'].items():
        public_path(spec['entrypoint'])
        require(spec['entrypoint'].startswith('scripts/') and spec['entrypoint'].endswith('.py'), 'Invalid entrypoint.')
        require(spec.get('python_requires') in ('>=3.9', '>=3.10'), 'Unsupported Python constraint.')
        for dep in spec.get('skill_dependencies', []):
            require(dep.get('name') in NAMES and dep['name'] != name
                    and dep.get('kind') in ('feature', 'workflow') and dep.get('when'),
                    'Invalid conditional Skill dependency.')


def private_markers(sources):
    markers = set()
    for source in sources.values():
        markers.add(source.encode())
        parsed = urlsplit(source if '://' in source else 'ssh://' + source.replace(':', '/', 1))
        if parsed.hostname and 'codeup' in parsed.hostname.lower():
            markers.add(parsed.hostname.encode())
    return markers


def check_private(items, markers):
    for name, (data, _) in items.items():
        require(not any(marker in data for marker in markers), 'Private source data in public file: ' + name)


def inventory(items):
    return {name: {'sha256': sha256(data), 'size': len(data), 'mode': mode}
            for name, (data, mode) in sorted(items.items())}


def artifact(name, data, public_root):
    return {'file': name, 'url': public_root + '/' + name, 'sha256': sha256(data), 'size': len(data)}


def sdk_check(data, recipe, base_tree):
    sdk = recipe['sdk']
    require(sha256(data) == sdk['sha256'], 'SDK wheel checksum mismatch.')
    files = zip_items(data)
    metadata_path = 'linxsci-' + sdk['version'] + '.dist-info/METADATA'
    require(metadata_path in files, 'Missing SDK metadata.')
    metadata = BytesParser().parsebytes(files[metadata_path][0])
    require(metadata['Name'] == sdk['name'] and metadata['Version'] == sdk['version'], 'Wrong SDK wheel version.')
    require(not metadata.get_all('Requires-Dist'), 'Unexpected SDK runtime dependency.')
    for name, (content, _) in files.items():
        if name.startswith('linxsci/'):
            original = 'skills/linxsci-base/' + name[len('linxsci/'):]
            require(original in base_tree and base_tree[original][0] == content,
                    'SDK wheel does not match the pinned base source: ' + name)
    require('linxsci/scripts/cli.py' in files, 'SDK wheel has no CLI.')
    return files


def license_note(license_spec):
    if not license_spec:
        return ''
    return ('\n## License / 许可\n\n'
            'Code and Skill instructions use the [MIT License](LICENSE), allowing use, modification, commercial use and redistribution. '
            'Retain the copyright and permission notice, including when redistributing the SDK wheel. '
            'API access still requires a valid key and follows service access rules. Third-party materials retain their own licenses.\n\n'
            '代码与 Skill 指令采用 [MIT 许可证](LICENSE)，允许使用、修改、商业使用和再分发。'
            '再分发（包括 SDK wheel）时保留版权声明和许可文本。API 仍需有效 Key 并遵守服务访问规则，第三方材料保留其原许可。\n')


def package_note(name, version, entrypoint, license_spec=None):
    return (f"# {name} — {version}\n\n"
            "Obtain the fixed suite assets from "
            "https://github.com/LinxSci/linxsci-skills/releases. Verify its manifest, SHA256SUMS and ZIP identity. "
            "A supplied local asset directory for the same version is also supported. "
            "Extract the complete flat package into a persistent directory; preserve local edits.\n\n"
            "从 LinxSci Releases 获取固定套件资产，也可使用同版本本地资产目录。"
            "核验清单、SHA256SUMS 和 ZIP 身份，完整解压到长期目录，保留已有修改。\n\n"
            "The standard-library installer is bundled at scripts/linxsci_release_install.py. It installs one explicitly "
            "selected package, validates metadata, files, environment and help, and never invokes Git, installs Python dependencies "
            "or recursively installs collaborators. Prepare requirements in the same interpreter first.\n\n"
            "```bash\npython scripts/linxsci_release_install.py --help\n"
            f"python {entrypoint} --help\n```\n\n"
            "Use --skill NAME with --assets-dir PATH for a local asset directory, or --manifest-url URL and --suite-version VERSION "
            "for a fixed official HTTPS suite. --destination is the absolute Skill directory. --yes reuses explicit authorization. "
            "Only installed/reused with exit 0 mean installation checks passed; confirmation-required/cancelled exit 3, failures exit 2. "
            "A valid unchanged installation is reused. Other existing directories are preserved and rejected, not overwritten.\n\n"
            "标准库安装入口已随包提供；用 --skill 指定一个目标，--assets-dir 指定本地资产，或用 --manifest-url 与 --suite-version "
            "指定固定公开清单。--destination 是完整 Skill 绝对目录，已有授权可用 --yes。只安装明确选择的包，不调用 Git、不升级 Python "
            "环境、不递归安装协作者；先在同一解释器准备 requirements。仅 installed/reused（退出 0）表示安装检查通过，"
            "待确认/取消退出 3，失败退出 2；已有修改或残缺目录不覆盖。\n\n"
            "For Idea fresh retrieval, install Survey from the same suite and resume the original arguments, working directory and output. "
            "The Idea adapter enforces the requester release.json version. Use Release assets for dependencies; "
            "existing evidence reuse needs no Survey download.\n\n"
            "Idea 新取证按同套件安装 Survey 后，由 Agent 保留原参数、原工作目录和输出位置续跑；适配入口核对调用方 release.json。"
            "依赖从 Release 资产取得；已有证据复用不下载 Survey。\n\n"
            "This flat package has no root install.py. The base Skill can use python scripts/cli.py install-skill; "
            "the legacy linxsci-base-0.3.4.zip has separate root installers. CLI/SDK remains 0.3.4. "
            "Configure LINXSCI_SKILLS_DIR as the absolute parent for CLI discovery and configure Agent discovery separately. "
            "Refresh the Agent; installation/help checks are not business-task acceptance.\n\n"
            "平铺包没有根目录 install.py，基础 Skill 可用 scripts/cli.py install-skill；旧 0.3.4 基础安装器 ZIP 格式不同。"
            "SDK/CLI 仍为 0.3.4。CLI 的 LINXSCI_SKILLS_DIR 使用绝对父目录，Agent 发现另行配置并刷新，安装/帮助检查不等于业务完成。\n\n"
            "Updates require newly verified assets and preservation of edits; Release copies do not use git pull or promise remote updates "
            "from local npx installs. Keep Symlink targets persistent. Tests require a source snapshot or maintainer source; single/full "
            "packages omit tests. Third-party libraries, fonts and production tools are not bundled.\n\n"
            "更新重新取得并核验包、保护已有修改；不用 git pull，不承诺本地 npx 自动更新。符号链接目标长期保留。"
            "测试需要源码快照或维护者源码，单项/完整包不含测试，也不包含第三方库、字体或外部制作环境。\n\n"
            "See [Skill instructions](SKILL.md).\n" + license_note(license_spec)).encode('utf-8')


def make_skill(name, tree, main_tree, commit, recipe, manifest_url, installer_data=None):
    version = recipe['suite_version']
    spec = recipe['skills'][name]
    if name == 'linxsci-base':
        prefix = 'skills/linxsci-base/'
        tree = {path[len(prefix):]: item for path, item in main_tree.items() if path.startswith(prefix)}
    files = {path: item for path, item in tree.items()
             if path in SINGLE_FILES or path.split('/')[0] in SINGLE_DIRS}
    if recipe.get('license'):
        require('LICENSE' in main_tree and files.get('LICENSE') == main_tree['LICENSE'],
                'Missing or inconsistent Skill LICENSE: ' + name)
    generated = {}
    if installer_data is not None:
        require(INSTALLER_PATH not in files, 'Generated installer path conflicts with source.')
        files[INSTALLER_PATH] = (installer_data, 0o644)
        generated[INSTALLER_PATH] = {'build_input': INSTALLER_INPUT, 'sha256': sha256(installer_data)}
    require('SKILL.md' in files and spec['entrypoint'] in files, 'Incomplete Skill: ' + name)
    require(re.search(r'^name:\s*' + re.escape(name) + r'\s*$', files['SKILL.md'][0].decode(), re.M),
            'SKILL.md name mismatch: ' + name)
    note = package_note(name, version, spec['entrypoint'], recipe.get('license'))
    if name == 'linxsci-base':
        files['README.md'] = (note, 0o644)
        files['README.zh-CN.md'] = (note, 0o644)
    files['PACKAGE.md'] = (note, 0o644)
    requirements = [line.strip() for line in files.get('requirements.txt', (b'', 0o644))[0].decode().splitlines()
                    if line.strip() and not line.lstrip().startswith('#')]
    expected_sdk = 'linxsci==' + recipe['sdk']['version']
    if name != 'linxsci-base':
        require(expected_sdk in requirements, 'Extension SDK constraint mismatch: ' + name)
    else:
        require(not requirements, 'Base Skill unexpectedly requires Python packages.')
    identity = {'schema_version': 1, 'status': recipe['status'], 'name': name, 'version': version,
                'suite_version': version, 'suite_tag': 'suite-v' + version, 'manifest_url': manifest_url,
                'source': {'commit': commit, 'path': 'skills/linxsci-base' if name == 'linxsci-base' else '.'},
                'python_requires': spec['python_requires'], 'python_requirements': requirements,
                'sdk_requirement': expected_sdk if name != 'linxsci-base' else None,
                'entrypoint': spec['entrypoint'], 'skill_dependencies': spec.get('skill_dependencies', []),
                'external_requirements': spec.get('external_requirements', []),
                'dependency_installation': 'explicit-package-installer-v1' if generated else 'not-implemented',
                'files': inventory(files)}
    if generated:
        identity['generated_files'] = generated
    if recipe.get('license'):
        identity['license'] = recipe['license']
    files['release.json'] = (encoded(identity), 0o644)
    markdown_links(files)
    return files, identity


def build(lock_path, recipe_path, sources_path, base_commit, sdk_wheel, output, *, release_mode=False):
    lock_data, recipe_data = lock_path.read_bytes(), recipe_path.read_bytes()
    lock, recipe = json_bytes(lock_data), json_bytes(recipe_data)
    sources = json_bytes(sources_path.read_bytes())
    validate_config(lock, recipe, base_commit, sources)
    require((recipe['status'] == 'release') == release_mode,
            'Final recipe requires --release; candidate recipe must not use --release.')
    require(not release_mode or recipe.get('license'), 'Final releases require an explicit license.')
    require(not output.exists(), 'Output already exists; select a new asset directory.')
    require(sdk_wheel.name == recipe['sdk']['file'], 'Unexpected wheel filename.')
    wheel_data = sdk_wheel.read_bytes()
    require(sha256(wheel_data) == recipe['sdk']['sha256'], 'SDK wheel checksum mismatch.')
    commits = {row['name']: row['commit'] for row in lock['extensions']}
    commits['linxsci-base'] = base_commit
    version = recipe['suite_version']
    root_url = 'https://github.com/' + recipe['github_repository'] + '/releases/download/suite-v' + version
    manifest_url = root_url + '/release-manifest.json'
    recipe_inputs = {'extensions.lock.json': (lock_data, 0o644), 'suite.json': (recipe_data, 0o644)}
    for name in TOOL_FILES:
        recipe_inputs['tools/' + name] = (Path(__file__).with_name(name).read_bytes(), 0o644)
    markers = private_markers(sources)
    check_private(recipe_inputs, markers)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Build entirely in private scratch directories. Only verified assets become output.
    with tempfile.TemporaryDirectory(prefix='linxsci-source-') as scratch:
        trees = {}
        for name in NAMES:
            print('Fetching fixed commit: ' + name, flush=True)
            try:
                trees[name] = fetch_tree(sources[name], commits[name], Path(scratch) / name)
            except ReleaseError as error:
                raise ReleaseError(name + ': ' + str(error)) from None
            check_private(trees[name], markers)
        main_tree = trees['linxsci-base']
        require('pyproject.toml' in main_tree, 'Pinned base project has no Python metadata.')
        require(re.search(r'^version\s*=\s*"' + re.escape(recipe['sdk']['version']) + r'"\s*$',
                          main_tree['pyproject.toml'][0].decode(), re.M), 'Base SDK version mismatch.')
        sdk_files = sdk_check(wheel_data, recipe, main_tree)
        check_private(sdk_files, markers)
        assets = {sdk_wheel.name: wheel_data}
        if recipe.get('license'):
            require('LICENSE' in main_tree and main_tree['LICENSE'][0].startswith(b'MIT License\n'),
                    'Missing main MIT LICENSE.')
            assets['LICENSE'] = main_tree['LICENSE'][0]
        records, packages = {}, {}
        for name in NAMES:
            files, identity = make_skill(name, trees[name], main_tree, commits[name], recipe, manifest_url,
                                         recipe_inputs[INSTALLER_INPUT][0])
            check_private(files, markers)
            filename = name + ('-skill-' if name == 'linxsci-base' else '-') + version + '.zip'
            content = zip_bytes(files)
            assets[filename] = content
            records[name] = {**{key: value for key, value in identity.items() if key != 'files'},
                             'artifact': {**artifact(filename, content, root_url), 'file_count': len(files)}}
            packages[name] = files
        manifest = {'schema_version': 1, 'status': recipe['status'], 'suite_version': version,
                    'suite_tag': 'suite-v' + version, 'published': release_mode,
                    'manifest_url': manifest_url, 'dependency_installation': 'explicit-package-installer-v1',
                    'sources': commits, 'build_inputs': inventory(recipe_inputs),
                    'sdk': {**recipe['sdk'], 'artifact': artifact(sdk_wheel.name, wheel_data, root_url)},
                    'skills': records,
                    'bundles': {'full': 'linxsci-skills-' + version + '-full.zip',
                                'source': 'linxsci-skills-' + version + '-source.zip'}}
        if recipe.get('license'):
            manifest['license'] = {**recipe['license'], 'artifact': artifact('LICENSE', assets['LICENSE'], root_url)}
        manifest_data = encoded(manifest)
        assets['release-manifest.json'] = manifest_data
        guide = ('# LinxSci suite ' + version + '\n\n'
                 'Verify outer SHA256SUMS, the manifest and each package inventory. '
                 'The eight actual directories are under skills/, individual ZIPs under packages/, and the unchanged SDK under wheels/.\n\n'
                 '核对外层 SHA256SUMS、发行清单及各包文件清单。skills/ 是八个真实目录，packages/ 是单项 ZIP，'
                 'wheels/ 包含未改动的 SDK。\n\n'
                 'Every Skill bundles scripts/linxsci_release_install.py, copied from the hashed build input. '
                 'Use its --help for explicit local or fixed HTTPS package installation; it does not invoke Git, install Python packages '
                 'or automatically traverse all collaborators. The Idea adapter installs Survey from the same suite before the Agent '
                 'resumes the original task.\n\n'
                 '各 Skill 随附同一份 scripts/linxsci_release_install.py，来源哈希记录在构建输入和 generated_files。'
                 '用 --help 查看本地/固定 HTTPS 包安装参数；不调用 Git、不升级 Python 环境、不递归安装协作者。'
                 'Idea 适配入口安装同套件 Survey 后由 Agent 原参数续跑。\n\n'
                 'Install only the complete Skill directories needed. Preserve existing files, edits and configuration. '
                 'Set LINXSCI_SKILLS_DIR to the absolute parent for CLI discovery, then configure and refresh each Agent separately. '
                 'Use Python 3.10+ for all extensions together and install their requirements in the same environment. '
                 'The SDK wheel can be installed offline from this directory:\n\n'
                 '```bash\npython -m pip install --no-index --no-deps wheels/' + sdk_wheel.name + '\n```\n\n'
                 '按需安装完整目录、保护已有修改；CLI 发现父目录与 Agent 发现分别设置并刷新。全套环境需 Python 3.10+，'
                 '同一解释器按各 README 准备全部 requirements。小红书仍需 PyMuPDF、Pillow 和字体，PPT 等制作工具由宿主提供。\n\n'
                 'Flat packages have no root install.py. Single/full packages omit tests: development checks need the source snapshot '
                 'or complete maintainer source. Third-party libraries, fonts and experiment/production tools are not included; this '
                 'is not a full offline environment. Updates use verified new packages, not git pull. Local npx installations do not '
                 'promise remote updates; Symlink targets must persist. Help checks do not prove research completion.\n\n'
                 '平铺包无根目录 install.py；开发测试需源码快照或维护者源码。完整套件不是第三方依赖、字体和实验工具的离线环境。'
                 '更新重新核验包，不用 git pull，不承诺本地 npx 自动更新；链接目标长期保留，帮助通过不等于业务完成。\n').encode()
        guide += license_note(recipe.get('license')).encode('utf-8')
        full = {'README.md': (guide, 0o644), 'README.zh-CN.md': (guide, 0o644),
                'release-manifest.json': (manifest_data, 0o644),
                'wheels/' + sdk_wheel.name: (wheel_data, 0o644)}
        if recipe.get('license'):
            full['LICENSE'] = main_tree['LICENSE']
        for name, files in packages.items():
            full.update({'skills/' + name + '/' + path: item for path, item in files.items()})
            filename = records[name]['artifact']['file']
            full['packages/' + filename] = (assets[filename], 0o644)
        markdown_links(full)
        assets[manifest['bundles']['full']] = zip_bytes(full)
        # Preserve all allowed tracked source files, including tests and maintenance tools.
        source = dict(main_tree)
        for name in NAMES[1:]:
            source.update({'skills/' + name + '/' + path: item for path, item in trees[name].items()})
        for name, files in packages.items():
            path = 'skills/' + name + '/' + INSTALLER_PATH
            require(path not in source, 'Generated installer conflicts with source snapshot.')
            source[path] = files[INSTALLER_PATH]
        source['release-manifest.json'] = (manifest_data, 0o644)
        for path, item in recipe_inputs.items():
            source['release/build-inputs/' + path] = item
        source_note = ('# Fixed source snapshot\n\n'
                       'This snapshot contains the allowed tracked files of the eight commits in `release-manifest.json`. '
                       'Developer working-tree changes are not included. Git metadata and private URLs are omitted. '
                       'Each Skill also includes a generated scripts/linxsci_release_install.py copied byte-for-byte from '
                       'release/build-inputs/tools/skill_install.py; generated_files records its origin and hash separately '
                       'from the fixed source commit.\n\n'
                       'The build recipe and exact builder files are under `release/build-inputs/`; their hashes appear in '
                       '`build_inputs` in the manifest. These recipe files are separate from the pinned base commit. '
                       'Rebuild using that builder with explicit `--lock`, `--recipe`, `--base-commit`, `--sources`, '
                       '`--sdk-wheel` and `--output` arguments. Private source access is required only for rebuilding.\n\n'
                       '本快照包括八个固定提交的公开源码、测试与维护资料；另附构建配方及工具快照。'
                       '各 Skill 额外附带从构建输入逐字节生成的公共安装模块，来源和哈希由 generated_files 单独记录，不伪称为固定提交文件。'
                       '开发工作区的未提交修改不属于固定源码部分。\n').encode()
        source['SOURCE_SNAPSHOT.md'] = (source_note, 0o644)
        markdown_links(source)
        check_private(source, markers)
        prefix = 'linxsci-skills-' + version + '-source/'
        assets[manifest['bundles']['source']] = zip_bytes({prefix + path: item for path, item in source.items()})
        sums = ''.join(sha256(data) + '  ' + name + '\n' for name, data in sorted(assets.items())).encode()
        assets['SHA256SUMS'] = sums
        with tempfile.TemporaryDirectory(prefix='.linxsci-candidate-', dir=output.parent) as temp:
            staged = Path(temp) / 'assets'
            staged.mkdir()
            for name, data in assets.items():
                (staged / name).write_bytes(data)
            check(staged)
            require(not output.exists(), 'Output appeared during build; no existing files were changed.')
            staged.rename(output)
    return manifest


def check(directory):
    require(directory.is_dir(), 'Candidate directory is missing.')
    require(not any(p.is_symlink() or not p.is_file() for p in directory.iterdir()), 'Unexpected candidate directory entry.')
    manifest = json_bytes((directory / 'release-manifest.json').read_bytes())
    require(manifest.get('schema_version') == 1 and manifest.get('status') in ('candidate', 'release')
            and type(manifest.get('published')) is bool
            and manifest['published'] == (manifest['status'] == 'release'), 'Invalid publication state.')
    version = manifest['suite_version']
    require(VERSION.fullmatch(version) and manifest['suite_tag'] == 'suite-v' + version, 'Manifest version mismatch.')
    if manifest['status'] == 'release':
        require(re.fullmatch(r'\d+\.\d+\.\d+', version), 'Final releases require a stable suite version.')
    root_url = 'https://github.com/LinxSci/linxsci-skills/releases/download/' + manifest['suite_tag']
    require(manifest['manifest_url'] == root_url + '/release-manifest.json', 'Wrong manifest URL.')
    require(set(manifest['skills']) == set(NAMES) and set(manifest['sources']) == set(NAMES), 'Incomplete manifest.')
    require(all(SHA.fullmatch(commit) for commit in manifest['sources'].values()), 'Invalid source commit.')
    expected = {'release-manifest.json', 'SHA256SUMS', manifest['sdk']['artifact']['file'], *manifest['bundles'].values()}
    expected.update(record['artifact']['file'] for record in manifest['skills'].values())
    license_spec = None
    if 'license' in manifest:
        notice = manifest['license']
        require(isinstance(notice, dict) and set(notice) == {'spdx', 'file', 'artifact'}
                and notice['spdx'] == 'MIT' and notice['file'] == 'LICENSE', 'Invalid suite license identity.')
        license_spec = {'spdx': notice['spdx'], 'file': notice['file']}
        expected.add('LICENSE')
    require(len(expected) == (14 if license_spec else 13)
            and {p.name for p in directory.iterdir()} == expected, 'Wrong candidate asset set.')
    sums = {}
    for line in (directory / 'SHA256SUMS').read_text().splitlines():
        fields = line.split('  ', 1)
        require(len(fields) == 2 and re.fullmatch(r'[a-f0-9]{64}', fields[0]), 'Invalid checksum line.')
        digest, name = fields
        require(name in expected - {'SHA256SUMS'} and name not in sums, 'Invalid checksum asset.')
        require(sha256((directory / name).read_bytes()) == digest, 'Checksum mismatch: ' + name)
        sums[name] = digest
    require(set(sums) == expected - {'SHA256SUMS'}, 'Incomplete checksums.')
    license_data = None
    if license_spec:
        license_data = (directory / 'LICENSE').read_bytes()
        require(manifest['license']['artifact'] == artifact('LICENSE', license_data, root_url)
                and license_data.startswith(b'MIT License\n'), 'License artifact mismatch.')
    packages = {}
    for name, record in manifest['skills'].items():
        asset = record['artifact']
        expected_name = name + ('-skill-' if name == 'linxsci-base' else '-') + version + '.zip'
        require(asset['file'] == expected_name and asset['url'] == root_url + '/' + expected_name, 'Wrong package download identity.')
        data = (directory / asset['file']).read_bytes()
        require(asset['size'] == len(data) and asset['sha256'] == sha256(data), 'Package hash/size mismatch.')
        files = zip_items(data)
        require(asset['file_count'] == len(files), 'Package file count mismatch.')
        require('SKILL.md' in files and record['entrypoint'] in files and 'release.json' in files, 'Missing Skill entrypoint.')
        identity = json_bytes(files['release.json'][0])
        require(identity.pop('files') == inventory({p: item for p, item in files.items() if p != 'release.json'}), 'Skill inventory mismatch.')
        require(identity == {key: value for key, value in record.items() if key != 'artifact'}, 'Skill metadata mismatch.')
        require(record['status'] == manifest['status']
                and record['name'] == name and record['version'] == version and record['suite_version'] == version
                and record['source']['commit'] == manifest['sources'][name]
                and record['manifest_url'] == manifest['manifest_url'], 'Skill provenance mismatch.')
        require(record.get('license') == license_spec, 'Skill license metadata mismatch.')
        if license_spec:
            require(files.get('LICENSE') == (license_data, 0o644), 'Skill license differs from suite notice.')
        markdown_links(files)
        packages[name] = files
    sdk_asset = manifest['sdk']['artifact']
    require(sdk_asset['file'] == manifest['sdk']['file'] and sdk_asset['url'] == root_url + '/' + sdk_asset['file'], 'Wrong SDK asset identity.')
    wheel_data = (directory / sdk_asset['file']).read_bytes()
    require(sdk_asset['size'] == len(wheel_data) and sdk_asset['sha256'] == manifest['sdk']['sha256'] == sha256(wheel_data), 'SDK artifact mismatch.')
    require(manifest['bundles'] == {'full': 'linxsci-skills-' + version + '-full.zip',
                                    'source': 'linxsci-skills-' + version + '-source.zip'}, 'Wrong bundle names.')
    full = zip_items((directory / manifest['bundles']['full']).read_bytes())
    require(full['release-manifest.json'][0] == (directory / 'release-manifest.json').read_bytes(), 'Full bundle manifest mismatch.')
    require(full['wheels/' + sdk_asset['file']][0] == wheel_data, 'Full bundle wheel mismatch.')
    expected_full = {'README.md', 'README.zh-CN.md', 'release-manifest.json', 'wheels/' + sdk_asset['file']}
    if license_spec:
        expected_full.add('LICENSE')
        require(full.get('LICENSE') == (license_data, 0o644), 'Full bundle license mismatch.')
    for name, files in packages.items():
        filename = manifest['skills'][name]['artifact']['file']
        require(full['packages/' + filename][0] == (directory / filename).read_bytes(), 'Embedded package mismatch.')
        expected_full.add('packages/' + filename)
        for path, item in files.items():
            target = 'skills/' + name + '/' + path
            require(full.get(target) == item, 'Expanded Skill differs from its package.')
            expected_full.add(target)
    require(set(full) == expected_full, 'Unexpected full bundle content.')
    markdown_links(full)
    source = zip_items((directory / manifest['bundles']['source']).read_bytes())
    prefix = 'linxsci-skills-' + version + '-source/'
    require(all(path.startswith(prefix) for path in source), 'Wrong source snapshot root.')
    source = {path[len(prefix):]: item for path, item in source.items()}
    if license_spec:
        require(source.get('LICENSE') == (license_data, 0o644), 'Source license mismatch.')
    require(source['release-manifest.json'][0] == (directory / 'release-manifest.json').read_bytes(), 'Source manifest mismatch.')
    inputs = {path[len('release/build-inputs/'):]: item for path, item in source.items() if path.startswith('release/build-inputs/')}
    require(inventory(inputs) == manifest['build_inputs'], 'Build recipe snapshot mismatch.')
    lock = json_bytes(inputs['extensions.lock.json'][0])
    recipe = json_bytes(inputs['suite.json'][0])
    validate_config(lock, recipe, manifest['sources']['linxsci-base'], {name: 'unused' for name in NAMES})
    require(recipe.get('license') == license_spec, 'Recipe license mismatch.')
    require(recipe['status'] == manifest['status'] and recipe['suite_version'] == version
            and recipe['sdk'] == {k: v for k, v in manifest['sdk'].items() if k != 'artifact'}, 'Recipe metadata mismatch.')
    require({row['name']: row['commit'] for row in lock['extensions']} == {name: commit for name, commit in manifest['sources'].items() if name != 'linxsci-base'}, 'Source lock mismatch.')
    installer_enabled = manifest.get('dependency_installation') == 'explicit-package-installer-v1'
    if installer_enabled:
        require(INSTALLER_INPUT in inputs, 'Installer build input is missing.')
    for name, files in packages.items():
        generated = manifest['skills'][name].get('generated_files', {})
        expected_generated = {INSTALLER_PATH: {'build_input': INSTALLER_INPUT,
                              'sha256': sha256(inputs[INSTALLER_INPUT][0])}} if installer_enabled else {}
        require(generated == expected_generated, 'Generated installer provenance mismatch.')
        if installer_enabled:
            require(files.get(INSTALLER_PATH) == inputs[INSTALLER_INPUT], 'Generated installer differs from build input.')
            require(manifest['skills'][name]['dependency_installation'] == 'explicit-package-installer-v1',
                    'Installer capability mismatch.')
        for path, item in files.items():
            if path in ('release.json', 'PACKAGE.md') or (name == 'linxsci-base' and path in ('README.md', 'README.zh-CN.md')):
                continue
            require(source.get('skills/' + name + '/' + path) == item, 'Source snapshot differs from packaged Skill.')
    sdk_check(wheel_data, recipe, source)
    markdown_links(source)
    return {'suite_version': version, 'assets': len(expected), 'skills': len(packages),
            'status': manifest['status'], 'published': manifest['published'],
            'hashes_and_sizes': 'passed', 'relative_links': 'passed',
            'source_and_bundle_consistency': 'passed'}


def build_main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lock', type=Path, default=ROOT / 'extensions.lock.json')
    parser.add_argument('--recipe', type=Path, default=ROOT / 'release/suite.json')
    parser.add_argument('--sources', type=Path, required=True, help='Private JSON mapping of eight source names to repository URLs.')
    parser.add_argument('--base-commit', required=True, help='Full, already committed main-project SHA.')
    parser.add_argument('--sdk-wheel', type=Path, required=True, help='Existing wheel matching the recipe checksum; never rebuilt here.')
    parser.add_argument('--output', type=Path, required=True, help='New local asset directory; existing output is never overwritten.')
    parser.add_argument('--release', action='store_true', help='Explicitly build a stable release recipe; no upload is performed.')
    args = parser.parse_args()
    manifest = build(args.lock, args.recipe, args.sources, args.base_commit, args.sdk_wheel,
                     args.output.resolve(), release_mode=args.release)
    print(json.dumps({'suite_version': manifest['suite_version'], 'skills': len(manifest['skills']),
                      'output': str(args.output.resolve()), 'status': manifest['status'],
                      'published': manifest['published'], 'uploaded': False}, ensure_ascii=False))


def check_main():
    parser = argparse.ArgumentParser(description='Check candidate or final Skill assets without fetching source or publishing.')
    parser.add_argument('directory', type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.directory), ensure_ascii=False, indent=2))


def guarded(main):
    try:
        main()
    except ReleaseError as error:
        raise SystemExit('Release error: ' + str(error)) from None
    except (OSError, ValueError, KeyError, TypeError, UnicodeError):
        raise SystemExit('Release error: invalid or unavailable input; private details suppressed.') from None
