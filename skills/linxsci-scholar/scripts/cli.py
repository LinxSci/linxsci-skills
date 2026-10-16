#!/usr/bin/env python3
"""LinxSci 统一命令行入口，按能力分组。"""
import argparse
import sys

if __package__:
    from .scholar import VERSION, main as scholar_main
else:
    from scholar import VERSION, main as scholar_main

# Add a capability only after its command handler is implemented and packaged.
# Handlers receive their own argv and a display name for argparse help/errors.
CAPABILITIES = {
    "scholar": ("论文检索、阅读、引用和 PDF 解析", scholar_main),
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(prog="linxsci", description=__doc__)
    parser.add_argument("--version", action="version", version=VERSION)
    groups = parser.add_subparsers(dest="capability", title="可用能力")
    for name, (description, handler) in CAPABILITIES.items():
        groups.add_parser(name, help=description, add_help=False)
    if not argv:
        parser.print_help()
        return 0
    if argv[0] in CAPABILITIES:
        # Forward unchanged, including options before the action and negative queries.
        handler = CAPABILITIES[argv[0]][1]
        return handler(argv[1:], prog="linxsci " + argv[0])
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
