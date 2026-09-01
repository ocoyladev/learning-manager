from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response

from learning_manager.api.routers import dashboard, goals, sessions, simulation

app = FastAPI(title="Learning Manager API")


@app.middleware("http")
async def add_request_run_id(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request.state.run_id = str(uuid4())
    return await call_next(request)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(goals.router)
app.include_router(sessions.router)
app.include_router(dashboard.router)
app.include_router(simulation.router)
