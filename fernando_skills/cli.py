from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, installer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fernando-skills",
        description="Install the spec-driven skills (/spec, /spec-impl) into an agent's config. Node-free fork of Klerith/fernando-skills.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser(
        "install",
        help="install the skills into an agent's config (run from the target repo)",
    )
    install_parser.add_argument("agent", choices=installer.AGENTS, help="target agent")
    install_parser.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        help=f"install into the user-level config (only {', '.join(installer.GLOBAL_AGENTS)})",
    )

    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="remove the skills previously installed into an agent's config",
    )
    uninstall_parser.add_argument("agent", choices=installer.AGENTS, help="target agent")
    uninstall_parser.add_argument(
        "--global",
        dest="global_install",
        action="store_true",
        help=f"uninstall from the user-level config (only {', '.join(installer.GLOBAL_AGENTS)})",
    )

    subparsers.add_parser("list", help="list the skills shipped in this package")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    target = Path.cwd()

    if args.command == "list":
        for line in installer.list_skills():
            print(line)
        return 0

    if args.global_install and args.agent not in installer.GLOBAL_AGENTS:
        print(
            f"error: --global is only supported for {', '.join(installer.GLOBAL_AGENTS)}.",
            file=sys.stderr,
        )
        return 2

    try:
        if args.command == "install":
            actions = installer.install(args.agent, target, args.global_install)
        else:
            actions = installer.uninstall(args.agent, target, args.global_install)
    except installer.InstallerError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    for action in actions:
        print(action)
    return 0


if __name__ == "__main__":
    sys.exit(main())
