#!/usr/bin/env python3
"""User-facing installer for the downloadable bundle; no pip needed."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "skills/linxsci-base/scripts"))
from cli import main


def install(argv=None):
    parser = argparse.ArgumentParser(description="安装 linxsci-base 并配置已有 API Key")
    parser.add_argument("--skills-dir", help="可选的 Skill 安装父目录")
    parser.add_argument("--update", action="store_true", help="更新或迁移本工具管理的 Skill 到 linxsci-base，并保留备份")
    parser.add_argument("--no-config", action="store_true", help="仅安装，不运行配置向导")
    parser.add_argument("--online", action="store_true", help="向导默认使用线上地址")
    parser.add_argument("--base-url", help="向导默认的服务根地址")
    args = parser.parse_args(argv)
    command = ["install-skill"]
    if args.skills_dir:
        command += ["--skills-dir", args.skills_dir]
    if args.update:
        command += ["--update"]
    status = main(command)
    if status or args.no_config:
        return status
    command = ["setup"]
    if args.online:
        command += ["--online"]
    if args.base_url:
        command += ["--base-url", args.base_url]
    status = main(command)
    if status:
        print("linxsci-base 文件已安装；API 配置或连接检查尚未完成。"
              "可以继续查看扩展指南，需要论文服务时再让助手协助配置。", file=sys.stderr)
    return status


if __name__ == "__main__":
    if sys.version_info < (3, 9):
        print("请安装 Python 3.9 或更高版本后重试。", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(install())
