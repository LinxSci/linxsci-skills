#!/usr/bin/env python3
"""LinxSci 统一命令行入口，常用动作直接运行。"""
import sys

if __package__:
    from .commands import VERSION, build_parser, main as commands_main
else:
    from commands import VERSION, build_parser, main as commands_main

# Add a capability only after its command handler is implemented and packaged.
# Handlers receive their own argv and a display name for argparse help/errors.
CAPABILITIES = {}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in CAPABILITIES:
        # Forward unchanged, including options before the action and negative queries.
        handler = CAPABILITIES[argv[0]][1]
        return handler(argv[1:], prog="linxsci " + argv[0])
    if not argv or argv in (["--help"], ["-h"]):
        parser = build_parser(prog="linxsci")
        extra = [name + "：" + description for name, (description, _) in CAPABILITIES.items()]
        if extra:
            parser.epilog = "扩展能力：" + "；".join(extra)
        if not argv:
            parser.print_help()
            return 0
        parser.parse_args(argv)  # argparse prints help and exits successfully.
    return commands_main(argv, prog="linxsci")


if __name__ == "__main__":
    sys.exit(main())
