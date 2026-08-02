import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTER = ROOT / "skills" / "webapp-testing" / "mase-reporter.cjs"


def _run_reporter(tmp_path: Path, *, status: str, retry: int, error: str = ""):
    output = tmp_path / "diagnostic.json"
    script = """
const Reporter = require(process.argv[1]);
const reporter = new Reporter();
reporter.onTestEnd(
  { id: 'journey-a', title: 'journey-a', titlePath: () => ['suite', 'journey-a'] },
  { status: process.argv[2], retry: Number(process.argv[3]), errors: process.argv[4] ? [{message: process.argv[4]}] : [], attachments: [{path: 'trace.zip'}] }
);
reporter.onEnd({ status: process.argv[2] === 'passed' ? 'passed' : 'failed' });
"""
    environment = dict(os.environ)
    environment["MASE_TEST_DIAGNOSTIC_PATH"] = str(output)
    subprocess.run(
        ["node", "-e", script, str(REPORTER), status, str(retry), error],
        check=True,
        env=environment,
        cwd=ROOT,
    )
    return json.loads(output.read_text(encoding="utf-8"))


def test_reporter_marks_retry_pass_as_flaky(tmp_path):
    payload = _run_reporter(tmp_path, status="passed", retry=1)

    assert payload["first_attempt_result"] == "failed"
    assert payload["final_result"] == "passed"
    assert payload["classification"] == "flaky"
    assert payload["attempts"] == 2
    assert payload["failed_tests"] == ["suite › journey-a"]


def test_reporter_classifies_environment_and_preserves_artifacts(tmp_path):
    payload = _run_reporter(
        tmp_path,
        status="failed",
        retry=0,
        error="browser net::ERR_CONNECTION_REFUSED",
    )

    assert payload["classification"] == "environment"
    assert payload["artifacts"] == ["trace.zip"]


def test_reporter_classifies_missing_browser_binary_as_environment(tmp_path):
    payload = _run_reporter(
        tmp_path,
        status="failed",
        retry=0,
        error="browserType.launch: Executable doesn't exist; run npx playwright install",
    )

    assert payload["classification"] == "environment"
