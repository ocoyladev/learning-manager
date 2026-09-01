from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from learning_manager.api.app import app
from learning_manager.api.deps import ApiRuntime, get_runtime
from learning_manager.contracts import NextSessionDecision


def test_full_happy_path_persists_a_goal_through_the_api() -> None:
    """Catches a route implementation that returns fixtures instead of workflow state."""
    client = TestClient(app)
    created = client.post(
        "/goals",
        json={
            "title": "Kubernetes",
            "purpose": "Interview preparation",
            "deadline": "2026-09-20",
            "daily_minutes": 25,
            "preferred_formats": ["practice"],
        },
    )

    assert created.status_code == 200
    goal_id = created.json()["goal"]["id"]

    diagnostic = client.post(f"/goals/{goal_id}/diagnostic")
    assert diagnostic.status_code == 200
    items = diagnostic.json()["items"]
    assert len(items) >= 5

    answers = [{"item_id": item["id"], "answer": item["expected"]} for item in items]
    model = client.post(f"/goals/{goal_id}/diagnostic/answers", json={"answers": answers})
    assert model.status_code == 200
    assert model.json()["learner_model"]["concepts"]

    researched = client.post(f"/goals/{goal_id}/research", json={"topic": "Kubernetes"})
    assert researched.status_code == 200
    assert researched.json()["sources"]

    session = client.get(f"/goals/{goal_id}/next-session", params={"today": "2026-09-05"})
    assert session.status_code == 200
    assert session.json()["blocks"]
    assert session.json()["session_date"] == "2026-09-05"

    dashboard = client.get(f"/goals/{goal_id}/dashboard")
    assert dashboard.status_code == 200
    assert 0 <= dashboard.json()["progress"] <= 1


def test_all_frozen_routes_and_human_controls_are_available() -> None:
    """Catches a router omission that leaves a frozen UI action unavailable."""
    client = TestClient(app)
    create = client.post(
        "/goals",
        json={
            "title": "Kubernetes",
            "purpose": "Interview preparation",
            "deadline": "2026-09-20",
            "daily_minutes": 25,
            "preferred_formats": ["practice"],
        },
    )
    goal_id = create.json()["goal"]["id"]
    items = client.post(f"/goals/{goal_id}/diagnostic").json()["items"]
    client.post(
        f"/goals/{goal_id}/diagnostic/answers",
        json={"answers": [{"item_id": item["id"], "answer": item["expected"]} for item in items]},
    )
    client.post(f"/goals/{goal_id}/research", json={"topic": "Kubernetes"})
    session = client.get(f"/goals/{goal_id}/next-session", params={"today": "2026-09-05"})
    session_id = session.json()["id"]

    responses = [
        client.get(f"/goals/{goal_id}"),
        client.patch(f"/goals/{goal_id}", json={"paused": True}),
        client.get(f"/goals/{goal_id}/sources"),
        client.post(f"/goals/{goal_id}/recommendations/reject", json={"reason": "Prefer practice"}),
        client.post(f"/sessions/{session_id}/assess", json={"answers": []}),
        client.post(
            f"/sessions/{session_id}/feedback", json={"appropriate": True, "reason": "Good pace"}
        ),
        client.post(f"/sessions/{session_id}/alternative-explanation"),
        client.get(f"/goals/{goal_id}/dashboard"),
        client.post(f"/goals/{goal_id}/simulate-day", json={"days": 1}),
    ]

    assert create.status_code == 200
    assert session.status_code == 200
    assert all(response.status_code == 200 for response in responses)


def test_next_session_obeys_openapi_model_and_explicit_today() -> None:
    """Catches session dates derived from the system clock or invalid route output."""
    client = TestClient(app)
    created = client.post(
        "/goals",
        json={
            "title": "Kubernetes",
            "purpose": "Interview preparation",
            "deadline": "2026-09-20",
            "daily_minutes": 25,
            "preferred_formats": ["practice"],
        },
    )
    goal_id = created.json()["goal"]["id"]
    client.post(f"/goals/{goal_id}/research", json={"topic": "Kubernetes"})

    response = client.get(f"/goals/{goal_id}/next-session", params={"today": "2026-09-05"})

    assert response.status_code == 200
    assert NextSessionDecision.model_validate(response.json()).session_date == date(2026, 9, 5)
    assert client.get(f"/goals/{goal_id}/next-session").status_code == 422


def test_unknown_goal_and_session_ids_are_not_fabricated() -> None:
    """Catches accidental fallback to demo fixtures for missing resources."""
    client = TestClient(app)

    assert client.get("/goals/unknown").status_code == 404
    assert client.post("/sessions/unknown/assess", json={"answers": []}).status_code == 404


def test_dependency_override_uses_supplied_runtime_and_shares_a_request_run_id(tmp_path) -> None:
    """Catches handlers that bypass request-scoped dependency injection."""
    runtime = ApiRuntime.in_memory(trajectory_dir=tmp_path)
    app.dependency_overrides[get_runtime] = lambda: runtime
    try:
        client = TestClient(app)
        created = client.post(
            "/goals",
            json={
                "title": "Kubernetes",
                "purpose": "Interview preparation",
                "deadline": "2026-09-20",
                "daily_minutes": 25,
                "preferred_formats": ["practice"],
            },
        )
        assert created.status_code == 200
        assert len(list(tmp_path.glob("*/*.jsonl"))) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("path", ["/goals", "/goals/not-a-goal"])
def test_frozen_routes_reject_invalid_bodies_or_unknown_ids(path: str) -> None:
    """Catches permissive validation and fabricated goal state."""
    client = TestClient(app)
    if path == "/goals":
        response = client.post(path, json={"title": "missing fields"})
        assert response.status_code == 422
    else:
        assert client.get(path).status_code == 404
