#!/usr/bin/env python3
"""LinxSci 统一命令行入口，常用动作直接运行。"""
import sys

if __package__:
    from .commands import VERSION, build_parser, main as commands_main
    from .skill_dispatch import SkillDispatchError, discover_skills, run_skill
else:
    from commands import VERSION, build_parser, main as commands_main
    from skill_dispatch import SkillDispatchError, discover_skills, run_skill

# Add a capability only after its command handler is implemented and packaged.
# Handlers receive their own argv and a display name for argparse help/errors.
CAPABILITIES = {}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser(prog="linxsci", human_errors="--human-errors" in argv)
    root_help = not argv or argv in (["--help"], ["-h"])
    # Built-in commands and their global options retain their original parser.
    if not root_help and (argv[0] in parser.command_names or argv[0].startswith("-")):
        return commands_main(argv, prog="linxsci")
    if argv and argv[0] in CAPABILITIES:
        # Forward unchanged, including options before the action and negative queries.
        handler = CAPABILITIES[argv[0]][1]
        return handler(argv[1:], prog="linxsci " + argv[0])
    if root_help:
        extra = [name + "：" + description for name, (description, _) in CAPABILITIES.items()]
        try:
            extra += discover_skills(set(parser.command_names) | set(CAPABILITIES))
        except SkillDispatchError as error:
            parser.error(str(error))
        parser.epilog = "扩展 Skill 使用 linxsci <名称>；默认查找 ~/.agents/skills，可用 LINXSCI_SKILLS_DIR 指定父目录。"
        if extra:
            parser.epilog += " 已发现扩展：" + "；".join(extra)
        if not argv:
            parser.print_help()
            return 0
        parser.parse_args(argv)  # argparse prints help and exits successfully.
    try:
        return run_skill(argv[0], argv[1:])
    except SkillDispatchError as error:
        parser.error(str(error))


if __name__ == "__main__":
    sys.exit(main())
