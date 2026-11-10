"""Install the bundled Skill without pip or network access."""
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path

SKILL_NAME = "linxsci-base"
LEGACY_SKILL_NAME = "linxsci-skills"
MARKER = ".linxsci-install.json"


def default_skills_dir():
    return Path.home() / ".agents" / "skills"


def install_skill(skills_dir=None, update=False):
    source = Path(__file__).resolve().parents[1]
    parent = Path(skills_dir).expanduser() if skills_dir else default_skills_dir()
    destination = parent / SKILL_NAME
    legacy = parent / LEGACY_SKILL_NAME
    for candidate in (destination, legacy):
        if candidate.is_symlink():
            raise ValueError(f"Skill 目录是符号链接：{candidate}。请使用原安装工具迁移，或选择其他安装目录。")
    if destination.exists() and legacy.exists():
        raise ValueError("linxsci-base 与 linxsci-skills 同时存在，未修改任何副本。请先通过各自原安装方式整理，避免重复发现。")
    existing = legacy if legacy.exists() else destination
    if existing == legacy and not update:
        raise ValueError("发现旧版 linxsci-skills。由本工具管理的副本请使用 --update 迁移到 linxsci-base；其他副本请使用原安装方式迁移。")
    if existing.exists():
        if not update:
            raise ValueError("Skill 已存在。更新或迁移本工具安装的版本请使用 --update；自定义安装请先备份。")
        marker = existing / MARKER
        try:
            if marker.is_symlink():
                raise ValueError("安装标记不能是符号链接。")
            installed = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise ValueError(f"无法确认 {existing} 由本安装工具管理。请使用原安装器迁移；手动安装请先备份并移出扫描目录，再安装新版。") from None
        if not isinstance(installed, dict) or installed.get("name") != existing.name:
            raise ValueError("安装标记不匹配，未修改已有目录。请使用原安装方式迁移或选择其他目录。")
    parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".linxsci-stage-", dir=parent))
    backup = None
    try:
        shutil.copytree(source, staging, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", MARKER))
        (staging / MARKER).write_text(json.dumps({"name": SKILL_NAME, "version": "0.3.4"}), encoding="utf-8")
        if existing.exists():
            backup_root = parent.parent / "linxsci-skill-backups"
            backup_root.mkdir(parents=True, exist_ok=True)
            backup = backup_root / (existing.name + ".backup-" + uuid.uuid4().hex[:8])
            os.replace(existing, backup)
        try:
            os.replace(staging, destination)
        except OSError:
            if backup:
                os.replace(backup, existing)
                backup = None
            raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return destination, backup
