#!/bin/bash
# Quick fix script for Verba 422 errors
# Run this from ~/verba directory

echo "🔧 Fixing Verba 422 Errors..."

# Navigate to frontend directory
cd ~/verba-frontend-ts/src/services/

# Backup original file
cp api.ts api.ts.backup

# Create fixed api.ts - THE KEY FIX: Add session_id parameter
cat > api.ts << 'EOF'
import { TranscriptionResponse, TranscriptionHistoryItem } from '../types/api';

const API_BASE_URL = 'http://localhost:8000';

class ApiService {
  async getTranscriptions(sessionId: string = 'default'): Promise<TranscriptionHistoryItem[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/transcriptions?session_id=${sessionId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching transcriptions:', error);
      throw error;
    }
  }

  async transcribeAudio(audioFile: File): Promise<TranscriptionResponse> {
    try {
      const formData = new FormData();
      formData.append('audio', audioFile);
      
      const response = await fetch(`${API_BASE_URL}/transcribe`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Transcription error:', errorData);
        throw new Error(`Transcription failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error transcribing audio:', error);
      throw error;
    }
  }

  async checkHealth() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  }
}

export const apiService = new ApiService();
EOF

echo "✅ Fixed api.ts with session_id parameter"
echo ""
echo "🎯 Now restart your frontend:"
echo "cd ~/verba-frontend-ts/"
echo "npm run dev"
