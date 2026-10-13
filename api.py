"""SpamShield API — local-only FastAPI backend serving the TypeScript frontend.

Run:
    pip install -r requirements.txt
    python api.py
    # -> http://127.0.0.1:8000  (serves frontend/dist when built, else API only)

Dev frontend (Vite HMR):
    cd frontend && npm install && npm run dev   # proxies /api -> 127.0.0.1:8000

Privacy: no network calls, no message persistence, never logs message contents.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

logger = logging.getLogger("spamshield.api")  # never log message contents

BASE_DIR = Path(__file__).resolve().parent
EVAL_PATH = BASE_DIR / "reports" / "evaluation.json"
COMPARE_PATH = BASE_DIR / "reports" / "model_comparison.json"
CM_PATH = BASE_DIR / "reports" / "confusion_matrix.png"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

app = FastAPI(
    title="SpamShield API",
    version="2.0.0",
    description="Local-only suspicious-message analyzer. No message leaves this machine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    text: str = Field(default="", max_length=5000)


def _read_json(path: Path) -> dict | None:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - corrupt report is non-fatal
            logger.warning("Could not read %s", path.name)
    return None


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "spamshield"}


@app.get("/api/status")
def status() -> dict:
    from spamshield.predictor import model_status

    return model_status()


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    from spamshield.predictor import analyze_message

    # Deliberately never log req.text (privacy: no message contents in logs).
    return analyze_message(req.text)


@app.get("/api/evaluation")
def evaluation() -> dict:
    return {
        "evaluation": _read_json(EVAL_PATH),
        "comparison": _read_json(COMPARE_PATH),
        "has_confusion_matrix": CM_PATH.exists(),
    }


@app.get("/api/confusion-matrix")
def confusion_matrix():
    if not CM_PATH.exists():
        return {"detail": "No confusion matrix found. Run: python train.py"}
    return FileResponse(str(CM_PATH), media_type="image/png")


# Serve the built TypeScript frontend (production: `cd frontend && npm run build`).
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000, log_level="info")
