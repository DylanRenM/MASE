"""MASE CLI — 麦哲思AI软件开发统一流程 命令行工具"""

import argparse
import sys
from mase_cli.commands import init_project, check_project


def main():
    parser = argparse.ArgumentParser(
        prog="mase",
        description="MASE — Measures AI Software Engineering CLI",
    )
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # --- mase init ---
    init_parser = sub.add_parser("init", help="初始化新项目")
    init_parser.add_argument("name", help="项目名称")
    init_parser.add_argument("--capabilities", "-c", nargs="+", default=["core"],
                             help="Capability 列表 (默认: core)")
    init_parser.add_argument("--package", "-p", required=True,
                             help="Python 包名 (snake_case)")
    init_parser.add_argument("--dir", "-d", default=".",
                             help="创建目录 (默认: 当前目录)")

    # --- mase check ---
    sub.add_parser("check", help="合规检查当前项目")

    # --- Parse ---
    args = parser.parse_args()

    if args.command == "init":
        init_project.run(args)
    elif args.command == "check":
        check_project.run()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
