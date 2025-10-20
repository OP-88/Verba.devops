import { TranscriptionResult } from '@/types';

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Transcription {
  id?: number;
  text: string;
  summary?: string;
  chatbot?: string;
  metadata: { speakers: number; mode?: string };
  created_at?: string;
  file_name?: string;
  duration?: number;
  language?: string;
  confidence?: number;
  segments?: Array<{
    start: number;
    end: number;
    text: string;
  }>;
}

export class ApiService {
  async getHistory(session_id: string = 'default'): Promise<Transcription[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/history?session_id=${session_id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch transcriptions:', error);
      throw error;
    }
  }

  async deleteTranscription(id: number): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/history/${id}`, {
        method: 'DELETE'
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Failed to delete transcription:', error);
      throw error;
    }
  }

  async transcribeAudio(audioBlob: Blob, mode: string = 'offline'): Promise<Transcription> {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.wav');
      formData.append('mode', mode);
      formData.append('session_id', 'default');
      
      const response = await fetch(`${API_BASE_URL}/transcribe`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('Transcription error:', errorData);
        throw new Error(`Transcription failed: ${response.status} - ${errorData.detail}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error transcribing audio:', error);
      throw error;
    }
  }

  async transcribeFile(file: File, mode: string = 'offline'): Promise<Transcription> {
    try {
      const formData = new FormData();
      formData.append('audio', file);
      formData.append('mode', mode);
      formData.append('session_id', 'default');
      
      const response = await fetch(`${API_BASE_URL}/transcribe`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('File transcription error:', errorData);
        throw new Error(`File transcription failed: ${response.status} - ${errorData.detail}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error transcribing file:', error);
      throw error;
    }
  }

  async chatWithAI(query: string, session_id: string = 'default'): Promise<string> {
    try {
      const response = await fetch(`${API_BASE_URL}/chat?session_id=${session_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      return result.response;
    } catch (error) {
      console.error('Chat error:', error);
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