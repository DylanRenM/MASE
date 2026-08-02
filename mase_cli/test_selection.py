"""Versioned test manifests and conservative impact-driven selection."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple, Union

from mase_cli.schema import GovernanceError, load_yaml_document, validate_payload


PathInput = Union[str, Path]
TEST_TIERS = (
    "unit",
    "contract",
    "integration",
    "ui_contract",
    "p0_journey",
    "p1_regression",
)
_WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")


@dataclass(frozen=True)
class TestManifestItem:
    id: str
    tier: str
    runner: str
    selectors: Tuple[str, ...]
    capabilities: Tuple[str, ...]
    paths: Tuple[str, ...]
    tags: Tuple[str, ...] = ()
    acceptance: str = ""

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TestManifestItem":
        return cls(
            id=str(payload["id"]),
            tier=str(payload["tier"]),
            runner=str(payload["runner"]),
            selectors=tuple(str(item) for item in payload.get("selectors", [])),
            capabilities=tuple(str(item) for item in payload.get("capabilities", [])),
            paths=tuple(str(item) for item in payload.get("paths", [])),
            tags=tuple(str(item) for item in payload.get("tags", [])),
            acceptance=str(payload.get("acceptance", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "id": self.id,
            "tier": self.tier,
            "runner": self.runner,
            "selectors": list(self.selectors),
            "capabilities": list(self.capabilities),
            "paths": list(self.paths),
            "tags": list(self.tags),
            "acceptance": self.acceptance,
        }
        return {key: value for key, value in payload.items() if value not in ("", [], ())}


@dataclass(frozen=True)
class TestManifest:
    path: Path
    tests: Tuple[TestManifestItem, ...]
    digest: str
    legacy: bool = False


@dataclass(frozen=True)
class TestSelection:
    test_ids: Tuple[str, ...]
    selectors: Tuple[str, ...]
    tiers: Tuple[str, ...]
    reason: str
    fallback: str = ""
    manifest_digest: str = ""

    @property
    def digest(self) -> str:
        payload = {
            "ids": list(self.test_ids),
            "selectors": list(self.selectors),
            "tiers": list(self.tiers),
            "manifest_digest": self.manifest_digest,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_ids": list(self.test_ids),
            "selectors": list(self.selectors),
            "tiers": list(self.tiers),
            "reason": self.reason,
            "fallback": self.fallback,
            "manifest_digest": self.manifest_digest,
            "test_digest": self.digest,
        }


def _validate_safe_value(root: Path, value: str, *, field: str) -> None:
    normalized = value.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or _WINDOWS_ABSOLUTE.match(value) or ".." in pure.parts:
        raise GovernanceError(
            f"{field} escapes project root: {value}",
            path=root / ".mase" / "tests.yaml",
            code="path_escape",
        )


def _manifest_digest(items: Sequence[TestManifestItem]) -> str:
    payload = [item.to_dict() for item in sorted(items, key=lambda item: item.id)]
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def load_test_manifest(project_root: PathInput, required: bool = True) -> TestManifest:
    root = Path(project_root).expanduser().resolve()
    path = root / ".mase" / "tests.yaml"
    if not path.is_file():
        if required:
            raise GovernanceError("test manifest is missing", path=path, code="not_found")
        return TestManifest(path=path, tests=(), digest="", legacy=True)

    payload = load_yaml_document(path)
    validate_payload(payload, "mase-test-manifest.schema.json", path=path)
    items = tuple(TestManifestItem.from_dict(item) for item in payload.get("tests", []))
    seen = set()
    for item in items:
        if item.id in seen:
            raise GovernanceError(f"duplicate test id: {item.id}", path=path, code="schema")
        seen.add(item.id)
        for value in item.paths:
            _validate_safe_value(root, value, field=f"test {item.id} path")
        for value in item.selectors:
            _validate_safe_value(root, value, field=f"test {item.id} selector")
    return TestManifest(path=path, tests=items, digest=_manifest_digest(items))


def _static_prefix(value: str) -> str:
    normalized = value.replace("\\", "/").lstrip("./")
    wildcard = min(
        (normalized.find(char) for char in "*[?" if char in normalized),
        default=len(normalized),
    )
    return normalized[:wildcard].rstrip("/")


def _paths_overlap(left: str, right: str) -> bool:
    left_norm = left.replace("\\", "/").lstrip("./")
    right_norm = right.replace("\\", "/").lstrip("./")
    if fnmatch.fnmatch(left_norm, right_norm) or fnmatch.fnmatch(right_norm, left_norm):
        return True
    left_prefix = _static_prefix(left_norm)
    right_prefix = _static_prefix(right_norm)
    if not left_prefix or not right_prefix:
        return False
    return (
        left_prefix == right_prefix
        or left_prefix.startswith(right_prefix + "/")
        or right_prefix.startswith(left_prefix + "/")
    )


def _unique(values: Iterable[str]) -> Tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def select_tests(
    manifest: TestManifest,
    *,
    tiers: Sequence[str],
    impact_paths: Sequence[str],
    capability_scope: Optional[str] = None,
    ui_changed: bool = False,
) -> TestSelection:
    requested_tiers = tuple(dict.fromkeys(str(item) for item in tiers))
    invalid = sorted(set(requested_tiers) - set(TEST_TIERS))
    if invalid:
        raise GovernanceError("unknown test tiers: " + ", ".join(invalid), code="schema")
    candidates = [item for item in manifest.tests if item.tier in requested_tiers]
    if capability_scope:
        candidates = [item for item in candidates if capability_scope in item.capabilities]
    matched = [
        item
        for item in candidates
        if any(_paths_overlap(test_path, impact) for test_path in item.paths for impact in impact_paths)
    ]
    fallback = ""
    if not matched and ui_changed and "p0_journey" in requested_tiers:
        matched = candidates
        fallback = "conservative_all_tier"
    matched.sort(key=lambda item: item.id)
    reason_parts = []
    if capability_scope:
        reason_parts.append(f"capability:{capability_scope}")
    if matched and not fallback:
        reason_parts.append("impact_path_match")
    elif fallback:
        reason_parts.append(fallback)
    else:
        reason_parts.append("no_applicable_tests")
    return TestSelection(
        test_ids=tuple(item.id for item in matched),
        selectors=_unique(selector for item in matched for selector in item.selectors),
        tiers=requested_tiers,
        reason=";".join(reason_parts),
        fallback=fallback,
        manifest_digest=manifest.digest,
    )
