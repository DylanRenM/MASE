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
from mase_cli.evidence import record_manual_evidence, run_gate
from mase_cli.schema import GovernanceError


EXIT_INCONSISTENT = 1
EXIT_USAGE = 2
EXIT_CONFIG = 3
EXIT_NOT_FOUND = 4


def _add_json(parser):
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")


def build_parser():
    parser = argparse.ArgumentParser(prog="mase", description="MASE — adaptive AI software engineering")
    parser.add_argument("--version", action="version", version=f"MASE {__version__}")
    parser.add_argument("--debug", action="store_true", help="预期错误也输出 Python traceback")
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

    stat = sub.add_parser("status", help="读取单个 change 或多 change portfolio 状态")
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

    gate = sub.add_parser("gate", help="运行门禁或记录结构化人工证据")
    gate_sub = gate.add_subparsers(dest="gate_command", required=True)
    gate_run = gate_sub.add_parser("run", help="执行命令并原子记录自动证据")
    gate_run.add_argument("gate")
    gate_run.add_argument("--change", required=True)
    gate_run.add_argument("--dir", "-d", default=".")
    gate_run.add_argument("--state")
    gate_run.add_argument("--input", action="append", default=[])
    gate_run.add_argument("--artifact", action="append", default=[])
    gate_run.add_argument("command_args", nargs="*")
    gate_manual = gate_sub.add_parser("manual", help="记录允许人工完成的门禁证据")
    gate_manual.add_argument("gate")
    gate_manual.add_argument("--change", required=True)
    gate_manual.add_argument("--dir", "-d", default=".")
    gate_manual.add_argument("--state")
    gate_manual.add_argument("--actor", required=True)
    gate_manual.add_argument("--subject", required=True)
    gate_manual.add_argument("--reference", required=True)

    return parser


def _state_path(args):
    from pathlib import Path

    root = Path(args.dir).expanduser().resolve()
    if Path(args.change).name != args.change or args.change in {".", ".."}:
        raise GovernanceError("change name must be a single safe path component", code="invalid_name")
    if args.state:
        candidate = (root / args.state).resolve()
    else:
        candidate = root / "openspec" / "changes" / args.change / "mase-state.yaml"
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise GovernanceError("state path escapes project root", path=candidate, code="path") from exc
    return root, candidate


def _dispatch(args):
    if args.command == "init":
        return init_project.run(args)
    elif args.command == "check":
        report = check_project.run(args.dir, args.json)
        if not report.ok:
            raise SystemExit(EXIT_INCONSISTENT)
        return report
    elif args.command == "status":
        report = status.run(args.dir, args.change, args.json)
        if not report.consistent:
            raise SystemExit(EXIT_INCONSISTENT)
        return report
    elif args.command == "doctor":
        report = doctor.run(args.stack, args.json)
        if not report.ok:
            raise SystemExit(EXIT_INCONSISTENT)
        return report
    elif args.command == "metrics":
        supplied = (args.input_tokens, args.output_tokens, args.cache_tokens)
        token_usage = None
        if any(value is not None for value in supplied):
            token_usage = {
                "input": args.input_tokens or 0,
                "output": args.output_tokens or 0,
                "cache": args.cache_tokens or 0,
            }
        return metrics.run(args.files, token_usage)
    elif args.command == "update":
        return update_project.run(args)
    elif args.command == "install":
        return install_framework.run(args)
    elif args.command == "gate":
        root, state = _state_path(args)
        if args.gate_command == "run":
            command = list(args.command_args)
            if command and command[0] == "--":
                command.pop(0)
            record = run_gate(root, state, args.gate, command, args.input, args.artifact)
        else:
            record = record_manual_evidence(
                state, args.gate, args.actor, args.subject, args.reference
            )
        print(f"{record.result}: {record.gate} ({record.kind})")
        if record.result != "passed":
            raise SystemExit(EXIT_INCONSISTENT)
        return record
    else:
        build_parser().print_help()
        raise SystemExit(EXIT_USAGE)


def _expected_exit_code(exc: BaseException) -> int:
    if isinstance(exc, GovernanceError) and exc.code in {"not_found", "path", "invalid_name"}:
        return EXIT_NOT_FOUND
    if isinstance(exc, FileNotFoundError):
        return EXIT_NOT_FOUND
    return EXIT_CONFIG


def main(argv=None):
    parser = build_parser()
    raw_args = list(sys.argv[1:] if argv is None else argv)
    gate_command = None
    if "gate" in raw_args and "run" in raw_args and "--" in raw_args:
        separator = raw_args.index("--")
        gate_command = raw_args[separator + 1 :]
        raw_args = raw_args[:separator]
    args = parser.parse_args(raw_args)
    if gate_command is not None and args.command == "gate" and args.gate_command == "run":
        args.command_args = gate_command
    try:
        _dispatch(args)
        return 0
    except (GovernanceError, ValueError, FileNotFoundError, PermissionError) as exc:
        if args.debug:
            raise
        code = _expected_exit_code(exc)
        print(f"mase: error[{code}]: {exc}", file=sys.stderr)
        raise SystemExit(code)


if __name__ == "__main__":
    main()
