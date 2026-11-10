"""Discover installed Skill folders and run their Python command entry points."""
import os
from pathlib import Path
import re
import subprocess
import sys

SKILLS_DIR_ENV = "LINXSCI_SKILLS_DIR"
COMMAND_NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*\Z")


class SkillDispatchError(ValueError):
    pass


def skills_directory():
    value = os.environ.get(SKILLS_DIR_ENV)
    try:
        directory = Path(value).expanduser() if value else Path.home() / ".agents" / "skills"
        if not directory.is_absolute() or "\x00" in str(directory):
            raise ValueError
        return directory
    except (ValueError, RuntimeError):
        raise SkillDispatchError("LINXSCI_SKILLS_DIR 必须是 Skill 父目录的绝对路径，可使用 ~。") from None


def entrypoint(directory, command):
    skill = directory / ("linxsci-" + command)
    return skill / "SKILL.md", skill / "scripts" / (command.replace("-", "_") + ".py")


def discover_skills(reserved=()):
    """List runnable folders without importing or executing their contents."""
    try:
        directory = skills_directory()
    except SkillDispatchError:
        if os.environ.get(SKILLS_DIR_ENV):
            raise
        # A minimal Windows environment may not provide a user home directory.
        # Optional discovery must not prevent access to the built-in CLI help.
        return []
    try:
        children = list(directory.iterdir())
    except FileNotFoundError:
        return []
    except OSError:
        raise SkillDispatchError("无法读取 Skill 父目录，请检查 LINXSCI_SKILLS_DIR 和目录访问权限。") from None
    commands = []
    for child in children:
        if not child.name.startswith("linxsci-"):
            continue
        command = child.name[len("linxsci-"):]
        if not COMMAND_NAME.fullmatch(command) or command in reserved:
            continue
        marker, script = entrypoint(directory, command)
        try:
            if marker.is_file() and script.is_file():
                commands.append(command)
        except OSError:
            # One inaccessible installation should not hide other available Skills.
            continue
    return sorted(commands)


def run_skill(command, argv):
    if not COMMAND_NAME.fullmatch(command):
        raise SkillDispatchError("Skill 命令名仅支持小写字母、数字和单个连字符分隔，例如 paper-qa。")
    marker, script = entrypoint(skills_directory(), command)
    try:
        if not marker.is_file():
            raise SkillDispatchError(
                "未找到 Skill linxsci-" + command + "。请将完整 Skill 放入 " + str(marker.parent.parent)
                + "，或用 LINXSCI_SKILLS_DIR 指定其父目录；Skill 根目录须有 SKILL.md。")
        if not script.is_file():
            raise SkillDispatchError("Skill 缺少可执行的 Python 入口：" + str(script))
        # Inherit stdin/stdout/stderr, configuration and the caller's directory.
        # A list of arguments avoids shell expansion of questions and file names.
        result = subprocess.run([sys.executable, str(script), *argv])
    except KeyboardInterrupt:
        return 130
    except OSError:
        raise SkillDispatchError("无法启动 Skill 脚本，请检查当前 Python 环境和文件访问权限。") from None
    # Convert a POSIX signal to the conventional shell exit status.
    return result.returncode if result.returncode >= 0 else 128 - result.returncode
