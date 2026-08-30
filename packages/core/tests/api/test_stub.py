import asyncio
import json
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import pytest

from learning_manager.api.stub import app


def request(method: str, path: str, **kwargs: Any) -> httpx.Response:
    async def run() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(run())


def test_create_goal_returns_deterministic_typed_fixture() -> None:
    response = request(
        "POST",
        "/goals",
        json={
            "title": "Learn containers",
            "purpose": "Build reliable services",
            "deadline": "2026-09-20",
            "daily_minutes": 30,
            "preferred_formats": ["examples"],
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "goal": {
            "id": "demo",
            "title": "Learn containers",
            "purpose": "Build reliable services",
            "deadline": "2026-09-20",
            "daily_minutes": 30,
            "preferred_formats": ["examples"],
            "success_criteria": [],
        },
        "concepts": [
            {
                "id": "containers-basics",
                "name": "Container basics",
                "prerequisites": [],
                "importance": 1.0,
                "estimated_minutes": 15,
            }
        ],
    }


def test_goal_diagnostic_research_session_assessment_and_dashboard() -> None:
    goal = request("GET", "/goals/custom-id")
    assert goal.status_code == 200
    assert goal.json()["goal"]["id"] == "custom-id"
    assert goal.json()["learner_model"]["concepts"]["containers-basics"]["mastery"] == 0.4

    diagnostic = request("POST", "/goals/custom-id/diagnostic")
    assert diagnostic.json() == {
        "items": [
            {
                "id": "diagnostic-1",
                "concept_id": "containers-basics",
                "question": "What does a container isolate?",
                "options": ["Process and dependencies", "An entire physical machine"],
                "expected": "Process and dependencies",
                "explanation": (
                    "A container isolates a process and its dependencies while sharing "
                    "the host kernel."
                ),
            }
        ]
    }
    answers = request(
        "POST",
        "/goals/custom-id/diagnostic/answers",
        json={"answers": [{"item_id": "diagnostic-1", "answer": "Process and dependencies"}]},
    )
    assert answers.status_code == 200
    assert answers.json()["learner_model"]["concepts"]["containers-basics"]["state"] == "developing"

    research = request("POST", "/goals/custom-id/research", json={"topic": "containers"})
    assert research.json()["sources"] == [
        {
            "id": "source-official",
            "url": "https://docs.docker.com/get-started/",
            "title": "Docker Get Started",
            "authority": "official",
            "version": None,
            "published_at": None,
            "retrieved_at": "2026-08-30",
            "content_path": None,
        }
    ]

    session = request("GET", "/goals/custom-id/next-session?today=2026-09-05")
    assert session.status_code == 200
    assert session.json()["session_date"] == "2026-09-05"
    assert session.json()["blocks"][0]["source_ids"] == ["source-official"]
    assert session.json()["total_minutes"] == 15

    assessment = request(
        "POST",
        "/sessions/session-demo/assess",
        json={"answers": [{"item_id": "diagnostic-1", "answer": "Process and dependencies"}]},
    )
    assert assessment.json()["results"] == [
        {
            "concept_id": "containers-basics",
            "score": 1.0,
            "correct": 1,
            "total": 1,
            "misconceptions": [],
            "evidence": ["Correctly explained process and dependency isolation."],
        }
    ]

    dashboard = request("GET", "/goals/custom-id/dashboard")
    assert dashboard.json() == {
        "progress": 0.4,
        "on_track": True,
        "deadline_status": "on_track",
        "strong": [],
        "weak": ["containers-basics"],
        "next_review": "2026-09-01",
        "why": "Container basics is the weakest prerequisite.",
        "estimated_sessions": 4,
        "projected_completion": "2026-09-20",
    }


def test_typed_validation_covers_answers_today_and_simulation_days() -> None:
    assert (
        request("POST", "/goals/demo/diagnostic/answers", json={"answers": [{}]}).status_code == 422
    )
    assert request("POST", "/goals/demo/research", json={"topic": 3}).status_code == 422
    assert request("GET", "/goals/demo/next-session").status_code == 422
    assert request("POST", "/goals/demo/simulate-day", json={"days": 0}).status_code == 422
    assert request("POST", "/goals/demo/simulate-day", json={"days": 366}).status_code == 422

    simulation = request("POST", "/goals/demo/simulate-day", json={"days": 3})
    assert simulation.json() == {
        "events": [
            {"day": 1, "kind": "notification", "message": "Review container basics."},
            {"day": 2, "kind": "notification", "message": "Review container basics."},
            {"day": 3, "kind": "notification", "message": "Review container basics."},
        ]
    }


def test_openapi_matches_generated_app_schema_and_is_stable() -> None:
    schema_path = Path(__file__).parents[4] / "openapi.json"
    schema = json.loads(schema_path.read_text())
    assert schema == app.openapi()
    assert schema_path.read_text().endswith("\n")
    assert schema_path.read_text() == json.dumps(schema, indent=2, sort_keys=True) + "\n"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/goals"),
        ("GET", "/goals/demo"),
        ("POST", "/goals/demo/diagnostic"),
        ("POST", "/goals/demo/diagnostic/answers"),
        ("POST", "/goals/demo/research"),
        ("GET", "/goals/demo/next-session?today=2026-09-05"),
        ("POST", "/sessions/session-demo/assess"),
        ("GET", "/goals/demo/dashboard"),
        ("POST", "/goals/demo/simulate-day"),
    ],
)
def test_required_route_is_registered(method: str, path: str) -> None:
    response = request(
        method,
        path,
        json=(
            {
                "title": "t",
                "purpose": "p",
                "deadline": date(2026, 9, 20).isoformat(),
                "daily_minutes": 5,
                "preferred_formats": [],
            }
            if path == "/goals"
            else {"answers": []}
            if "answers" in path or "/assess" in path
            else {"topic": "t"}
            if "/research" in path
            else {"days": 1}
            if "simulate-day" in path
            else None
        ),
    )
    assert response.status_code != 404
