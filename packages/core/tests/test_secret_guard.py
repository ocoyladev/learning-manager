from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[3]
GUARD_SOURCE = REPOSITORY_ROOT / ".githooks" / "no-env-file.sh"


def _isolated_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "isolated repository"
    repository.mkdir()
    subprocess.run(["git", "init", "--quiet", str(repository)], check=True)
    for key, value in (
        ("user.name", "Secret Guard Test"),
        ("user.email", "secret-guard@example.invalid"),
    ):
        subprocess.run(
            ["git", "-C", str(repository), "config", key, value],
            check=True,
        )
    guard = repository / ".githooks" / "no-env-file.sh"
    guard.parent.mkdir()
    shutil.copy2(GUARD_SOURCE, guard)
    guard.chmod(guard.stat().st_mode | os.X_OK)
    return repository


def _run_guard(repository: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(repository / ".githooks" / "no-env-file.sh")],
        cwd=repository,
        capture_output=True,
        text=True,
        check=False,
    )


def test_guard_rejects_staged_env_basename_without_reading_a_secret(tmp_path: Path) -> None:
    repository = _isolated_repository(tmp_path)
    env_file = repository / "folder with spaces" / ".env"
    env_file.parent.mkdir()
    env_file.write_text("EXAMPLE=value\n")
    subprocess.run(["git", "-C", str(repository), "add", str(env_file)], check=True)

    result = _run_guard(repository)

    assert result.returncode != 0
    assert ".env" in result.stderr
    assert "error" in result.stderr.lower()


def test_guard_accepts_staged_env_example(tmp_path: Path) -> None:
    repository = _isolated_repository(tmp_path)
    env_example = repository / "folder with spaces" / ".env.example"
    env_example.parent.mkdir()
    env_example.write_text("EXAMPLE=value\n")
    subprocess.run(["git", "-C", str(repository), "add", str(env_example)], check=True)

    result = _run_guard(repository)

    assert result.returncode == 0
    assert result.stderr == ""
