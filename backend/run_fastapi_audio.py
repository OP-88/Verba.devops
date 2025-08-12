#!/usr/bin/env python3
from verba_gui_integration import VerbaFastAPIAudio
import uvicorn

if __name__ == "__main__":
    audio_app = VerbaFastAPIAudio()
    print("🚀 Starting FastAPI server...")
    print("📱 Open http://localhost:8000 in your browser")
    uvicorn.run(audio_app.app, host="0.0.0.0", port=8000, reload=True)
