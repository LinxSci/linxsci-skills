#!/usr/bin/env python3
"""User-facing installer for the downloadable bundle; no pip needed."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "skills/linxsci-scholar/scripts"))
from cli import main


def install(argv=None):
    parser = argparse.ArgumentParser(description="安装 LinxSci Scholar Skill 并配置已有 API Key")
    parser.add_argument("--skills-dir", help="可选的 Skill 安装父目录")
    parser.add_argument("--update", action="store_true", help="更新已有版本并保留备份")
    parser.add_argument("--no-config", action="store_true", help="仅安装，不运行配置向导")
    parser.add_argument("--online", action="store_true", help="向导默认使用线上地址")
    parser.add_argument("--base-url", help="向导默认的服务根地址")
    args = parser.parse_args(argv)
    command = ["scholar", "install-skill"]
    if args.skills_dir:
        command += ["--skills-dir", args.skills_dir]
    if args.update:
        command += ["--update"]
    status = main(command)
    if status or args.no_config:
        return status
    command = ["scholar", "setup"]
    if args.online:
        command += ["--online"]
    if args.base_url:
        command += ["--base-url", args.base_url]
    return main(command)


if __name__ == "__main__":
    if sys.version_info < (3, 9):
        print("请安装 Python 3.9 或更高版本后重试。", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(install())
