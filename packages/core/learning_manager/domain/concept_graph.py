"""Concept prerequisite graph and deterministic learner gating."""

from __future__ import annotations

from collections import defaultdict

from learning_manager.contracts import PREREQ_THRESHOLD, Concept, LearnerModel


class CyclicGraphError(ValueError):
    """Raised when concept prerequisites do not form a directed acyclic graph."""


class ConceptGraph:
    """An immutable-in-practice graph of concepts and their prerequisites."""

    def __init__(self, concepts: list[Concept]) -> None:
        self._concepts = {concept.id: concept for concept in concepts}
        if len(self._concepts) != len(concepts):
            raise ValueError("concept IDs must be unique")

        for concept in concepts:
            unknown = sorted(set(concept.prerequisites) - self._concepts.keys())
            if unknown:
                raise ValueError(
                    f"concept {concept.id!r} has unknown prerequisite(s): {', '.join(unknown)}"
                )

        self._order = self._compute_topological_order()

    def _compute_topological_order(self) -> list[str]:
        dependents: dict[str, list[str]] = defaultdict(list)
        indegree = {concept_id: 0 for concept_id in self._concepts}
        for concept in self._concepts.values():
            for prerequisite in concept.prerequisites:
                dependents[prerequisite].append(concept.id)
                indegree[concept.id] += 1

        available = sorted(concept_id for concept_id, degree in indegree.items() if degree == 0)
        order: list[str] = []
        while available:
            concept_id = available.pop(0)
            order.append(concept_id)
            for dependent in sorted(dependents[concept_id]):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    available.append(dependent)
            available.sort()

        if len(order) != len(self._concepts):
            raise CyclicGraphError("concept prerequisite graph contains a cycle")
        return order

    def topological_order(self) -> list[str]:
        """Return concept IDs in deterministic prerequisite-first order."""
        return list(self._order)

    def detect_cycle(self) -> list[str] | None:
        """Return ``None`` for this validated acyclic graph.

        Cyclic graphs are rejected during construction, so this method is useful
        to callers that want an explicit validation result after construction.
        """
        return None

    def blocked_by(self, concept_id: str, model: LearnerModel) -> list[str]:
        """Return prerequisites that are absent or below the unlock threshold."""
        concept = self._concepts.get(concept_id)
        if concept is None:
            raise KeyError(f"unknown concept: {concept_id}")

        return [
            prerequisite
            for prerequisite in concept.prerequisites
            if (
                prerequisite not in model.concepts
                or model.concepts[prerequisite].mastery < PREREQ_THRESHOLD
            )
        ]

    def unlocked(self, model: LearnerModel) -> list[str]:
        """Return concepts whose prerequisites satisfy the mastery threshold."""
        return [concept_id for concept_id in self._order if not self.blocked_by(concept_id, model)]
