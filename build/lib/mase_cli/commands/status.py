"""mase status — single-change detail or resilient portfolio status."""

from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Optional, Union

from mase_cli.baseline import load_baseline
from mase_cli.schema import GovernanceError
from mase_cli.state import StatusReport, inspect_change_status


SAFE_CHANGE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
PHASE_RANK = {
    "draft": 0,
    "proposal": 1,
    "design": 2,
    "build": 3,
    "verify": 4,
    "retro": 5,
    "release": 6,
    "complete": 7,
    "archived": 8,
}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    change: str = ""
    path: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            key: value
            for key, value in (
                ("code", self.code),
                ("message", self.message),
                ("change", self.change),
                ("path", self.path),
            )
            if value
        }


@dataclass(frozen=True)
class PortfolioConflict:
    left: str
    right: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"left": self.left, "right": self.right, "reason": self.reason}


@dataclass(frozen=True)
class PortfolioReport:
    changes: tuple[StatusReport, ...]
    conflicts: tuple[PortfolioConflict, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    baseline_debt: int = 0
    expired_baseline: int = 0

    @property
    def consistent(self) -> bool:
        return (
            all(item.consistent for item in self.changes)
            and not self.conflicts
            and not self.diagnostics
            and self.expired_baseline == 0
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "consistent": self.consistent,
            "changes": [item.to_dict() for item in self.changes],
            "conflicts": [item.to_dict() for item in self.conflicts],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "baseline": {"debt": self.baseline_debt, "expired": self.expired_baseline},
        }


def _changes_root(root: Path) -> Path:
    return root / "openspec" / "changes"


def _select_change(root: Path, name: str) -> Path:
    if not SAFE_CHANGE.fullmatch(name) or name in {".", ".."}:
        raise ValueError("change name must be a single safe path component")
    change = _changes_root(root) / name
    if not change.is_dir():
        raise GovernanceError(f"change does not exist: {name}", path=change, code="not_found")
    return change


def _static_prefix(pattern: str) -> str:
    wildcard = min((pattern.find(char) for char in "*[?" if char in pattern), default=len(pattern))
    return pattern[:wildcard].rstrip("/")


def _paths_overlap(left: str, right: str) -> bool:
    if fnmatch.fnmatchcase(left, right) or fnmatch.fnmatchcase(right, left):
        return True
    left_prefix = _static_prefix(left)
    right_prefix = _static_prefix(right)
    if not left_prefix or not right_prefix:
        return True
    return (
        left_prefix == right_prefix
        or left_prefix.startswith(right_prefix + "/")
        or right_prefix.startswith(left_prefix + "/")
    )


def _dependency_issues(reports: dict[str, StatusReport]) -> dict[str, list[str]]:
    issues: dict[str, list[str]] = {name: [] for name in reports}
    graph: dict[str, list[str]] = {name: [] for name in reports}
    for name, report in reports.items():
        for dependency in report.dependencies:
            target_name = str(dependency.get("change", ""))
            required_phase = str(dependency.get("phase", "complete"))
            target = reports.get(target_name)
            if target is None:
                issues[name].append(f"dependency {target_name} is missing")
                continue
            graph[name].append(target_name)
            if PHASE_RANK.get(target.phase, -1) < PHASE_RANK.get(required_phase, 7):
                issues[name].append(
                    f"dependency {target_name} requires {required_phase} but is {target.phase}"
                )

    visited: set[str] = set()
    active: list[str] = []

    def visit(name: str) -> None:
        if name in active:
            cycle = active[active.index(name) :] + [name]
            message = "dependency cycle: " + " -> ".join(cycle)
            for member in set(cycle):
                if message not in issues[member]:
                    issues[member].append(message)
            return
        if name in visited:
            return
        active.append(name)
        for target in graph[name]:
            visit(target)
        active.pop()
        visited.add(name)

    for name in graph:
        visit(name)
    return issues


def _portfolio(root: Path) -> PortfolioReport:
    changes_root = _changes_root(root)
    if not changes_root.exists():
        return PortfolioReport(())
    reports: dict[str, StatusReport] = {}
    diagnostics: list[Diagnostic] = []
    for change in sorted(item for item in changes_root.iterdir() if item.is_dir()):
        state = change / "mase-state.yaml"
        if not state.exists():
            continue
        try:
            report = inspect_change_status(change)
        except (GovernanceError, ValueError, OSError) as exc:
            diagnostics.append(
                Diagnostic(
                    getattr(exc, "code", "invalid_state"),
                    str(exc),
                    change=change.name,
                    path=state.relative_to(root).as_posix(),
                )
            )
            continue
        if report.phase != "archived":
            reports[report.change] = report

    dependency_issues = _dependency_issues(reports)
    for name, extra in dependency_issues.items():
        if extra:
            current = reports[name]
            reports[name] = replace(
                current,
                consistent=False,
                issues=current.issues + tuple(extra),
            )

    conflicts: list[PortfolioConflict] = []
    names = sorted(reports)
    for index, left_name in enumerate(names):
        left = reports[left_name]
        for right_name in names[index + 1 :]:
            right = reports[right_name]
            explicit = right_name in left.conflicts_with or left_name in right.conflicts_with
            overlapping = any(
                _paths_overlap(left_path, right_path)
                for left_path in left.impact_paths
                for right_path in right.impact_paths
            )
            if explicit or overlapping:
                reason = "declared conflict" if explicit else "overlapping impact paths"
                conflicts.append(PortfolioConflict(left_name, right_name, reason))
                for name in (left_name, right_name):
                    current = reports[name]
                    message = f"portfolio conflict with {right_name if name == left_name else left_name}: {reason}"
                    if message not in current.issues:
                        reports[name] = replace(
                            current,
                            consistent=False,
                            issues=current.issues + (message,),
                        )

    debt = 0
    expired = 0
    baseline_path = root / ".mase" / "baseline.yaml"
    if baseline_path.exists():
        try:
            baseline = load_baseline(baseline_path)
            from datetime import date

            debt = len(baseline.failures)
            expired = sum(date.fromisoformat(item.expires) < date.today() for item in baseline.failures)
        except (GovernanceError, ValueError, OSError) as exc:
            diagnostics.append(
                Diagnostic(getattr(exc, "code", "invalid_baseline"), str(exc), path=".mase/baseline.yaml")
            )
    return PortfolioReport(
        tuple(reports[name] for name in sorted(reports)),
        tuple(conflicts),
        tuple(diagnostics),
        debt,
        expired,
    )


def get_status(
    project_dir: Union[str, Path] = ".", change: Optional[str] = None
) -> Union[StatusReport, PortfolioReport]:
    root = Path(project_dir).expanduser().resolve()
    if change is not None:
        return inspect_change_status(_select_change(root, change))
    return _portfolio(root)


def run(project_dir: Union[str, Path] = ".", change: Optional[str] = None, json_output: bool = False):
    report = get_status(project_dir, change)
    if json_output:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    elif isinstance(report, StatusReport):
        marker = "✓" if report.consistent else "✗"
        print(
            f"{marker} {report.change}: lifecycle={report.lifecycle} phase={report.phase} "
            f"profile={report.profile} stack={report.stack} tasks={report.complete}/{report.total}"
        )
        for issue in report.issues:
            print(f"  ! {issue}")
    else:
        marker = "✓" if report.consistent else "✗"
        print(f"{marker} MASE portfolio · {len(report.changes)} active change(s)")
        if report.changes:
            print("  CHANGE              PHASE      LIFECYCLE          TASKS  PROFILE   STATUS")
            for item in report.changes:
                print(
                    f"  {item.change[:18]:18}  {item.phase:9}  {item.lifecycle:17}  "
                    f"{item.complete:>3}/{item.total:<3} {item.profile:9} "
                    f"{'ok' if item.consistent else 'attention'}"
                )
        for conflict in report.conflicts:
            print(f"  ! {conflict.left} ↔ {conflict.right}: {conflict.reason}")
        for diagnostic in report.diagnostics:
            print(f"  ! {diagnostic.change or diagnostic.path}: {diagnostic.message}")
        if report.baseline_debt:
            print(f"  baseline debt: {report.baseline_debt} ({report.expired_baseline} expired)")
    return report
