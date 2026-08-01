from pathlib import Path
from typing import List, Optional

import pytest
import yaml

from mase_cli.schema import GovernanceError
from mase_cli.test_selection import load_test_manifest, select_tests


def _write_manifest(root: Path, tests: List[dict]):
    target = root / ".mase" / "tests.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump(
            {"schema": "mase-test-manifest/v1", "tests": tests},
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return target


def _item(
    test_id: str,
    *,
    tier: str = "p0_journey",
    capability: str = "testcase_generation",
    selector: str = "e2e/tests/testcase.spec.js",
    paths: Optional[List[str]] = None,
):
    item = {
        "id": test_id,
        "tier": tier,
        "runner": "playwright",
        "selectors": [selector],
        "capabilities": [capability],
        "paths": paths or ["templates/testcase.html", "static/js/testcase.js"],
    }
    if tier == "p0_journey":
        item["acceptance"] = "上传需求并生成、预览和下载测试用例"
    return item


def test_manifest_loads_versioned_items_and_stable_digest(tmp_path):
    _write_manifest(tmp_path, [_item("testcase-generate"), _item(
        "testcase-tabs",
        tier="ui_contract",
        selector="e2e/tests/testcase-tabs.spec.js",
    )])

    first = load_test_manifest(tmp_path)
    second = load_test_manifest(tmp_path)

    assert tuple(item.id for item in first.tests) == ("testcase-generate", "testcase-tabs")
    assert first.digest == second.digest
    assert first.path == tmp_path / ".mase" / "tests.yaml"


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda tests: tests + [dict(tests[0])], "duplicate test id"),
        (lambda tests: [{**tests[0], "tier": "smoke"}], "tier"),
        (lambda tests: [{**tests[0], "selectors": ["../outside.spec.js"]}], "escapes project root"),
        (lambda tests: [{**tests[0], "paths": ["/tmp/outside"]}], "escapes project root"),
        (lambda tests: [{key: value for key, value in tests[0].items() if key != "acceptance"}], "acceptance"),
        (lambda tests: [{**tests[0], "capabilities": []}], "capabilities"),
    ],
)
def test_manifest_rejects_invalid_or_unsafe_items(tmp_path, mutate, message):
    _write_manifest(tmp_path, mutate([_item("testcase-generate")]))

    with pytest.raises(GovernanceError, match=message):
        load_test_manifest(tmp_path)


def test_missing_manifest_is_legacy_compatible_when_not_required(tmp_path):
    manifest = load_test_manifest(tmp_path, required=False)

    assert manifest.legacy is True
    assert manifest.tests == ()
    with pytest.raises(GovernanceError, match="test manifest is missing"):
        load_test_manifest(tmp_path, required=True)


def test_selection_matches_impact_and_capability_with_stable_order(tmp_path):
    _write_manifest(tmp_path, [
        _item("z-storypoint", capability="story_point", selector="e2e/tests/story.spec.js",
              paths=["templates/story_point.html"]),
        _item("b-testcase-download", selector="e2e/tests/testcase-download.spec.js"),
        _item("a-testcase-generate", selector="e2e/tests/testcase-generate.spec.js"),
    ])
    manifest = load_test_manifest(tmp_path)

    selection = select_tests(
        manifest,
        tiers=("p0_journey",),
        impact_paths=("templates/testcase.html",),
        capability_scope="testcase_generation",
        ui_changed=True,
    )

    assert selection.test_ids == ("a-testcase-generate", "b-testcase-download")
    assert selection.selectors == (
        "e2e/tests/testcase-generate.spec.js",
        "e2e/tests/testcase-download.spec.js",
    )
    assert selection.fallback == ""
    assert "capability:testcase_generation" in selection.reason


def test_ui_p0_selection_conservatively_falls_back_to_all_tier(tmp_path):
    _write_manifest(tmp_path, [
        _item("storypoint", capability="story_point", selector="e2e/tests/story.spec.js",
              paths=["templates/story_point.html"]),
        _item("testcase", selector="e2e/tests/testcase.spec.js"),
    ])

    selection = select_tests(
        load_test_manifest(tmp_path),
        tiers=("p0_journey",),
        impact_paths=("templates/new_ui.html",),
        ui_changed=True,
    )

    assert selection.test_ids == ("storypoint", "testcase")
    assert selection.fallback == "conservative_all_tier"
    assert selection.to_dict()["fallback"] == "conservative_all_tier"


def test_non_ui_change_does_not_trigger_p0_fallback(tmp_path):
    _write_manifest(tmp_path, [_item("testcase")])

    selection = select_tests(
        load_test_manifest(tmp_path),
        tiers=("p0_journey",),
        impact_paths=("docs/README.md",),
        ui_changed=False,
    )

    assert selection.test_ids == ()
    assert selection.fallback == ""
