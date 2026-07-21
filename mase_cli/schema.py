"""Validated, source-aware loading for MASE project governance files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from mase_cli.config import PACKAGE_ROOT, framework_home


PathInput = Union[str, Path]


class GovernanceError(ValueError):
    """Expected configuration or governance failure suitable for CLI output."""

    def __init__(self, message: str, *, path: Optional[PathInput] = None, code: str = "config"):
        self.path = Path(path) if path is not None else None
        self.code = code
        prefix = f"{self.path}: " if self.path is not None else ""
        super().__init__(prefix + message)


def load_yaml_document(path: PathInput) -> dict[str, Any]:
    source = Path(path)
    if not source.is_file():
        raise GovernanceError("file does not exist", path=source, code="not_found")
    try:
        payload = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        location = f"line {mark.line + 1}, column {mark.column + 1}: " if mark else ""
        detail = getattr(exc, "problem", None) or str(exc).splitlines()[0]
        raise GovernanceError(location + detail, path=source, code="yaml") from exc
    if not isinstance(payload, dict):
        raise GovernanceError("expected a YAML mapping", path=source, code="schema")
    return payload


def validate_payload(payload: dict[str, Any], schema_name: str, *, path: Optional[PathInput] = None) -> None:
    schema_path = framework_home() / "schemas" / schema_name
    if not schema_path.is_file():
        schema_path = PACKAGE_ROOT / "schemas" / schema_name
    schema = load_yaml_document(schema_path)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload),
        key=lambda item: list(item.path),
    )
    if not errors:
        return
    first = errors[0]
    field = ".".join(str(item) for item in first.absolute_path) or "document"
    raise GovernanceError(f"{field}: {first.message}", path=path, code="schema")


@dataclass(frozen=True)
class ProjectMetadata:
    path: Path
    version: str
    project: str
    profile: str
    stack: str
    toolchains: tuple[str, ...]
    layout: dict[str, str]
    legacy: bool = False

    @classmethod
    def load(cls, path: PathInput, *, allow_legacy: bool = False) -> "ProjectMetadata":
        source = Path(path)
        payload = load_yaml_document(source)
        metadata = payload.get("mase", {})
        if not isinstance(metadata, dict):
            raise GovernanceError("mase must be a mapping", path=source, code="schema")
        legacy = any(key not in metadata for key in ("profile", "stack")) or str(metadata.get("version")) == "1.3"
        if legacy and allow_legacy:
            metadata = dict(metadata)
            metadata.setdefault("project", source.parent.name)
            metadata.setdefault("profile", "standard")
            metadata.setdefault("stack", "python" if (source.parent / "pyproject.toml").exists() else "generic")
            metadata.setdefault("toolchains", [])
            payload = {**payload, "mase": metadata}
        validate_payload(payload, "mase-project.schema.json", path=source)
        return cls(
            path=source,
            version=str(metadata["version"]),
            project=str(metadata["project"]),
            profile=str(metadata["profile"]),
            stack=str(metadata["stack"]),
            toolchains=tuple(str(item) for item in metadata.get("toolchains", [])),
            layout={str(key): str(value) for key, value in metadata.get("layout", {}).items()},
            legacy=legacy,
        )
