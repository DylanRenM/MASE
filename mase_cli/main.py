"""MASE v2 command-line entry point."""

import argparse
import json
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
from mase_cli.gates import (
    execute_defined_gate,
    freeze_candidate,
    load_gate_definitions,
    plan_change,
)
from mase_cli.context import build_context_plan
from mase_cli.impact import (
    apply_classification,
    classify_change,
    impact_status,
    load_impact_scan,
    reconcile_impact,
    render_impact_views,
)
from mase_cli.release import build_release_plan, load_release_context
from mase_cli.schema import GovernanceError
from mase_cli.state import inspect_change_status


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
    measure.add_argument("files", nargs="*")
    measure.add_argument("--input-tokens", type=int)
    measure.add_argument("--output-tokens", type=int)
    measure.add_argument("--cache-tokens", type=int)
    measure.add_argument("--usage-file")
    measure.add_argument("--tool-output-characters", type=int, default=0)
    measure.add_argument("--test-automation", action="store_true")
    measure.add_argument("--dir", "-d", default=".")
    measure.add_argument("--manual-regression-minutes", type=float)
    measure.add_argument("--manual-regression-source", default="")

    context = sub.add_parser("context", help="规划受预算和排除规则约束的 Agent 上下文")
    context_sub = context.add_subparsers(dest="context_command", required=True)
    context_plan = context_sub.add_parser("plan", help="生成当前 change 的上下文文件计划")
    context_plan.add_argument("--change", required=True)
    context_plan.add_argument("--dir", "-d", default=".")
    context_plan.add_argument("--read", action="append", default=[])
    context_plan.add_argument("--allow-excluded", action="store_true")
    _add_json(context_plan)

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
    gate_run.add_argument("--scope", default="change")
    gate_run.add_argument("--verbose", action="store_true", help="流式显示完整门禁输出")
    gate_run.add_argument("command_args", nargs="*")
    gate_manual = gate_sub.add_parser("manual", help="记录允许人工完成的门禁证据")
    gate_manual.add_argument("gate")
    gate_manual.add_argument("--change", required=True)
    gate_manual.add_argument("--dir", "-d", default=".")
    gate_manual.add_argument("--state")
    gate_manual.add_argument("--actor", required=True)
    gate_manual.add_argument("--subject", required=True)
    gate_manual.add_argument("--reference", required=True)
    gate_plan = gate_sub.add_parser("plan", help="按阶段显示可执行、可复用和延后的门禁")
    gate_plan.add_argument("--change", required=True)
    gate_plan.add_argument("--dir", "-d", default=".")
    _add_json(gate_plan)
    gate_freeze = gate_sub.add_parser("freeze", help="冻结最终候选版本")
    gate_freeze.add_argument("--change", required=True)
    gate_freeze.add_argument("--dir", "-d", default=".")
    _add_json(gate_freeze)

    release = sub.add_parser("release", help="校验并规划发布；不执行生产变更")
    release_sub = release.add_subparsers(dest="release_command", required=True)
    release_plan = release_sub.add_parser("plan", help="从发布上下文生成只读计划")
    release_plan.add_argument("--context", required=True)
    release_plan.add_argument("--date", help="固定计划日期以获得可复现输出")
    _add_json(release_plan)
    release_status = release_sub.add_parser("status", help="报告 change 的发布证据状态")
    release_status.add_argument("--change", required=True)
    release_status.add_argument("--dir", "-d", default=".")
    _add_json(release_status)

    impact = sub.add_parser("impact", help="校验、复扫并生成影响链分析产物")
    impact_sub = impact.add_subparsers(dest="impact_command", required=True)
    impact_classify = impact_sub.add_parser("classify", help="判定历史变更是否需要影响分析")
    impact_classify.add_argument(
        "kind",
        help="comments/formatting/non-machine-wording/log-wording/runtime/contract 等",
    )
    impact_classify.add_argument("--machine-consumed", action="store_true")
    impact_classify.add_argument("--change")
    impact_classify.add_argument("--dir", "-d", default=".")
    impact_classify.add_argument("--baseline", default="pending")
    impact_classify.add_argument("--diff-digest", default="pending")
    _add_json(impact_classify)
    for command_name, help_text in (
        ("validate", "校验影响分析 Schema、策略与状态绑定"),
        ("status", "报告影响等级、范围、决策和复扫状态"),
        ("render", "生成影响范围、测试范围和回滚文档"),
    ):
        command = impact_sub.add_parser(command_name, help=help_text)
        command.add_argument("--change", required=True)
        command.add_argument("--dir", "-d", default=".")
        command.add_argument("--require-matched", action="store_true")
        _add_json(command)
    impact_reconcile = impact_sub.add_parser("reconcile", help="按实际差异复扫计划范围")
    impact_reconcile.add_argument("--change", required=True)
    impact_reconcile.add_argument("--dir", "-d", default=".")
    impact_reconcile.add_argument("--actual-path", action="append", required=True)
    impact_reconcile.add_argument("--actual-diff-digest", required=True)
    _add_json(impact_reconcile)
    impact_scan = impact_sub.add_parser("scan", help="校验语言适配器的标准扫描结果")
    impact_scan.add_argument("--input", required=True)
    _add_json(impact_scan)

    return parser


def _state_path(args):
    from pathlib import Path

    root = Path(args.dir).expanduser().resolve()
    if Path(args.change).name != args.change or args.change in {".", ".."}:
        raise GovernanceError("change name must be a single safe path component", code="invalid_name")
    if getattr(args, "state", None):
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
        if args.test_automation:
            report = metrics.collect_test_automation_metrics(
                args.dir,
                manual_regression_minutes=args.manual_regression_minutes,
                manual_regression_source=args.manual_regression_source,
            )
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return report
        if not args.files:
            raise ValueError("metrics requires files unless --test-automation is used")
        supplied = (args.input_tokens, args.output_tokens, args.cache_tokens)
        token_usage = None
        if any(value is not None for value in supplied):
            token_usage = {
                "input": args.input_tokens or 0,
                "output": args.output_tokens or 0,
                "cache": args.cache_tokens or 0,
            }
        return metrics.run(
            args.files,
            token_usage,
            usage_file=args.usage_file,
            tool_output_characters=args.tool_output_characters,
        )
    elif args.command == "context":
        report = build_context_plan(
            args.dir,
            args.change,
            explicit_reads=args.read,
            allow_excluded=args.allow_excluded,
        )
        if args.json:
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(
                f"Context plan: {report.change} · profile={report.profile} · "
                f"files={len(report.included)} · characters={report.characters}"
            )
            for item in report.included:
                suffix = " [override]" if item.override else ""
                print(f"  + {item.path}: {item.reason}{suffix}")
            for item in report.excluded:
                print(f"  - {item.path}: {item.reason}")
            if report.over_budget:
                print(f"  ! context proxy budget exceeded: {', '.join(report.budget_reasons)}")
        return report
    elif args.command == "update":
        return update_project.run(args)
    elif args.command == "install":
        return install_framework.run(args)
    elif args.command == "release":
        if args.release_command == "plan":
            report = build_release_plan(
                load_release_context(args.context), generated_on=args.date
            )
            if args.json:
                print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
            else:
                print(report.to_markdown(), end="")
            return report
        from pathlib import Path

        root = Path(args.dir).expanduser().resolve()
        if Path(args.change).name != args.change or args.change in {".", ".."}:
            raise GovernanceError(
                "change name must be a single safe path component", code="invalid_name"
            )
        report = inspect_change_status(root / "openspec" / "changes" / args.change)
        payload = {
            "change": report.change,
            "release": report.release,
            "release_outcome": report.release_outcome,
            "required_gates": list(report.required_gates),
            "effective_gates": report.effective_gates,
            "issues": list(report.issues),
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(
                f"Release status: {report.change} · outcome={report.release_outcome}"
            )
            for gate in report.required_gates:
                if gate.startswith("release_"):
                    print(f"  {gate}: {report.effective_gates.get(gate, 'pending')}")
        return report
    elif args.command == "impact":
        if args.impact_command == "classify":
            if args.change:
                root, state_path = _state_path(args)
                payload = apply_classification(
                    state_path.parent,
                    args.kind,
                    machine_consumed=args.machine_consumed,
                    baseline=args.baseline,
                    diff_digest=args.diff_digest,
                )
            else:
                payload = classify_change(args.kind, machine_consumed=args.machine_consumed)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print(
                    f"impact classification: {payload['applicability']} · "
                    f"{payload.get('exemption_kind') or payload.get('reason')}"
                )
            return payload
        if args.impact_command == "scan":
            payload = load_impact_scan(args.input)
            report = {
                "adapter": payload["adapter"],
                "change_points": len(payload["change_points"]),
                "callers": len(payload["callers"]),
                "boundaries": len(payload["boundaries"]),
                "diagnostics": payload["diagnostics"],
            }
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print(
                    f"impact scan: adapter={payload['adapter']['name']} · "
                    f"change_points={report['change_points']} · callers={report['callers']} · "
                    f"boundaries={report['boundaries']}"
                )
            return report
        root, state_path = _state_path(args)
        change = state_path.parent
        if args.impact_command == "reconcile":
            report = reconcile_impact(
                change,
                actual_paths=args.actual_path,
                actual_diff_digest=args.actual_diff_digest,
            )
        elif args.impact_command == "render":
            paths = render_impact_views(change)
            payload = {
                "change": args.change,
                "views": [path.relative_to(root).as_posix() for path in paths],
            }
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print("generated impact views:")
                for path in payload["views"]:
                    print(f"  {path}")
            return payload
        else:
            report = impact_status(change)
        if getattr(args, "require_matched", False) and report.reconciliation != "matched":
            raise GovernanceError(
                f"impact reconciliation is {report.reconciliation}; matched is required",
                code="blocked",
            )
        if args.json:
            print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(
                f"Impact status: {report.change} · level={report.level or 'exempt'} · "
                f"decision={report.decision} · reconciliation={report.reconciliation}"
            )
            for issue in report.issues:
                print(f"  ! {issue}")
        if not report.consistent:
            raise SystemExit(EXIT_INCONSISTENT)
        return report
    elif args.command == "gate":
        root, state = _state_path(args)
        if args.gate_command == "run":
            command = list(args.command_args)
            if command and command[0] == "--":
                command.pop(0)
            definitions = load_gate_definitions(root, required=False)
            if definitions.legacy:
                print(
                    "mase: warning: .mase/gates.yaml missing; running in ad-hoc compatibility mode",
                    file=sys.stderr,
                )
                record = run_gate(
                    root, state, args.gate, command, args.input, args.artifact,
                    scope=args.scope,
                    stream_output=args.verbose,
                )
                reused = False
            else:
                execution = execute_defined_gate(
                    root,
                    args.change,
                    args.gate,
                    explicit_command=command or None,
                    explicit_inputs=args.input or None,
                    explicit_artifacts=args.artifact or None,
                    scope=args.scope,
                    stream_output=args.verbose,
                )
                record = execution.record
                reused = execution.reused
        elif args.gate_command == "manual":
            record = record_manual_evidence(
                state, args.gate, args.actor, args.subject, args.reference
            )
            reused = False
        elif args.gate_command == "plan":
            report = plan_change(root, args.change)
            if args.json:
                print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
            else:
                print(f"Gate plan: {report.change} · profile={report.profile}")
                for stage, checks in report.test_schedule.items():
                    print(f"  schedule {stage:10} {', '.join(checks)}")
                for instance in report.instances.values():
                    print(
                        f"  {instance.name:24} {instance.stage:10} "
                        f"{instance.status:10} {instance.reason}; next: {instance.next_action}"
                    )
                for diagnostic in report.diagnostics:
                    print(f"  ! {diagnostic.code}: {diagnostic.message}")
            return report
        else:
            candidate = freeze_candidate(root, args.change)
            if args.json:
                print(json.dumps({"candidate_id": candidate.id, **candidate.to_dict()}, ensure_ascii=False, indent=2))
            else:
                print(f"frozen candidate: {candidate.id}")
            return candidate
        suffix = " [cache hit]" if reused else ""
        print(
            f"{record.result}: {record.gate} ({record.kind}){suffix}; "
            f"duration={record.duration_seconds:.2f}s; log={record.log_path or '-'}"
        )
        if record.result != "passed" and record.log_path:
            log_path = root / record.log_path
            if log_path.is_file():
                excerpt = log_path.read_text(encoding="utf-8", errors="replace")[-4000:]
                print("--- bounded failure excerpt ---")
                print(excerpt)
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
