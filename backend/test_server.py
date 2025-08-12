#!/usr/bin/env python3
"""Minimal FastAPI test server"""
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    print("Starting minimal test server...")
    try:
        uvicorn.run(
            "test_server:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="debug"
        )
    except Exception as e:
        print(f"Server failed to start: {e}")
