from pathlib import Path

import pytest

from mase_cli import main as cli
from mase_cli.fix import promote_lite_change, start_lite_change
from mase_cli.schema import GovernanceError


def test_fix_start_creates_single_source_and_promote_is_lossless(tmp_path: Path):
    source = start_lite_change(tmp_path, "layout-typo")

    assert source.name == "change.md"
    text = source.read_text(encoding="utf-8")
    for heading in ("原因", "验收行为", "影响范围", "根因假设与 RED 证据", "测试方法", "回滚方式", "Tasks"):
        assert f"# {heading}" in text
    change = source.parent
    assert sorted(item.name for item in change.iterdir()) == ["change.md"]

    outputs = promote_lite_change(tmp_path, "layout-typo")

    assert {item.name for item in outputs} >= {
        "proposal.md", "design.md", "tasks.md", "mase-state.yaml"
    }
    assert (change / "specs" / "behavior" / "spec.md").is_file()
    assert (change / "change.md").read_text(encoding="utf-8") == text
    assert "layout-typo" in (change / "proposal.md").read_text(encoding="utf-8")


def test_fix_promote_conflict_leaves_existing_files_untouched(tmp_path: Path):
    source = start_lite_change(tmp_path, "conflict")
    proposal = source.parent / "proposal.md"
    proposal.write_text("user content\n", encoding="utf-8")

    with pytest.raises(GovernanceError, match="conflict"):
        promote_lite_change(tmp_path, "conflict")

    assert proposal.read_text(encoding="utf-8") == "user content\n"
    assert not (source.parent / "tasks.md").exists()


def test_fix_cli_start_and_promote(tmp_path: Path, capsys):
    assert cli.main(["fix", "start", "cli-fix", "--dir", str(tmp_path)]) == 0
    assert "change.md" in capsys.readouterr().out
    assert cli.main([
        "fix", "promote", "cli-fix", "--to", "standard", "--dir", str(tmp_path)
    ]) == 0
    assert "proposal.md" in capsys.readouterr().out
