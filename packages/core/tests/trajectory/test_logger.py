import json
from pathlib import Path

from learning_manager.trajectory.logger import TrajectoryLogger


def test_writes_one_json_object_per_line(tmp_path: Path) -> None:
    log = TrajectoryLogger(run_dir=tmp_path, run_id="run1")
    agent = log.for_agent("CurriculumPlanner")
    agent.step("llm_call", attempt=1, model="gemini-x")
    agent.step("validation", attempt=1, violations=[])

    lines = (tmp_path / "run1" / "CurriculumPlanner.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["agent"] == "CurriculumPlanner"
    assert first["step"] == "llm_call"
    assert first["attempt"] == 1
    assert "ts" in first


def test_separate_file_per_agent(tmp_path: Path) -> None:
    log = TrajectoryLogger(run_dir=tmp_path, run_id="run2")
    log.for_agent("Assessor").step("start")
    log.for_agent("Researcher").step("start")
    files = {p.name for p in (tmp_path / "run2").iterdir()}
    assert files == {"Assessor.jsonl", "Researcher.jsonl"}
