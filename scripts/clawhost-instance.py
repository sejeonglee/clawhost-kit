#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_POLL_INTERVAL_SECONDS = 300
DEFAULT_MAX_PARALLEL_TASKS = 1
DEFAULT_MAX_ACTIVE_WORKTREES = 2
DEFAULT_HOST_DEFAULTS_REF = "clawhost-default"
DEFAULT_BRANCH = "main"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def parse_repo_slug(repo_url: str) -> tuple[str, str]:
    https_match = re.match(r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/.]+?)(?:\.git)?/?$", repo_url)
    if https_match:
        return https_match.group('owner'), https_match.group('repo')

    ssh_match = re.match(r"git@github\.com:(?P<owner>[^/]+)/(?P<repo>[^/.]+?)(?:\.git)?$", repo_url)
    if ssh_match:
        return ssh_match.group('owner'), ssh_match.group('repo')

    parsed = urlparse(repo_url)
    if parsed.scheme and parsed.netloc == 'github.com':
        parts = [part for part in parsed.path.split('/') if part]
        if len(parts) >= 2:
            repo = parts[1][:-4] if parts[1].endswith('.git') else parts[1]
            return parts[0], repo

    raise SystemExit(f'Unsupported GitHub repo URL: {repo_url}')


def json_dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def json_load(path: Path) -> dict:
    return json.loads(path.read_text())


def instance_paths(instances_root: Path, name: str) -> dict[str, Path]:
    instance_root = instances_root / name
    return {
        'instance_root': instance_root,
        'config_dir': instance_root / 'config',
        'config_file': instance_root / 'config' / 'project-instance.json',
        'state_dir': instance_root / 'state',
        'runtime_file': instance_root / 'state' / 'runtime.json',
        'cursor_file': instance_root / 'state' / 'github-issue-cursor.json',
        'manual_brief_dir': instance_root / 'intake' / 'manual-briefs',
        'manual_brief_archive_dir': instance_root / 'intake' / 'manual-briefs-archive',
        'worktrees_dir': instance_root / 'worktrees',
        'logs_dir': instance_root / 'logs',
    }


def describe_instance_payload(paths: dict[str, Path]) -> dict:
    config = json_load(paths['config_file'])
    runtime = json_load(paths['runtime_file'])
    return {
        'instance_id': config['instance_id'],
        'status': runtime['status'],
        'host_defaults_ref': config['host_defaults_ref'],
        'repo': {
            'url': config['repo']['url'],
            'default_branch': config['repo']['default_branch'],
            'github_owner': config['repo']['github_owner'],
            'github_repo': config['repo']['github_repo'],
            'slug': config['repo']['slug'],
        },
        'paths': {
            'instance_root': str(paths['instance_root']),
            'config_file': str(paths['config_file']),
            'state_root': str(paths['state_dir']),
            'runtime_file': str(paths['runtime_file']),
            'cursor_file': str(paths['cursor_file']),
            'worktrees_root': config['paths']['worktrees_root'],
            'logs_root': config['paths']['logs_root'],
        },
        'intake': {
            'sources': list(config['intake']['sources']),
            'github_issue_polling': dict(config['intake']['github_issue_polling']),
            'manual_brief': dict(config['intake']['manual_brief']),
        },
        'runtime': {
            'updated_at': runtime['updated_at'],
            'started_at': runtime.get('started_at'),
            'poll_interval_seconds': config['poller']['interval_seconds'],
            'max_parallel_tasks': config['runtime_overrides']['max_parallel_tasks'],
            'max_active_worktrees': config['runtime_overrides']['max_active_worktrees'],
            'intake_sources': list(runtime['intake_sources']),
            'manual_brief_dir': config['intake']['manual_brief']['inbox_dir'],
            'cursor_path': config['poller']['cursor_file'],
        },
    }


def create_instance(args: argparse.Namespace) -> int:
    owner, repo = parse_repo_slug(args.repo_url)
    paths = instance_paths(args.instances_root, args.name)
    for key in ('config_dir', 'state_dir', 'manual_brief_dir', 'manual_brief_archive_dir', 'worktrees_dir', 'logs_dir'):
        paths[key].mkdir(parents=True, exist_ok=True)

    config = {
        'scope': 'project-instance',
        'instance_id': args.name,
        'created_at': utc_now(),
        'repo': {
            'url': args.repo_url,
            'default_branch': args.default_branch,
            'github_owner': owner,
            'github_repo': repo,
            'slug': f'{owner}/{repo}',
        },
        'paths': {
            'instance_root': str(paths['instance_root']),
            'state_root': str(paths['state_dir']),
            'worktrees_root': str(paths['worktrees_dir']),
            'logs_root': str(paths['logs_dir']),
        },
        'intake': {
            'sources': ['github_issue', 'manual_brief'],
            'github_issue_polling': {
                'enabled': True,
                'poll_interval_seconds': args.poll_interval_seconds,
            },
            'manual_brief': {
                'enabled': True,
                'inbox_dir': str(paths['manual_brief_dir']),
                'archive_dir': str(paths['manual_brief_archive_dir']),
            },
        },
        'poller': {
            'provider': 'github_issue',
            'interval_seconds': args.poll_interval_seconds,
            'cursor_file': str(paths['cursor_file']),
        },
        'host_defaults_ref': args.host_defaults_ref,
        'runtime_overrides': {
            'max_parallel_tasks': args.max_parallel_tasks,
            'max_active_worktrees': args.max_active_worktrees,
        },
        'env': {
            'workspace_name': args.name,
        },
    }
    json_dump(paths['config_file'], config)
    json_dump(paths['runtime_file'], {
        'status': 'created',
        'updated_at': utc_now(),
        'intake_sources': ['github_issue_polling', 'manual_brief'],
    })
    json_dump(paths['cursor_file'], {
        'repo_slug': f'{owner}/{repo}',
        'last_seen_issue_number': None,
        'updated_at': utc_now(),
    })

    print(json.dumps({
        'instance_id': args.name,
        'repo_url': args.repo_url,
        'instance_root': str(paths['instance_root']),
        'config_path': str(paths['config_file']),
        'runtime_path': str(paths['runtime_file']),
        'cursor_path': str(paths['cursor_file']),
        'manual_brief_dir': str(paths['manual_brief_dir']),
        'manual_brief_archive_dir': str(paths['manual_brief_archive_dir']),
        'worktrees_dir': str(paths['worktrees_dir']),
        'logs_dir': str(paths['logs_dir']),
        'host_defaults_ref': args.host_defaults_ref,
        'repo_slug': f'{owner}/{repo}',
        'status': 'created',
    }))
    return 0


def start_instance(args: argparse.Namespace) -> int:
    paths = instance_paths(args.instances_root, args.name)
    config = json_load(paths['config_file'])
    runtime = {
        'status': 'running',
        'started_at': utc_now(),
        'updated_at': utc_now(),
        'repo_slug': config['repo']['slug'],
        'poll_interval_seconds': config['poller']['interval_seconds'],
        'max_parallel_tasks': config['runtime_overrides']['max_parallel_tasks'],
        'max_active_worktrees': config['runtime_overrides']['max_active_worktrees'],
        'intake_sources': ['github_issue_polling', 'manual_brief'],
        'manual_brief_dir': config['intake']['manual_brief']['inbox_dir'],
        'cursor_path': config['poller']['cursor_file'],
    }
    json_dump(paths['runtime_file'], runtime)
    if not paths['cursor_file'].exists():
        json_dump(paths['cursor_file'], {
            'repo_slug': config['repo']['slug'],
            'last_seen_issue_number': None,
            'updated_at': utc_now(),
        })
    print(json.dumps(runtime))
    return 0


def status_instance(args: argparse.Namespace) -> int:
    paths = instance_paths(args.instances_root, args.name)
    detail = describe_instance_payload(paths)
    payload = {
        'instance_id': detail['instance_id'],
        'status': detail['status'],
        'repo_slug': detail['repo']['slug'],
        'repo_url': detail['repo']['url'],
        'poll_interval_seconds': detail['runtime']['poll_interval_seconds'],
        'max_parallel_tasks': detail['runtime']['max_parallel_tasks'],
        'max_active_worktrees': detail['runtime']['max_active_worktrees'],
        'manual_brief_dir': detail['intake']['manual_brief']['inbox_dir'],
        'cursor_path': detail['paths']['cursor_file'],
        'worktrees_dir': detail['paths']['worktrees_root'],
        'config_path': detail['paths']['config_file'],
        'runtime_path': detail['paths']['runtime_file'],
    }
    print(json.dumps(payload))
    return 0


def describe_instance(args: argparse.Namespace) -> int:
    paths = instance_paths(args.instances_root, args.name)
    print(json.dumps(describe_instance_payload(paths)))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Manage Clawhost project instances.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    create = subparsers.add_parser('create', help='Create a project instance from a repo URL.')
    create.add_argument('--instances-root', type=Path, required=True)
    create.add_argument('--name', required=True)
    create.add_argument('--repo-url', required=True)
    create.add_argument('--default-branch', default=DEFAULT_BRANCH)
    create.add_argument('--host-defaults-ref', default=DEFAULT_HOST_DEFAULTS_REF)
    create.add_argument('--poll-interval-seconds', type=int, default=DEFAULT_POLL_INTERVAL_SECONDS)
    create.add_argument('--max-parallel-tasks', type=int, default=DEFAULT_MAX_PARALLEL_TASKS)
    create.add_argument('--max-active-worktrees', type=int, default=DEFAULT_MAX_ACTIVE_WORKTREES)
    create.set_defaults(func=create_instance)

    start = subparsers.add_parser('start', help='Mark an instance running and materialize runtime state.')
    start.add_argument('--instances-root', type=Path, required=True)
    start.add_argument('--name', required=True)
    start.set_defaults(func=start_instance)

    status = subparsers.add_parser('status', help='Report instance status.')
    status.add_argument('--instances-root', type=Path, required=True)
    status.add_argument('--name', required=True)
    status.set_defaults(func=status_instance)

    describe = subparsers.add_parser('describe', help='Report the full instance surface for setup/automation.')
    describe.add_argument('--instances-root', type=Path, required=True)
    describe.add_argument('--name', required=True)
    describe.set_defaults(func=describe_instance)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
