from fastapi import FastAPI

app = FastAPI(title="Learning Manager API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
