import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_repository_boundary.py"


def run_audit(root: Path, *extra: str):
    return subprocess.run(
        [sys.executable, str(AUDIT), "--root", str(root), "--json", *extra],
        text=True,
        capture_output=True,
        check=False,
    )


def test_current_repository_boundary_is_clean():
    result = run_audit(ROOT)

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {"ok": True, "issues": []}


def test_audit_rejects_unknown_root_and_generated_debris(tmp_path):
    (tmp_path / "embedded-product").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / ".DS_Store").write_text("metadata", encoding="utf-8")

    result = run_audit(tmp_path)
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["ok"] is False
    assert {issue["path"] for issue in payload["issues"]} == {
        "embedded-product",
    }


def test_finder_metadata_is_ignored_consistently(tmp_path):
    (tmp_path / ".DS_Store").write_text("metadata", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / ".DS_Store").write_text("metadata", encoding="utf-8")

    result = run_audit(tmp_path)

    assert result.returncode == 0
    assert json.loads(result.stdout) == {"ok": True, "issues": []}


def test_embedded_products_and_legacy_roots_are_absent():
    for relative in (
        "bazi-encyclopedia",
        "story point",
        ".backup",
        ".frontend-slides",
        "framework",
        "history",
        "index.html",
        "docs/archive",
        "docs/superpowers",
        "training/ai4se",
        "training/skills",
        "training/measures-training.html",
    ):
        assert not (ROOT / relative).exists(), relative


def test_pytest_collection_is_scoped_to_framework_tests():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "[tool.pytest.ini_options]" in text
    assert 'testpaths = ["tests"]' in text
    assert 'addopts = "-p no:cacheprovider"' in text


def test_e2e_framework_change_does_not_embed_named_adopter_work():
    change = ROOT / "openspec" / "changes" / "optimize-e2e-automation"
    if not change.exists():
        return

    checked = [
        change / "proposal.md",
        change / "design.md",
        change / "tasks.md",
        change / "verification.md",
    ]
    violations = [
        str(path.relative_to(ROOT))
        for path in checked
        if path.is_file()
        and re.search(r"\bPilot\b|\.\./pilot", path.read_text(encoding="utf-8"), re.I)
    ]

    assert violations == []
