#!/usr/bin/env python3
"""Exercise extracted Skill assets using a temporary Python environment and no Git."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from skill_release import NAMES, check, encoded, guarded, json_bytes, require, zip_items


def unpack(data, destination):
    for name, (content, mode) in zip_items(data).items():
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        target.chmod(mode)


def smoke(directory):
    summary = check(directory)
    manifest = json_bytes((directory / 'release-manifest.json').read_bytes())
    require(sys.version_info >= (3, 10), 'All-Skill smoke checks require Python 3.10+.')
    checks = []
    with tempfile.TemporaryDirectory(prefix='linxsci-candidate-smoke-') as temp:
        root = Path(temp)
        environment = root / 'environment'
        result = subprocess.run([sys.executable, '-m', 'venv', str(environment)], capture_output=True, timeout=120)
        require(result.returncode == 0, 'Could not create isolated smoke environment.')
        binary = environment / ('Scripts' if os.name == 'nt' else 'bin')
        python = binary / ('python.exe' if os.name == 'nt' else 'python')
        cli = binary / ('linxsci.exe' if os.name == 'nt' else 'linxsci')
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(('LINXSCI_', 'PYTHON', 'PIP_'))}
        env.update({'PATH': str(binary), 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1',
                    'PIP_CONFIG_FILE': os.devnull, 'PIP_DISABLE_PIP_VERSION_CHECK': '1',
                    'LINXSCI_CONFIG_FILE': str(root / 'unused-config.json'),
                    'LINXSCI_SKILLS_DIR': str(root / 'installed')})
        require(shutil.which('git', path=env['PATH']) is None, 'Git must be absent from smoke PATH.')
        work = root / 'unrelated-directory'
        work.mkdir()

        def run(label, args):
            result = subprocess.run([str(arg) for arg in args], cwd=work, env=env,
                                    capture_output=True, text=True, timeout=60)
            require(result.returncode == 0, 'Smoke check failed: ' + label + '\n' + result.stderr[-1200:])
            checks.append(label)
            return result.stdout

        run('offline-sdk-wheel-install', [python, '-m', 'pip', 'install', '--no-index', '--no-deps',
                                         directory.resolve() / manifest['sdk']['artifact']['file']])
        location = run('installed-sdk-location', [python, '-c', 'import linxsci; print(linxsci.__file__)']).strip()
        require(Path(location).resolve().is_relative_to(environment.resolve()), 'Smoke imported a development SDK.')
        run('sdk-version', [cli, '--version'])
        for name, record in manifest['skills'].items():
            destination = root / 'installed' / name
            unpack((directory / record['artifact']['file']).read_bytes(), destination)
            run(name + '-single-help', [python, destination / record['entrypoint'], '--help'])
            if name != 'linxsci-base':
                run(name + '-dispatch-help', [cli, 'skill', name[len('linxsci-'):], '--help'])
        found = json.loads(run('all-extensions-discovered', [python, '-c',
            'import json; from linxsci.scripts import skill_dispatch; print(json.dumps(skill_dispatch.discover_skills()))']))
        require(set(found) == {name[len('linxsci-'):] for name in NAMES[1:]}, 'Wrong extracted extension set.')
        full = root / 'full'
        unpack((directory / manifest['bundles']['full']).read_bytes(), full)
        env['LINXSCI_SKILLS_DIR'] = str(full / 'skills')
        for name in NAMES[1:]:
            run(name + '-full-help', [cli, 'skill', name[len('linxsci-'):], '--help'])
        run('full-base-routes', [python, full / 'skills/linxsci-base/scripts/cli.py', 'routes'])
        source = root / 'source'
        unpack((directory / manifest['bundles']['source']).read_bytes(), source)
        snapshot = source / ('linxsci-skills-' + manifest['suite_version'] + '-source')
        env['LINXSCI_SKILLS_DIR'] = str(snapshot / 'skills')
        for name, record in manifest['skills'].items():
            run(name + '-source-help', [python, snapshot / 'skills' / name / record['entrypoint'], '--help'])
    return {**summary, 'smoke_checks': len(checks), 'checks': checks, 'git_available': False,
            'sdk_install_source': 'bundled wheel, offline', 'business_api_calls': 0,
            'limits': ['Help/discovery checks only; no research or content-production acceptance.',
                       'Third-party dependencies and external tools are not installed or exercised.',
                       'Package installation and Idea continuation are checked separately by verify_skill_installation.py.',
                       'This smoke run does not verify anonymous public downloads or SkillHub installation.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = smoke(args.directory)
    if args.report:
        require(not args.report.resolve().is_relative_to(args.directory.resolve()),
                'Keep verification reports outside immutable candidate assets.')
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_bytes(encoded(report))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    guarded(main)
