import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from mase_cli import main as cli
from mase_cli.evidence import run_gate
from mase_cli.gates import execute_defined_gate, load_gate_definitions
from mase_cli.profiles import ProfileRegistry
from mase_cli.release import build_release_plan
from mase_cli.risk import derive_gate_plan
from mase_cli.state import ChangeState, inspect_change_status
from mase_cli.evidence import path_digest


ROOT = Path(__file__).resolve().parents[1]


def release_context(**overrides):
    payload = {
        "schema": "mase-release/v1",
        "intent": "deploy",
        "authority": "read-only",
        "artifact": {
            "kind": "image",
            "identity": "registry.example/app@sha256:abc123",
            "provenance": "commit:abc123",
        },
        "target": {
            "kind": "orchestrator",
            "environment": "production",
            "platform": "linux",
        },
        "rollout": {"strategy": "rolling", "max_impact": "one replica"},
        "state": {"classes": [], "migration": "none"},
        "interfaces": ["event"],
        "external_capabilities": [],
        "recovery": {"strategies": ["roll-forward"]},
        "observation": {"signals": ["consumer success rate"], "window": "15m"},
    }
    payload.update(overrides)
    return payload


def write_change(root: Path, *, release=None, risks=None, gates=None, evidence=None):
    change = root / "openspec" / "changes" / "demo"
    change.mkdir(parents=True)
    payload = {
        "schema": "mase-project/v2",
        "profile": "standard",
        "stack": "generic",
        "toolchains": [],
        "phase": "release",
        "product": {"has_ui": False, "ui_platform": None},
        "impact": {"ui_changed": False, "paths": ["src/**"]},
        "risk": {"triggers": risks or [], "capabilities": {}},
        "gates": gates or {},
        "evidence": evidence or [],
        "dependencies": [],
        "conflicts_with": [],
        "blockers": [],
    }
    if release is not None:
        payload["release"] = release
    (change / "mase-state.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    (change / "tasks.md").write_text("- [x] 1.1 done\n", encoding="utf-8")
    return change


def test_release_overlay_is_optional_and_exposed_by_state(tmp_path):
    legacy = write_change(tmp_path)
    state = ChangeState.load(legacy / "mase-state.yaml")
    assert state.release == {}

    overlay = release_context()
    payload = yaml.safe_load((legacy / "mase-state.yaml").read_text(encoding="utf-8"))
    payload["release"] = overlay
    (legacy / "mase-state.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    state = ChangeState.load(legacy / "mase-state.yaml")
    assert state.release["intent"] == "deploy"
    assert state.release["artifact"]["kind"] == "image"


def test_release_outcome_distinguishes_artifact_and_live_evidence(tmp_path):
    release = release_context()
    gates = {
        "release_artifact_identity": "passed",
        "release_artifact_integrity": "passed",
        "release_forbidden_content": "passed",
        "release_target_preflight": "pending",
        "release_recovery_readiness": "pending",
        "release_live_verification": "pending",
        "release_observation": "pending",
    }
    change = write_change(tmp_path, release=release, gates=gates)
    for gate in (
        "release_artifact_identity",
        "release_artifact_integrity",
        "release_forbidden_content",
    ):
        run_gate(
            tmp_path,
            change / "mase-state.yaml",
            gate,
            [sys.executable, "-c", "print('ok')"],
            inputs=[],
        )
    report = inspect_change_status(change)
    assert report.release_outcome == "artifact_ready"
    assert report.to_dict()["release"]["intent"] == "deploy"


def test_candidate_object_without_fresh_final_evidence_is_not_ready(tmp_path):
    change = write_change(tmp_path, release=release_context(), gates={})
    payload = yaml.safe_load((change / "mase-state.yaml").read_text(encoding="utf-8"))
    payload["candidate"] = {
        "id": "candidate-1234",
        "created_at": "2026-07-28T00:00:00Z",
        "input_digest": path_digest(tmp_path, []),
        "inputs": [],
    }
    (change / "mase-state.yaml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    assert inspect_change_status(change).release_outcome == "planned"


def test_release_overlay_adds_gates_without_forcing_strict():
    plan = derive_gate_plan(
        ProfileRegistry(ROOT / "profiles"),
        "standard",
        [],
        product={"has_ui": False},
        impact={"ui_changed": False},
        release=release_context(),
    )

    assert plan.profile == "standard"
    assert {
        "release_artifact_identity",
        "release_artifact_integrity",
        "release_target_preflight",
        "release_live_verification",
        "release_observation",
    }.issubset(plan.required_gates)


def test_release_risk_triggers_escalate_only_when_declared():
    registry = ProfileRegistry(ROOT / "profiles")
    ordinary = derive_gate_plan(registry, "standard", ["cross_platform_deployment"])
    infrastructure = derive_gate_plan(registry, "standard", ["infrastructure_change"])

    assert ordinary.profile == "standard"
    assert "release_target_preflight" in ordinary.required_gates
    assert infrastructure.profile == "strict"
    assert "independent_review" in infrastructure.required_gates
    assert "rollback_verification" in infrastructure.required_gates


def test_gate_schema_accepts_release_stages(tmp_path):
    gate_file = tmp_path / ".mase" / "gates.yaml"
    gate_file.parent.mkdir(parents=True)
    gate_file.write_text(
        yaml.safe_dump(
            {
                "schema": "mase-gates/v1",
                "gates": {
                    "release_artifact_identity": {
                        "stage": "release_artifact",
                        "command": ["python3", "-c", "print('ok')"],
                        "artifacts": ["dist/release.bin"],
                        "mode": "automatic",
                        "effect": "read-only",
                        "required_authority": "read-only",
                        "requires": [],
                    },
                    "release_observation": {
                        "stage": "release_observe",
                        "command": ["python3", "-c", "print('ok')"],
                        "mode": "automatic",
                        "effect": "read-only",
                        "required_authority": "read-only",
                        "requires": [],
                    },
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    definitions = load_gate_definitions(tmp_path)
    assert definitions.gates["release_artifact_identity"].stage == "release_artifact"
    assert definitions.gates["release_observation"].stage == "release_observe"


def test_release_gate_evidence_becomes_stale_when_artifact_identity_changes(tmp_path):
    change = write_change(
        tmp_path,
        release=release_context(),
        gates={"release_artifact_identity": "pending"},
    )
    gate_file = tmp_path / ".mase" / "gates.yaml"
    gate_file.parent.mkdir(parents=True)
    gate_file.write_text(
        yaml.safe_dump(
            {
                "schema": "mase-gates/v1",
                "gates": {
                    "release_artifact_identity": {
                        "stage": "release_artifact",
                        "command": [sys.executable, "-c", "print('ok')"],
                        "mode": "automatic",
                        "effect": "read-only",
                        "required_authority": "read-only",
                        "requires": [],
                    }
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    execute_defined_gate(tmp_path, "demo", "release_artifact_identity")
    assert inspect_change_status(change).effective_gates["release_artifact_identity"] == "passed"

    payload = yaml.safe_load((change / "mase-state.yaml").read_text(encoding="utf-8"))
    payload["release"]["artifact"]["identity"] = "registry.example/app@sha256:different"
    (change / "mase-state.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )

    assert inspect_change_status(change).effective_gates["release_artifact_identity"] == "stale"


def test_read_only_authority_blocks_effectful_release_before_command(tmp_path):
    change = write_change(
        tmp_path,
        release=release_context(authority="read-only"),
        gates={"release_live_verification": "pending"},
    )
    sentinel = tmp_path / "live-mutated.txt"
    gate_file = tmp_path / ".mase" / "gates.yaml"
    gate_file.parent.mkdir(parents=True)
    gate_file.write_text(yaml.safe_dump({
        "schema": "mase-gates/v1",
        "gates": {
            "release_live_verification": {
                "stage": "release_live",
                "command": [sys.executable, "-c", "from pathlib import Path; Path('live-mutated.txt').write_text('bad')"],
                "mode": "automatic",
                "effect": "external-write",
                "required_authority": "release",
                "requires": [],
            }
        },
    }, sort_keys=False), encoding="utf-8")

    with pytest.raises(Exception, match="release authority"):
        execute_defined_gate(tmp_path, "demo", "release_live_verification")

    assert not sentinel.exists()
    assert not yaml.safe_load((change / "mase-state.yaml").read_text())["evidence"]


def test_release_gate_not_selected_by_overlay_intent_is_blocked(tmp_path):
    write_change(
        tmp_path,
        release=release_context(intent="package", authority="release"),
        gates={"release_observation": "pending"},
    )
    gate_file = tmp_path / ".mase" / "gates.yaml"
    gate_file.parent.mkdir(parents=True)
    gate_file.write_text(yaml.safe_dump({
        "schema": "mase-gates/v1",
        "gates": {
            "release_observation": {
                "stage": "release_observe",
                "command": [sys.executable, "-c", "print('observe')"],
                "mode": "automatic",
                "effect": "read-only",
                "required_authority": "read-only",
                "requires": [],
            }
        },
    }, sort_keys=False), encoding="utf-8")

    with pytest.raises(Exception, match="not applicable"):
        execute_defined_gate(tmp_path, "demo", "release_observation")


def test_release_stage_predecessors_are_fresh_before_live_execution(tmp_path):
    write_change(
        tmp_path,
        release=release_context(authority="release"),
        gates={
            "release_target_preflight": "pending",
            "release_live_verification": "pending",
        },
    )
    gate_file = tmp_path / ".mase" / "gates.yaml"
    gate_file.parent.mkdir(parents=True)
    gate_file.write_text(yaml.safe_dump({
        "schema": "mase-gates/v1",
        "gates": {
            "release_target_preflight": {
                "stage": "release_preflight",
                "command": [sys.executable, "-c", "print('preflight')"],
                "mode": "automatic",
                "effect": "read-only",
                "required_authority": "read-only",
                "requires": [],
            },
            "release_live_verification": {
                "stage": "release_live",
                "command": [sys.executable, "-c", "print('live')"],
                "mode": "automatic",
                "effect": "external-write",
                "required_authority": "release",
                "requires": ["release_target_preflight"],
            },
        },
    }, sort_keys=False), encoding="utf-8")

    with pytest.raises(Exception, match="predecessor evidence"):
        execute_defined_gate(tmp_path, "demo", "release_live_verification")


def test_release_cli_plan_is_read_only_and_platform_neutral(tmp_path, capsys):
    context = tmp_path / "release-context.yaml"
    context.write_text(yaml.safe_dump(release_context(), sort_keys=False), encoding="utf-8")
    before = context.read_bytes()

    assert cli.main(
        ["release", "plan", "--context", str(context), "--date", "2026-07-28", "--json"]
    ) == 0
    result = json.loads(capsys.readouterr().out)

    assert result["intent"] == "deploy"
    assert result["release_outcome"] == "planned"
    assert "container-orchestrator" in result["adapters"]
    assert all(value == "pending" for value in result["gates"].values())
    assert context.read_bytes() == before


def test_release_cli_rejects_canary_without_observation_signal(tmp_path, capsys):
    context = release_context(
        rollout={"strategy": "canary", "max_impact": "5%"},
        observation={"signals": [], "window": "15m"},
    )
    path = tmp_path / "release-context.yaml"
    path.write_text(yaml.safe_dump(context, sort_keys=False), encoding="utf-8")

    with pytest.raises(SystemExit) as exit_info:
        cli.main(["release", "plan", "--context", str(path), "--json"])

    assert exit_info.value.code == cli.EXIT_CONFIG
    assert "observation" in capsys.readouterr().err


def test_release_plan_generator_omits_irrelevant_web_and_windows_assumptions(tmp_path):
    context = tmp_path / "release-context.yaml"
    context.write_text(yaml.safe_dump(release_context(), sort_keys=False), encoding="utf-8")
    script = ROOT / "skills" / "release-software" / "scripts" / "generate_release_plan.py"

    first = subprocess.run(
        [sys.executable, str(script), "--context", str(context), "--date", "2026-07-28"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    second = subprocess.run(
        [sys.executable, str(script), "--context", str(context), "--date", "2026-07-28"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout

    assert first == second
    assert "container image" in first.lower()
    assert "rolling" in first.lower()
    assert "event" in first.lower()
    for forbidden in ("PowerShell", "ZIP", "PID", "browser", "database", "LLM"):
        assert forbidden not in first


@pytest.mark.parametrize(
    ("target", "artifact", "expected"),
    [
        ({"kind": "vm", "environment": "production", "platform": "linux"},
         {"kind": "binary", "identity": "sha256:vm", "provenance": "commit:vm"},
         "vm-service"),
        ({"kind": "orchestrator", "environment": "production", "platform": "linux"},
         {"kind": "image", "identity": "repo/app@sha256:container", "provenance": "commit:c"},
         "container-orchestrator"),
        ({"kind": "registry", "environment": "public", "platform": "generic"},
         {"kind": "package", "identity": "pkg@1.2.3", "provenance": "commit:r"},
         "package-registry"),
        ({"kind": "app-store", "environment": "production", "platform": "ios"},
         {"kind": "store-submission", "identity": "app:42", "provenance": "commit:a"},
         "distributed-client"),
    ],
)
def test_release_plan_selects_only_context_adapters(target, artifact, expected):
    plan = build_release_plan(release_context(target=target, artifact=artifact))

    assert expected in plan.adapters
    assert "windows-powershell" not in plan.adapters
    if target.get("platform") == "linux":
        assert "linux-unix" in plan.adapters


def test_release_skill_package_is_valid_and_progressively_disclosed():
    skill = ROOT / "skills" / "release-software"
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(text.split("---", 2)[1])
    metadata = yaml.safe_load((skill / "agents" / "openai.yaml").read_text(encoding="utf-8"))

    assert set(frontmatter) == {"name", "description"}
    assert frontmatter["name"] == "release-software"
    assert "$release-software" in metadata["interface"]["default_prompt"]
    assert len(text.splitlines()) < 220
    for reference in (
        "release-contract.md",
        "artifact-and-state.md",
        "rollout-strategies.md",
        "verification-and-recovery.md",
        "platform-adapters.md",
    ):
        assert (skill / "references" / reference).is_file()


def test_release_docs_manifest_and_rules_route_the_skill():
    rules = (ROOT / "project-rules.md").read_text(encoding="utf-8")
    framework = (ROOT / "docs" / "MASE-framework.md").read_text(encoding="utf-8")
    guide = (ROOT / "docs" / "user-guide.md").read_text(encoding="utf-8")
    manifest = yaml.safe_load((ROOT / "framework-manifest.yaml").read_text(encoding="utf-8"))

    for text in (rules, framework, guide):
        assert "Release Overlay" in text
        assert "release-software" in text
        assert "artifact_ready" in text
        assert "live_verified" in text
    assert "skills" in manifest["runtime"]
    assert "templates" in manifest["runtime"]
    assert "schemas" in manifest["runtime"]
    assert "templates/release-context.yaml" not in manifest["runtime"]
    assert "schemas/mase-release.schema.json" not in manifest["runtime"]
