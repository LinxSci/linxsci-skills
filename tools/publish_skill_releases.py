#!/usr/bin/env python3
"""Plan a suite upload locally; explicit flags upload a draft or publish verified assets."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from skill_release import ReleaseError, check, guarded, json_bytes, require, sha256

REPOSITORY = 'LinxSci/linxsci-skills'
REQUIRED_CHECKS = {'offline-sdk-install', 'sdk-location', 'missing-before-install', 'wrong-suite-rejected',
                   'confirmation-required', 'http-404', 'http-timeout', 'http-interrupted', 'http-redirect',
                   'damaged-hash', 'damaged-size', 'damaged-corrupt', 'damaged-identity', 'damaged-malicious',
                   'publish-rollback', 'http-package-install', 'reuse-without-download', 'local-edits-preserved',
                   'incomplete-preserved', 'official-source-state', 'original-task-resumed',
                   'follow-up-resumed', 'evidence-reuse-without-survey'}


def plan(directory, installation_report, notes):
    directory = directory.resolve()
    summary = check(directory)
    require(summary['status'] == 'release' and summary['published'], 'Publication requires final release assets.')
    manifest_data = (directory / 'release-manifest.json').read_bytes()
    manifest = json_bytes(manifest_data)
    files = sorted(p.name for p in directory.iterdir())
    asset_hashes = {name: sha256((directory / name).read_bytes()) for name in files}
    report = json_bytes(installation_report.read_bytes())
    require(report.get('schema_version') == 1 and report.get('passed') is True and report.get('skips') == 0
            and report.get('manifest_sha256') == sha256(manifest_data)
            and report.get('assets_sha256') == asset_hashes
            and type(report.get('smoke_checks')) is int and report['smoke_checks'] >= 30
            and report.get('suite_version') == manifest['suite_version']
            and report.get('status') == 'release' and report.get('idea_from_single_zip') is True
            and report.get('git_available') is False, 'Missing or stale installation acceptance report.')
    checks = report.get('checks', [])
    require(isinstance(checks, list) and all(isinstance(row, dict) for row in checks)
            and REQUIRED_CHECKS <= {row.get('check') for row in checks}, 'Installation acceptance omitted required scenarios.')
    require(next(row for row in checks if row['check'] == 'official-source-state').get('exit') == 0,
            'Final assets did not pass the production source selection check.')
    require(notes.is_file() and notes.read_text(encoding='utf-8').strip(), 'Provide reviewed suite release notes.')
    tag = manifest['suite_tag']
    upload = ['gh', 'release', 'create', tag, *[str(directory / name) for name in files],
              '--repo', REPOSITORY, '--verify-tag', '--draft', '--title', 'LinxSci ' + tag,
              '--notes-file', str(notes.resolve())]
    publish = ['gh', 'release', 'edit', tag, '--repo', REPOSITORY, '--draft=false', '--latest=false']
    return {'repository': REPOSITORY, 'tag': tag, 'base_commit': manifest['sources']['linxsci-base'],
            'manifest_sha256': sha256(manifest_data),
            'files': asset_hashes,
            'upload_draft_argv': upload, 'publish_argv': publish,
            'network_accessed': False, 'uploaded': False, 'public_download_verified': False}


def run_gh(arguments):
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        raise ReleaseError('GitHub CLI is unavailable or timed out; inspect remote state before retrying.') from None
    require(result.returncode == 0, 'GitHub operation failed; inspect remote state. Existing assets were not overwritten.')
    return result.stdout


def verify_tag(value):
    actual = run_gh(['gh', 'api', 'repos/' + REPOSITORY + '/commits/' + value['tag'], '--jq', '.sha']).strip()
    require(actual == value['base_commit'], 'Suite tag does not resolve to the fixed main-project commit.')


def verify_remote_draft(value):
    record = json_bytes(run_gh(['gh', 'release', 'view', value['tag'], '--repo', REPOSITORY,
                               '--json', 'tagName,isDraft,assets']).encode())
    require(record.get('tagName') == value['tag'] and record.get('isDraft') is True,
            'Expected an existing draft. Published releases are never modified.')
    require({a.get('name') for a in record.get('assets', [])} == set(value['files']), 'Remote draft asset set differs.')
    with tempfile.TemporaryDirectory(prefix='linxsci-release-download-') as temp:
        root = Path(temp)
        run_gh(['gh', 'release', 'download', value['tag'], '--repo', REPOSITORY, '--dir', str(root)])
        require({p.name for p in root.iterdir()} == set(value['files']), 'Downloaded asset set differs.')
        require(all(not (root / name).is_symlink() and (root / name).is_file()
                    and sha256((root / name).read_bytes()) == digest for name, digest in value['files'].items()),
                'Remote draft bytes differ from locally validated assets.')
        check(root)


def execute(value, action):
    require(action in ('upload-draft', 'publish'), 'Unknown publication action.')
    verify_tag(value)
    if action == 'upload-draft':
        # gh release create rejects an existing release; no --clobber or replacement.
        run_gh(value['upload_draft_argv'])
        verify_remote_draft(value)
    else:
        verify_remote_draft(value)
        run_gh(value['publish_argv'])
    return {**value, 'network_accessed': True, 'uploaded': True,
            'draft': action == 'upload-draft', 'public_download_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--installation-report', type=Path, required=True)
    parser.add_argument('--notes-file', type=Path, required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--upload-draft', action='store_true', help='Upload a NEW draft, then download and verify its bytes.')
    action.add_argument('--publish', action='store_true', help='Verify an existing draft and publish it without changing SDK latest.')
    args = parser.parse_args()
    value = plan(args.directory, args.installation_report, args.notes_file)
    if args.upload_draft or args.publish:
        value = execute(value, 'upload-draft' if args.upload_draft else 'publish')
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    guarded(main)
