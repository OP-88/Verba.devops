#!/usr/bin/env python3
"""
FastAPI launcher with lifespan events (no deprecation warnings).
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn

# --- lifespan boilerplate ----------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    print("🚀 Verba FastAPI starting...")
    yield
    # shutdown
    print("🛑 Verba FastAPI shutting down...")

app = FastAPI(lifespan=lifespan)

# health check
@app.get("/health")
def health():
    return {"status": "ok"}

# transcription route (stub)
@app.post("/transcribe/file")
def transcribe_file():
    return {"text": "stub - wire your transcription service here"}

# run
if __name__ == "__main__":
    uvicorn.run("run_fastapi_audio_fixed:app", host="0.0.0.0", port=8000, reload=True)
