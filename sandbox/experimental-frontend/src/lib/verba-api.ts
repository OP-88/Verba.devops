// src/lib/verba-api.ts
interface TranscriptionResponse {
  text: string;
  processing_time: number;
  vad_segments?: any[];
  ai_analysis?: {
    summary: string;
    key_points: string[];
    action_items: string[];
    sentiment: string;
  };
}

interface ChatResponse {
  response: string;
  processing_time: number;
}

interface HistoryItem {
  id: string;
  filename: string;
  text: string;
  created_at: string;
  ai_analysis?: any;
}

export class VerbaAPI {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  async transcribeFile(file: File, options: {
    enableVAD?: boolean;
    enableAI?: boolean;
  } = {}): Promise<TranscriptionResponse> {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options.enableVAD !== undefined) {
      formData.append('enable_vad', options.enableVAD.toString());
    }
    
    if (options.enableAI !== undefined) {
      formData.append('enable_ai', options.enableAI.toString());
    }

    const response = await fetch(`${this.baseUrl}/transcribe`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Transcription failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async chatWithAI(message: string, context?: string): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        context: context || '',
      }),
    });

    if (!response.ok) {
      throw new Error(`Chat failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async getHistory(): Promise<HistoryItem[]> {
    const response = await fetch(`${this.baseUrl}/history`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch history: ${response.statusText}`);
    }

    return await response.json();
  }

  async getTranscription(id: string): Promise<HistoryItem> {
    const response = await fetch(`${this.baseUrl}/transcription/${id}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch transcription: ${response.statusText}`);
    }

    return await response.json();
  }

  async deleteTranscription(id: string): Promise<boolean> {
    const response = await fetch(`${this.baseUrl}/transcription/${id}`, {
      method: 'DELETE',
    });

    return response.ok;
  }
}

export const verbaApi = new VerbaAPI();
