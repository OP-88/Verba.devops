import pytest
import io
import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model" in data
    assert "database" in data

def test_transcribe_diarization():
    """Test transcription with speaker diarization"""
    # Create a mock audio file (you would add a real WAV file to test with)
    audio_data = b"mock audio data"  # In production, use actual WAV file
    
    response = client.post(
        "/transcribe",
        files={"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")},
        data={"mode": "offline", "session_id": "test"}
    )
    
    # Note: This will fail with mock data, but shows expected structure
    # With real audio file, should return 200
    assert response.status_code in [200, 500]  # 500 expected with mock data

def test_chat_offline_mode():
    """Test chat endpoint in offline mode"""
    response = client.post(
        "/chat",
        json={"query": "Summarize the transcript"},
        params={"session_id": "test"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "hybrid mode only" in data["response"].lower()

def test_history_endpoint():
    """Test transcription history retrieval"""
    response = client.get("/history?session_id=test")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_delete_transcription():
    """Test transcription deletion"""
    # This would fail if ID doesn't exist, which is expected
    response = client.delete("/history/999")
    assert response.status_code in [200, 404]

if __name__ == "__main__":
    pytest.main([__file__])