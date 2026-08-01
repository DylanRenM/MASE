import json
import re
import zipfile
from pathlib import Path

import yaml

from scripts.verify_wheel_manifest import expected_runtime_files, verify


ROOT = Path(__file__).resolve().parents[1]


def test_manifest_runtime_is_non_overlapping_and_contains_release_skill():
    expected = expected_runtime_files(ROOT)

    assert "skills/release-software/SKILL.md" in expected
    assert "skills/release-software/agents/openai.yaml" in expected
    assert "skills/release-software/scripts/generate_release_plan.py" in expected
    assert "schemas/sandbox-config-v1.schema.json" in expected
    assert "schemas/mase-test-manifest.schema.json" in expected
    assert "schemas/mase-test-diagnostic.schema.json" in expected
    assert "templates/tests.yaml" in expected
    assert "skills/webapp-testing/mase-reporter.cjs" in expected


def test_wheel_manifest_verifier_detects_missing_runtime_file(tmp_path):
    expected = expected_runtime_files(ROOT)
    missing = "skills/release-software/SKILL.md"
    wheel = tmp_path / "mase-2.4.0-py3-none-any.whl"
    prefix = "mase-2.4.0.data/data/share/mase/"
    with zipfile.ZipFile(wheel, "w") as archive:
        for relative in sorted(expected - {missing}):
            archive.writestr(prefix + relative, "test")

    report = verify(ROOT, wheel)

    assert report["ok"] is False
    assert report["missing"] == [missing]


def test_python_javascript_lock_and_manifest_versions_match():
    manifest = yaml.safe_load((ROOT / "framework-manifest.yaml").read_text(encoding="utf-8"))
    package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "package-lock.json").read_text(encoding="utf-8"))
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    version = str(manifest["version"])
    assert f'version = "{version}"' in pyproject
    assert package["version"] == lock["version"] == lock["packages"][""]["version"] == version


def test_distributed_markdown_relative_links_resolve():
    missing = []
    for base in (ROOT / "skills", ROOT / "docs"):
        for source in base.rglob("*.md"):
            for raw in re.findall(r"\[[^]]+\]\(([^)]+)\)", source.read_text(encoding="utf-8")):
                target = raw.split("#", 1)[0].strip()
                if not target or "://" in target or target.startswith(("#", "mailto:")):
                    continue
                if not (source.parent / target).resolve().exists():
                    missing.append(f"{source.relative_to(ROOT)} -> {target}")

    assert missing == []
