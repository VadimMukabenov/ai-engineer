import json
import subprocess
import sys


def run(root, command):
    return subprocess.run(
        [sys.executable, "-m", "learning_hub.cli", "--root", str(root), command],
        capture_output=True,
        text=True,
    )


def test_status_command_outputs_real_zero(course_root):
    result = run(course_root, "status")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["mastered_outcomes"] == 0


def test_verify_fails_when_lock_removed(course_root):
    (course_root / "governance/content-lock.json").unlink()
    result = run(course_root, "verify")
    assert result.returncode == 1
    assert "lock" in result.stdout
