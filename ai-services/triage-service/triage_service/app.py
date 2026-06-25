from fastapi import FastAPI

app = FastAPI(title="InsureFlow AI Triage Service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "triage-service"}
