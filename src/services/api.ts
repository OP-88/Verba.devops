// ~/verba-frontend-ts/src/services/api.ts
// Fixed version addressing both 422 errors

import { TranscriptionResponse, TranscriptionHistoryItem } from '../types/api';

const API_BASE_URL = 'http://localhost:8000';

class ApiService {
  // Fixed: Add session_id parameter to transcriptions
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

  // Fixed: Proper FormData handling without manual Content-Type
  async transcribeAudio(audioFile: File): Promise<TranscriptionResponse> {
    try {
      const formData = new FormData();
      formData.append('audio', audioFile);
      
      // CRITICAL: Do NOT set Content-Type header manually
      // Browser will set it automatically with boundary for multipart/form-data
      const response = await fetch(`${API_BASE_URL}/transcribe`, {
        method: 'POST',
        body: formData
        // No headers! Let browser handle Content-Type
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
