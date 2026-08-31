import pytest

from learning_manager.contracts import Concept, ConceptState, LearnerConceptState, LearnerModel
from learning_manager.domain.concept_graph import ConceptGraph, CyclicGraphError

CONCEPTS = [
    Concept(id="pods", name="Pods"),
    Concept(id="services", name="Services", prerequisites=["pods"]),
    Concept(id="ingress", name="Ingress", prerequisites=["services"]),
]


def _model(**mastery: float) -> LearnerModel:
    return LearnerModel(
        goal_id="g",
        concepts={
            concept_id: LearnerConceptState(
                concept_id=concept_id,
                mastery=value,
                confidence=0.8,
                state=ConceptState.DEVELOPING,
            )
            for concept_id, value in mastery.items()
        },
    )


def test_unlocked_includes_roots() -> None:
    assert ConceptGraph(CONCEPTS).unlocked(_model()) == ["pods"]


def test_non_root_requires_every_prerequisite_to_meet_threshold() -> None:
    graph = ConceptGraph(CONCEPTS)

    assert graph.unlocked(_model(pods=0.9, services=0.30)) == ["pods", "services"]
    assert "ingress" not in graph.unlocked(_model(pods=0.9, services=0.30))


def test_non_root_unlocks_at_exact_prerequisite_threshold() -> None:
    graph = ConceptGraph(CONCEPTS)

    assert graph.unlocked(_model(pods=0.70, services=0.70)) == ["pods", "services", "ingress"]


def test_missing_model_state_keeps_concept_locked() -> None:
    graph = ConceptGraph(CONCEPTS)

    assert graph.blocked_by("services", _model()) == ["pods"]
    assert graph.blocked_by("ingress", _model(pods=0.9)) == ["services"]


def test_blocked_by_returns_only_weak_or_missing_prerequisites_in_declared_order() -> None:
    graph = ConceptGraph(
        [
            Concept(id="root", name="Root"),
            Concept(id="branch-a", name="Branch A", prerequisites=["root"]),
            Concept(id="branch-b", name="Branch B", prerequisites=["root"]),
            Concept(
                id="capstone",
                name="Capstone",
                prerequisites=["branch-a", "branch-b"],
            ),
        ]
    )

    assert graph.blocked_by("capstone", _model(root=0.9, **{"branch-a": 0.7})) == ["branch-b"]


def test_topological_order_is_deterministic_and_respects_dependencies() -> None:
    concepts = [
        Concept(id="z", name="Z", prerequisites=["b"]),
        Concept(id="a", name="A"),
        Concept(id="b", name="B", prerequisites=["a"]),
        Concept(id="y", name="Y"),
    ]

    graph = ConceptGraph(concepts)

    assert graph.topological_order() == ["a", "b", "y", "z"]
    assert graph.topological_order() == graph.topological_order()


def test_cycle_is_rejected_at_construction() -> None:
    cyclic = [
        Concept(id="a", name="A", prerequisites=["b"]),
        Concept(id="b", name="B", prerequisites=["a"]),
    ]

    with pytest.raises(CyclicGraphError):
        ConceptGraph(cyclic)


def test_unknown_prerequisite_is_rejected() -> None:
    with pytest.raises(ValueError, match="ghost"):
        ConceptGraph([Concept(id="a", name="A", prerequisites=["ghost"])])


def test_unknown_concept_queries_are_rejected() -> None:
    graph = ConceptGraph(CONCEPTS)

    with pytest.raises(KeyError, match="ghost"):
        graph.blocked_by("ghost", _model())
