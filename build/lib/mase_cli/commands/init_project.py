"""mase init — initialize a profile- and stack-aware project."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

import yaml

from mase_cli.config import framework_home, load_manifest
from mase_cli.profiles import ProfileRegistry
from mase_cli.rules import RuleSynchronizer


def _slug(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    if not normalized or normalized[0].isdigit():
        normalized = "app_" + normalized
    return normalized


def _swift_module(value: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", value)
    module = "".join(part[:1].upper() + part[1:] for part in parts) or "App"
    return "App" + module if module[0].isdigit() else module


def _write(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _render_template(root: Path, relative: str, **values: str) -> str:
    template = (root / "templates" / "stacks" / relative).read_text(encoding="utf-8")
    for key, value in values.items():
        template = template.replace("{" + key + "}", value)
    return template


def _common_project_files(project: Path, name: str, stack: str, profile: str, root: Path) -> None:
    manifest = load_manifest(root)
    version = str(manifest["version"])
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    metadata = {
        "mase": {
            "version": version,
            "created": created,
            "project": name,
            "profile": profile,
            "stack": stack,
        }
    }
    _write(project / ".mase.yaml", yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True))
    _write(
        project / "README.md",
        _render_template(
            root,
            "common/README.md.tpl",
            project_name=name,
            profile=profile,
            stack=stack,
        ),
    )
    _write(project / ".gitignore", _render_template(root, "common/gitignore.tpl"))
    _write(project / ".env.example", "# Project environment variables\n")
    for directory in ("openspec/changes", "docs", "scripts"):
        (project / directory).mkdir(parents=True, exist_ok=True)
    canonical_rules = root / str(manifest["canonical"]["rules"])
    _write(project / "project-rules.md", canonical_rules.read_text(encoding="utf-8"))
    RuleSynchronizer(project / "project-rules.md").write_missing(project)


def _create_python(project: Path, name: str, package: str, capabilities: Iterable[str], root: Path) -> None:
    _write(
        project / "pyproject.toml",
        _render_template(root, "python/pyproject.toml.tpl", project_name=name),
    )
    _write(project / "Makefile", _render_template(root, "python/Makefile.tpl"))
    package_root = project / "src" / package
    _write(package_root / "__init__.py")
    _write(project / "tests" / "__init__.py")
    for capability in capabilities:
        cap = _slug(capability)
        for subdir in ("models", "services", "routes", "schemas"):
            _write(package_root / cap / subdir / "__init__.py")
        (project / "tests" / "unit" / cap).mkdir(parents=True, exist_ok=True)
    for subdir in ("config", "database", "utils"):
        _write(package_root / "shared" / subdir / "__init__.py")
    (project / "tests" / "integration").mkdir(parents=True, exist_ok=True)


def _create_swift(project: Path, name: str, root: Path) -> None:
    module = _swift_module(name)
    _write(
        project / "Package.swift",
        _render_template(
            root,
            "swift/Package.swift.tpl",
            project_name=name,
            module_name=module,
        ),
    )
    _write(project / "Sources" / module / "main.swift", 'print("Hello from MASE")\n')
    _write(project / "Tests" / f"{module}Tests" / ".gitkeep")


def _create_generic(project: Path) -> None:
    (project / "src").mkdir(parents=True, exist_ok=True)
    (project / "tests").mkdir(parents=True, exist_ok=True)


def run(args):
    root = framework_home(getattr(args, "framework_home", None))
    name = str(args.name)
    if name in {"", ".", ".."} or Path(name).name != name or "/" in name or "\\" in name:
        raise ValueError("project name must be a single safe path component")
    package: Optional[str] = getattr(args, "package", None)
    stack = getattr(args, "stack", None) or ("python" if package else "generic")
    profile = getattr(args, "profile", None) or "standard"
    capabilities = getattr(args, "capabilities", None) or ["core"]
    if stack not in {"generic", "python", "swift"}:
        raise ValueError(f"Unsupported stack: {stack}")
    ProfileRegistry(root / "profiles").get(profile)
    if stack == "python":
        package = _slug(package or name)

    base_dir = Path(getattr(args, "dir", ".")).expanduser().resolve()
    project = base_dir / name
    if project.exists() and any(project.iterdir()):
        raise FileExistsError(f"Project directory is not empty: {project}")
    project.mkdir(parents=True, exist_ok=True)
    _common_project_files(project, name, stack, profile, root)
    if stack == "python":
        _create_python(project, name, package or _slug(name), capabilities, root)
    elif stack == "swift":
        _create_swift(project, name, root)
    else:
        _create_generic(project)
    print(f"  ✓ Created MASE {profile}/{stack} project: {project}")
    return project
