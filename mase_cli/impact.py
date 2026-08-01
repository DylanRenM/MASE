"""Language-neutral impact-chain artifact policy and generated review views."""

from __future__ import annotations

import hashlib
import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence, Union

import yaml

from mase_cli.schema import GovernanceError, load_yaml_document, validate_payload
from mase_cli.config import framework_home


PathInput = Union[str, Path]
LEVEL_RANK = {"L1": 1, "L2": 2, "L3": 3}
LEVEL_GATES = {
    "L1": {
        "impact_analysis", "impact_reconcile", "related_tests", "contract_differential",
    },
    "L2": {
        "impact_analysis", "impact_reconcile", "related_tests", "contract_differential",
        "integration_tests", "impact_review", "code_review",
    },
    "L3": {
        "impact_analysis", "impact_reconcile", "related_tests", "contract_differential",
        "integration_tests", "impact_review", "code_review", "architecture_review",
        "full_chain_smoke", "rollback_verification",
    },
}
IMPACT_GATES = frozenset().union(*LEVEL_GATES.values())
RESOLVED_ARCHITECTURE_DECISIONS = {
    "version-isolation", "feature-flag", "split-change", "terminate",
}


@dataclass(frozen=True)
class ImpactAssessment:
    applicability: str
    level: str
    required_gates: tuple[str, ...]
    caller_count: int
    boundary_count: int
    architecture_review_required: bool
    decision: str
    reconciliation: str
    diagnostics: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "applicability": self.applicability,
            "level": self.level,
            "required_gates": list(self.required_gates),
            "caller_count": self.caller_count,
            "boundary_count": self.boundary_count,
            "architecture_review_required": self.architecture_review_required,
            "decision": self.decision,
            "reconciliation": self.reconciliation,
            "diagnostics": list(self.diagnostics),
        }


@dataclass(frozen=True)
class ImpactStatus:
    change: str
    artifact: str
    digest: str
    level: str
    decision: str
    reconciliation: str
    caller_count: int
    boundary_count: int
    required_gates: tuple[str, ...]
    consistent: bool
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "change": self.change,
            "artifact": self.artifact,
            "digest": self.digest,
            "level": self.level,
            "decision": self.decision,
            "reconciliation": self.reconciliation,
            "caller_count": self.caller_count,
            "boundary_count": self.boundary_count,
            "required_gates": list(self.required_gates),
            "consistent": self.consistent,
            "issues": list(self.issues),
        }


def file_digest(path: PathInput) -> str:
    source = Path(path)
    return "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()


def classify_change(kind: str, *, machine_consumed: bool = False) -> dict[str, str]:
    normalized = str(kind).strip().lower().replace("-", "_")
    exemptions = {
        "comments": "comments",
        "formatting": "formatting",
        "non_machine_wording": "non_machine_wording",
        "log_wording": "non_machine_wording",
    }
    if normalized in exemptions and not machine_consumed:
        return {"applicability": "exempt", "exemption_kind": exemptions[normalized]}
    return {"applicability": "required", "reason": "historical_behavior_or_contract_change"}


def apply_classification(
    change_dir: PathInput,
    kind: str,
    *,
    machine_consumed: bool = False,
    baseline: str = "pending",
    diff_digest: str = "pending",
) -> dict[str, str]:
    change = Path(change_dir).expanduser().resolve()
    state_path, state = _state_payload(change)
    result = classify_change(kind, machine_consumed=machine_consumed)
    if result["applicability"] == "exempt":
        state["impact_analysis"] = {
            "applicability": "exempt",
            "exemption": {
                "kind": result["exemption_kind"],
                "evidence": f"mase impact classify {kind}",
            },
            "reconciliation": "exempt",
        }
    else:
        artifact = change / "impact-analysis.yaml"
        if not artifact.exists():
            template = framework_home() / "templates" / "impact-analysis.yaml"
            payload = load_yaml_document(template)
            payload["comparison"]["baseline"] = str(baseline)
            payload["comparison"]["diff_digest"] = str(diff_digest)
            _atomic_yaml(artifact, payload)
        state["impact_analysis"] = {
            "applicability": "required",
            "level": "L2",
            "decision": "proceed",
            "artifact": "impact-analysis.yaml",
            "artifact_digest": file_digest(artifact),
            "baseline_digest": str(baseline),
            "diff_digest": str(diff_digest),
            "reconciliation": "pending",
        }
        result = {**result, "artifact": "impact-analysis.yaml"}
    _atomic_yaml(state_path, state)
    return result


def _unique_first_party_callers(payload: Mapping[str, Any]) -> int:
    return len({
        (str(item.get("path", "")), str(item.get("symbol", "")))
        for item in payload.get("callers", [])
        if bool(item.get("first_party", False))
    })


def _unique_boundaries(payload: Mapping[str, Any]) -> int:
    return len({
        (str(item.get("kind", "")), str(item.get("path", "")))
        for item in payload.get("boundaries", [])
    })


def assess_impact(payload: Mapping[str, Any]) -> ImpactAssessment:
    applicability = str(payload.get("applicability", "required"))
    if applicability == "exempt":
        return ImpactAssessment("exempt", "", (), 0, 0, False, "exempt", "exempt", ())

    diagnostics: list[str] = []
    computed_rank = 1
    change_points = list(payload.get("change_points", []))
    implicit_channels = list(payload.get("implicit_channels", []))
    terminations = list(payload.get("terminations", []))
    adapter = dict(payload.get("adapter", {}))
    call_graph = dict(payload.get("call_graph", {}))
    effect_budget = dict(payload.get("effect_budget", {}))
    caller_count = _unique_first_party_callers(payload)
    boundary_count = _unique_boundaries(payload)

    semantic_change_types = {
        "external_contract", "business_semantics", "configuration", "serialization",
        "persistence", "deletion", "rename", "replacement", "reroute",
    }
    if any(
        str(item.get("change_type")) in semantic_change_types
        or not bool(item.get("semantics_preserved", True))
        or not bool(item.get("side_effects_preserved", True))
        for item in change_points
    ):
        computed_rank = 3
        diagnostics.append("contract_or_semantic_change")
    if boundary_count:
        computed_rank = 3
        diagnostics.append("system_boundary_affected")

    if any(
        bool(item.get("core_path", False))
        or str(item.get("call_frequency", "unknown")) != "low"
        for item in change_points
    ):
        computed_rank = max(computed_rank, 2)
        diagnostics.append("core_or_non_low_frequency")
    if str(adapter.get("confidence", "low")) != "high":
        computed_rank = max(computed_rank, 2)
        diagnostics.append("analysis_confidence_not_high")
    if call_graph and str(call_graph.get("status", "unverified")) != "verified":
        computed_rank = max(computed_rank, 2)
        diagnostics.append("call_graph_diff_unverified")
    if effect_budget and str(effect_budget.get("status", "unverified")) != "verified":
        computed_rank = max(computed_rank, 2)
        diagnostics.append("effect_budget_unverified")
    if any(str(item.get("status")) in {"discovered", "unverified", "outside_repository"} for item in implicit_channels):
        computed_rank = max(computed_rank, 2)
        diagnostics.append("implicit_dependency_or_uncertainty")

    depth_limit = any(str(item.get("reason")) == "depth_limit" for item in terminations)
    uncontrolled = any(str(item.get("risk")) == "uncontrolled" for item in implicit_channels)
    architecture_required = False
    if caller_count > 10:
        architecture_required = True
        computed_rank = 3
        diagnostics.append("caller_threshold_exceeded")
    if boundary_count >= 3:
        architecture_required = True
        computed_rank = 3
        diagnostics.append("boundary_threshold_reached")
    if depth_limit:
        architecture_required = True
        computed_rank = max(computed_rank, 2)
        diagnostics.append("depth_limit_unresolved")
    if uncontrolled:
        architecture_required = True
        computed_rank = max(computed_rank, 2)
        diagnostics.append("uncontrolled_hidden_dependency")

    computed_level = f"L{computed_rank}"
    declared_level = str(dict(payload.get("classification", {})).get("level", computed_level))
    if declared_level not in LEVEL_RANK:
        declared_level = computed_level
    effective_level = declared_level if LEVEL_RANK[declared_level] >= computed_rank else computed_level
    decision = str(dict(payload.get("decision", {})).get("status", "proceed"))
    reconciliation = str(dict(payload.get("reconciliation", {})).get("status", "pending"))
    return ImpactAssessment(
        applicability,
        effective_level,
        tuple(sorted(LEVEL_GATES[effective_level])),
        caller_count,
        boundary_count,
        architecture_required,
        decision,
        reconciliation,
        tuple(dict.fromkeys(diagnostics)),
    )


def _validate_impact_policy(payload: Mapping[str, Any], path: Path) -> ImpactAssessment:
    assessment = assess_impact(payload)
    if assessment.applicability == "exempt":
        return assessment
    declared = str(dict(payload.get("classification", {})).get("level", ""))
    if LEVEL_RANK.get(declared, 0) < LEVEL_RANK[assessment.level]:
        raise GovernanceError(
            f"classification.level {declared or '<missing>'} cannot be lower than computed {assessment.level}",
            path=path,
            code="policy",
        )
    reconciliation = dict(payload.get("reconciliation", {}))
    actual_paths = [str(item) for item in reconciliation.get("actual_paths", [])]
    forbidden_paths = [str(item) for item in payload.get("forbidden_paths", [])]
    forbidden_hits = sorted({
        actual
        for actual in actual_paths
        if any(fnmatch.fnmatch(actual, pattern) for pattern in forbidden_paths)
    })
    if forbidden_hits:
        raise GovernanceError(
            "actual paths enter forbidden change scope: " + ", ".join(forbidden_hits),
            path=path,
            code="blocked",
        )

    call_graph = dict(payload.get("call_graph", {}))
    if call_graph:
        def edge_key(item: Mapping[str, Any]) -> tuple[str, str, str, str]:
            return (
                str(item.get("operation", "")),
                str(item.get("caller", "")),
                str(item.get("callee", "")),
                str(item.get("via", "")),
            )

        planned = {edge_key(item) for item in call_graph.get("planned_changes", [])}
        actual = {edge_key(item) for item in call_graph.get("actual_changes", [])}
        reported = {edge_key(item) for item in call_graph.get("unplanned_changes", [])}
        computed_unplanned = actual - planned
        if reported != computed_unplanned:
            raise GovernanceError(
                "call_graph.unplanned_changes does not match actual minus planned edges",
                path=path,
                code="policy",
            )
        if computed_unplanned:
            raise GovernanceError(
                "unplanned call-graph edge changes require scope reconciliation",
                path=path,
                code="blocked",
            )

    protected_tests = dict(payload.get("protected_tests", {}))
    for change in protected_tests.get("changes", []):
        if not str(change.get("approval", "")).strip():
            raise GovernanceError(
                "protected test change requires approval: "
                + str(change.get("selector", "<unknown>")),
                path=path,
                code="blocked",
            )

    effect_budget = dict(payload.get("effect_budget", {}))
    observed_extra = [str(item) for item in effect_budget.get("observed_extra", [])]
    if observed_extra:
        raise GovernanceError(
            "observed effects exceed declared budget: " + ", ".join(observed_extra),
            path=path,
            code="blocked",
        )

    declaration = dict(payload.get("change_declaration", {}))
    undeclared_scope = [
        str(item)
        for field in ("incidental_changes", "non_spec_changes")
        for item in declaration.get(field, [])
    ]
    if undeclared_scope and not dict(payload.get("decision", {})).get("approval"):
        raise GovernanceError(
            "incidental or non-Spec changes require human disposition",
            path=path,
            code="blocked",
        )
    if assessment.architecture_review_required:
        decision = dict(payload.get("decision", {}))
        status = str(decision.get("status", ""))
        if status == "proceed":
            raise GovernanceError(
                "excessive impact scope cannot proceed without architecture disposition",
                path=path,
                code="blocked",
            )
        if status in RESOLVED_ARCHITECTURE_DECISIONS and not decision.get("approval"):
            raise GovernanceError(
                "resolved architecture decision requires human approval",
                path=path,
                code="blocked",
            )
    return assessment


def load_impact_analysis(path: PathInput) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    payload = load_yaml_document(source)
    validate_payload(payload, "mase-impact-analysis.schema.json", path=source)
    _validate_impact_policy(payload, source)
    return payload


def load_impact_scan(path: PathInput) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    payload = load_yaml_document(source)
    validate_payload(payload, "mase-impact-scan.schema.json", path=source)
    return payload


def _inside(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise GovernanceError("impact artifact path escapes change directory", path=candidate, code="path") from exc
    return candidate


def _state_payload(change: Path) -> tuple[Path, dict[str, Any]]:
    state_path = change / "mase-state.yaml"
    return state_path, load_yaml_document(state_path)


def _impact_artifact(change: Path, state: Mapping[str, Any]) -> Path:
    summary = state.get("impact_analysis", {})
    relative = str(summary.get("artifact", "impact-analysis.yaml"))
    return _inside(change, relative)


def _project_root(change: Path) -> Path:
    if change.parent.name != "changes" or change.parent.parent.name != "openspec":
        raise GovernanceError(
            "impact change must be inside openspec/changes",
            path=change,
            code="path",
        )
    return change.parents[2]


def impact_status(change_dir: PathInput) -> ImpactStatus:
    change = Path(change_dir).expanduser().resolve()
    state_path, state = _state_payload(change)
    summary = dict(state.get("impact_analysis", {}))
    if not summary:
        raise GovernanceError("impact_analysis summary is not declared", path=state_path, code="not_found")
    if summary.get("applicability") == "exempt":
        return ImpactStatus(change.name, "", "", "", "exempt", "exempt", 0, 0, (), True, ())
    artifact = _impact_artifact(change, state)
    payload = load_impact_analysis(artifact)
    assessment = assess_impact(payload)
    digest = file_digest(artifact)
    issues: list[str] = []
    expected_digest = str(summary.get("artifact_digest", ""))
    if expected_digest != digest:
        issues.append("impact artifact digest does not match state")
    comparisons = {
        "level": assessment.level,
        "decision": assessment.decision,
        "reconciliation": assessment.reconciliation,
    }
    for field, actual in comparisons.items():
        if str(summary.get(field, "")) != actual:
            issues.append(f"state {field} does not match impact artifact")
    reconciliation = dict(payload.get("reconciliation", {}))
    if assessment.reconciliation == "matched":
        from mase_cli.evidence import path_digest

        expected_diff_digest = str(reconciliation.get("actual_diff_digest", ""))
        current_diff_digest = path_digest(
            _project_root(change),
            [str(item) for item in reconciliation.get("actual_paths", [])],
        )
        if current_diff_digest != expected_diff_digest:
            issues.append("actual diff digest is stale for reconciled paths")
        if str(summary.get("diff_digest", "")) != expected_diff_digest:
            issues.append("state diff_digest does not match reconciled actual diff")
    return ImpactStatus(
        change.name,
        artifact.relative_to(change).as_posix(),
        digest,
        assessment.level,
        assessment.decision,
        assessment.reconciliation,
        assessment.caller_count,
        assessment.boundary_count,
        assessment.required_gates,
        not issues,
        tuple(issues),
    )


def _atomic_yaml(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        yaml.safe_dump(dict(payload), sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    temporary.replace(path)


def reconcile_impact(
    change_dir: PathInput,
    *,
    actual_paths: Sequence[str],
    actual_diff_digest: str,
    actual_symbols: Sequence[str] = (),
) -> ImpactStatus:
    change = Path(change_dir).expanduser().resolve()
    state_path, state = _state_payload(change)
    artifact = _impact_artifact(change, state)
    payload = load_impact_analysis(artifact)
    if payload.get("applicability") == "exempt":
        raise GovernanceError("exempt impact analysis cannot be reconciled", path=artifact, code="conflict")
    planned = {
        str(item) for item in payload.get("approved_paths", [])
    } or {str(item.get("path")) for item in payload.get("change_points", [])}
    planned_symbols = {
        str(item) for item in payload.get("approved_symbols", [])
    } or {
        f"{item.get('path')}:{item.get('symbol')}"
        for item in payload.get("change_points", [])
    }
    actual = tuple(dict.fromkeys(str(item) for item in actual_paths))
    realized_symbols = tuple(dict.fromkeys(str(item) for item in actual_symbols))
    from mase_cli.evidence import path_digest

    current_diff_digest = path_digest(_project_root(change), actual)
    if str(actual_diff_digest) != current_diff_digest:
        raise GovernanceError(
            "actual diff digest does not match current reconciled paths",
            path=artifact,
            code="stale",
        )
    unplanned = tuple(sorted(set(actual) - planned))
    unplanned_symbols = tuple(sorted(set(realized_symbols) - planned_symbols))
    reconciliation = dict(payload.get("reconciliation", {}))
    reconciliation.update({
        "status": "expanded" if unplanned or unplanned_symbols else "matched",
        "actual_diff_digest": current_diff_digest,
        "actual_paths": list(actual),
        "unplanned_paths": list(unplanned),
        "actual_symbols": list(realized_symbols),
        "unplanned_symbols": list(unplanned_symbols),
    })
    payload["reconciliation"] = reconciliation
    _atomic_yaml(artifact, payload)

    assessment = assess_impact(payload)
    summary = dict(state.get("impact_analysis", {}))
    summary.update({
        "level": assessment.level,
        "decision": assessment.decision,
        "artifact_digest": file_digest(artifact),
        "diff_digest": current_diff_digest,
        "reconciliation": reconciliation["status"],
    })
    state["impact_analysis"] = summary
    _atomic_yaml(state_path, state)
    return impact_status(change)


def _bullet(items: Sequence[Any], empty: str = "无") -> str:
    values = [str(item) for item in items]
    return "\n".join(f"- {item}" for item in values) if values else f"- {empty}"


def _atomic_text(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def render_impact_views(change_dir: PathInput) -> tuple[Path, Path, Path]:
    change = Path(change_dir).expanduser().resolve()
    state_path, state = _state_payload(change)
    artifact = _impact_artifact(change, state)
    payload = load_impact_analysis(artifact)
    assessment = assess_impact(payload)
    digest = file_digest(artifact)
    digest_line = f"> Source digest: `{digest}`"
    change_points = [
        f"{item.get('path')}::{item.get('symbol')}（{item.get('change_type')}）"
        for item in payload.get("change_points", [])
    ]
    callers = [
        f"L{item.get('depth')} · {item.get('path')}::{item.get('symbol')}"
        for item in payload.get("callers", [])
    ]
    implicit = [
        f"{item.get('kind')}: {item.get('status')} / {item.get('risk')}"
        for item in payload.get("implicit_channels", [])
    ]
    terminations = [
        f"{item.get('branch')}: {item.get('reason')}（深度 {item.get('depth')}）"
        for item in payload.get("terminations", [])
    ]
    call_graph = dict(payload.get("call_graph", {}))
    edge_changes = [
        f"{item.get('operation')} · {item.get('caller')} → {item.get('callee')}（{item.get('via')}）"
        for item in call_graph.get("actual_changes", [])
    ]
    declaration = dict(payload.get("change_declaration", {}))
    impact_scope = (
        "# 影响范围说明书\n\n"
        f"{digest_line}\n\n"
        f"- 影响等级：{assessment.level or '豁免'}\n"
        f"- 决策：{assessment.decision}\n"
        f"- 第一方调用方：{assessment.caller_count}\n"
        f"- 系统边界：{assessment.boundary_count}\n\n"
        "## 修改点\n\n" + _bullet(change_points) + "\n\n"
        "## 批准的文件与符号边界\n\n"
        + _bullet(payload.get("approved_paths", [])) + "\n\n"
        + _bullet(payload.get("approved_symbols", [])) + "\n\n"
        "## 受保护不变量\n\n" + _bullet(payload.get("protected_invariants", [])) + "\n\n"
        "## 受影响调用方\n\n" + _bullet(callers) + "\n\n"
        f"## 调用图差异（{call_graph.get('status', '未声明')}）\n\n"
        + _bullet(edge_changes) + "\n\n"
        "## 实现变更声明\n\n"
        "### Spec 内变更\n\n" + _bullet(declaration.get("spec_changes", [])) + "\n\n"
        "### 附带/非 Spec 变更\n\n"
        + _bullet([
            *declaration.get("incidental_changes", []),
            *declaration.get("non_spec_changes", []),
        ]) + "\n\n"
        "## 隐性依赖通道\n\n" + _bullet(implicit) + "\n\n"
        "## 递归终止\n\n" + _bullet(terminations) + "\n\n"
        "## 诊断与剩余风险\n\n"
        + _bullet([*assessment.diagnostics, *payload.get("residual_risks", [])]) + "\n"
    )
    verification = dict(payload.get("verification", {}))
    protected_tests = dict(payload.get("protected_tests", {}))
    effect_budget = dict(payload.get("effect_budget", {}))
    allowed_effects = dict(effect_budget.get("allowed", {}))
    allowed_effect_lines = [
        f"{kind}: {value}"
        for kind, values in allowed_effects.items()
        for value in values
    ]
    test_scope = (
        "# 测试范围确认单\n\n"
        f"{digest_line}\n\n"
        "## 测试类型\n\n" + _bullet(verification.get("test_types", [])) + "\n\n"
        "## 测试选择\n\n" + _bullet(verification.get("tests", [])) + "\n\n"
        f"## 受保护历史测试（基线 {protected_tests.get('baseline', '未声明')}）\n\n"
        + _bullet(protected_tests.get("selectors", [])) + "\n\n"
        "## 数据来源\n\n" + _bullet(verification.get("fixture_sources", [])) + "\n\n"
        "## 允许差异\n\n" + _bullet(verification.get("expected_differences", []), "新旧结果必须一致") + "\n\n"
        f"## 副作用隔离\n\n{verification.get('side_effect_isolation', '未声明')}\n\n"
        f"## 副作用预算（{effect_budget.get('status', '未声明')}）\n\n"
        + _bullet(allowed_effect_lines) + "\n\n"
        "### 禁止与超额副作用\n\n"
        + _bullet([
            *effect_budget.get("forbidden", []),
            *effect_budget.get("observed_extra", []),
        ]) + "\n"
    )
    recovery = dict(payload.get("recovery", {}))
    rollback = (
        "# 回滚方案\n\n"
        f"{digest_line}\n\n"
        f"## 回退策略\n\n{recovery.get('strategy', '未声明')}\n\n"
        f"## 数据兼容性\n\n{recovery.get('data_compatibility', '未声明')}\n\n"
        "## 停止条件\n\n" + _bullet(recovery.get("stop_conditions", []), "按变更/发布计划执行") + "\n"
    )
    paths = (change / "impact-scope.md", change / "test-scope.md", change / "rollback.md")
    for path, content in zip(paths, (impact_scope, test_scope, rollback)):
        _atomic_text(path, content)
    return paths
