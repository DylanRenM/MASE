"""MASE v2 command-line entry point."""

import argparse
import sys

from mase_cli import __version__
from mase_cli.commands import (
    check_project,
    doctor,
    init_project,
    install_framework,
    metrics,
    status,
    update_project,
)


def _add_json(parser):
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")


def build_parser():
    parser = argparse.ArgumentParser(prog="mase", description="MASE — adaptive AI software engineering")
    parser.add_argument("--version", action="version", version=f"MASE {__version__}")
    sub = parser.add_subparsers(dest="command", help="可用命令")

    init = sub.add_parser("init", help="初始化 Profile/stack 感知项目")
    init.add_argument("name")
    init.add_argument("--capabilities", "-c", nargs="+", default=["core"])
    init.add_argument("--package", "-p", help="Python 包名；旧 v1.3 参数保持兼容")
    init.add_argument("--stack", choices=("generic", "python", "swift"))
    init.add_argument("--profile", choices=("lite", "standard", "strict"), default="standard")
    init.add_argument("--dir", "-d", default=".")

    check = sub.add_parser("check", help="按 Profile 和 stack 执行合规检查")
    check.add_argument("--dir", "-d", default=".")
    _add_json(check)

    stat = sub.add_parser("status", help="读取唯一 change 状态并检查一致性")
    stat.add_argument("--change", "-c")
    stat.add_argument("--dir", "-d", default=".")
    _add_json(stat)

    doc = sub.add_parser("doctor", help="执行非修改式环境预检")
    doc.add_argument("--stack", choices=("generic", "python", "swift"), default="generic")
    _add_json(doc)

    measure = sub.add_parser("metrics", help="报告真实 Token 或明确标记的上下文代理值")
    measure.add_argument("files", nargs="+")
    measure.add_argument("--input-tokens", type=int)
    measure.add_argument("--output-tokens", type=int)
    measure.add_argument("--cache-tokens", type=int)

    update = sub.add_parser("update", help="预览或应用非破坏框架迁移")
    update.add_argument("--check", dest="check_only", action="store_true")
    update.add_argument("--dry-run", action="store_true")
    update.add_argument("--dir", "-d", default=".")

    install = sub.add_parser("install", help="按 manifest 安装框架运行时")
    install.add_argument("--source", help="MASE 源仓库；默认自动检测当前目录")
    install.add_argument("--destination")
    install.add_argument("--dry-run", action="store_true")

    return parser


def main():
    args = build_parser().parse_args()
    if args.command == "init":
        init_project.run(args)
    elif args.command == "check":
        report = check_project.run(args.dir, args.json)
        if not report.ok:
            raise SystemExit(1)
    elif args.command == "status":
        report = status.run(args.dir, args.change, args.json)
        if not report.consistent:
            raise SystemExit(1)
    elif args.command == "doctor":
        report = doctor.run(args.stack, args.json)
        if not report.ok:
            raise SystemExit(1)
    elif args.command == "metrics":
        supplied = (args.input_tokens, args.output_tokens, args.cache_tokens)
        token_usage = None
        if any(value is not None for value in supplied):
            token_usage = {
                "input": args.input_tokens or 0,
                "output": args.output_tokens or 0,
                "cache": args.cache_tokens or 0,
            }
        metrics.run(args.files, token_usage)
    elif args.command == "update":
        update_project.run(args)
    elif args.command == "install":
        install_framework.run(args)
    else:
        build_parser().print_help()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
