"""Install the bundled Skill without pip or network access."""
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path

SKILL_NAME = "linxsci-skills"
MARKER = ".linxsci-install.json"


def default_skills_dir():
    return Path.home() / ".agents" / "skills"


def install_skill(skills_dir=None, update=False):
    source = Path(__file__).resolve().parents[1]
    parent = Path(skills_dir).expanduser() if skills_dir else default_skills_dir()
    destination = parent / SKILL_NAME
    if destination.is_symlink():
        raise ValueError("目标 Skill 是符号链接，请选择其他安装目录。")
    existing = destination
    if existing.exists():
        if not update:
            raise ValueError("Skill 已存在。更新或迁移本工具安装的版本请使用 --update；自定义安装请先备份。")
        marker = existing / MARKER
        try:
            installed = json.loads(marker.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise ValueError("目标目录不是本安装工具管理的 Skill，请先备份或选择其他目录。") from None
        if not isinstance(installed, dict) or installed.get("name") != existing.name:
            raise ValueError("安装标记不匹配，请选择其他目录。")
    parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".linxsci-stage-", dir=parent))
    backup = None
    try:
        shutil.copytree(source, staging, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", MARKER))
        (staging / MARKER).write_text(json.dumps({"name": SKILL_NAME, "version": "0.3.0"}), encoding="utf-8")
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
