import json
from pathlib import Path

import pytest

from learning_manager.contracts import Concept, LearnerConceptState, LearningGoal
from learning_manager.domain.concept_graph import ConceptGraph

ROOT = Path(__file__).parents[4]
CASES = sorted(ROOT.joinpath("eval/cases/nsdq").glob("*.json"))


def test_there_are_eleven_cases() -> None:
    assert len(CASES) == 11


def test_at_least_one_case_is_hard() -> None:
    assert sum(json.loads(p.read_text())["difficulty"] == "hard" for p in CASES) >= 1


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_case_is_structurally_valid(path: Path) -> None:
    case = json.loads(path.read_text())
    LearningGoal(**case["goal"])
    ConceptGraph([Concept(**item) for item in case["concept_graph"]])
    ids = {item["id"] for item in case["concept_graph"]}
    for cid, state in case["learner_model"].items():
        assert cid in ids
        LearnerConceptState(concept_id=cid, **state)


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_every_case_has_a_matching_key(path: Path) -> None:
    assert (ROOT / "eval/keys" / path.name).is_file()


@pytest.mark.parametrize("path", sorted((ROOT / "eval/cases/sources").glob("*.json")))
def test_every_referenced_source_exists_in_corpus(path: Path) -> None:
    case = json.loads(path.read_text())
    manifest = json.loads((ROOT / "corpus" / case["topic"] / "manifest.json").read_text())
    known = {item["id"] for item in manifest}
    for claim in case["claims"]:
        for field in ("supported_by", "superseded_by"):
            if claim.get(field):
                assert claim[field] in known
