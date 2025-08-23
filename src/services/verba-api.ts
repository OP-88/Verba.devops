// src/services/verba-api.ts
export interface TranscriptionResult {
  success: boolean;
  transcription?: string;
  confidence?: number;
  processing_time?: number;
  transcription_id?: string;
  segments?: any[];
  error?: string;
}

export interface AIResponse {
  success: boolean;
  response?: string;
  conversation_id?: string;
  timestamp?: string;
  error?: string;
  fallback?: string;
}

export interface Settings {
  theme?: string;
  model?: string;
  language?: string;
  auto_save?: boolean;
  vad_enabled?: boolean;
}

class VerbaAPI {
  private baseUrl: string = 'http://localhost:8000';
  private sessionId: string | null = null;

  constructor() {
    this.initSession();
  }

  private async initSession(): Promise<void> {
    this.sessionId = localStorage.getItem('verba_session_id');
    
    if (!this.sessionId) {
      try {
        const response = await fetch(`${this.baseUrl}/session/new`);
        const data = await response.json();
        this.sessionId = data.session_id;
        localStorage.setItem('verba_session_id', this.sessionId);
      } catch (error) {
        this.sessionId = `local-${Date.now()}`;
        localStorage.setItem('verba_session_id', this.sessionId);
      }
    }
  }

  private async ensureSession(): Promise<string> {
    if (!this.sessionId) {
      await this.initSession();
    }
    return this.sessionId!;
  }

  async transcribeAudio(audioFile: File, options: Partial<Settings> = {}): Promise<TranscriptionResult> {
    const sessionId = await this.ensureSession();
    
    const formData = new FormData();
    formData.append('audio', audioFile);
    formData.append('session_id', sessionId);
    
    if (options.model) formData.append('model', options.model);
    if (options.language) formData.append('language', options.language);

    try {
      const response = await fetch(`${this.baseUrl}/transcribe`, {
        method: 'POST',
        body: formData
      });

      const result = await response.json();
      
      if (response.ok) {
        return {
          success: true,
          transcription: result.transcription,
          confidence: result.confidence,
          processing_time: result.processing_time,
          transcription_id: result.transcription_id,
          segments: result.segments || []
        };
      } else {
        return { success: false, error: result.detail || 'Transcription failed' };
      }
    } catch (error: any) {
      return { success: false, error: error.message };
    }
  }

  async chatWithAI(message: string, conversationId?: string): Promise<AIResponse> {
    const sessionId = await this.ensureSession();
    
    const payload = {
      session_id: sessionId,
      message: message,
      conversation_id: conversationId || `conv-${Date.now()}`
    };

    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      
      if (response.ok) {
        return {
          success: true,
          response: result.response,
          conversation_id: result.conversation_id,
          timestamp: result.timestamp
        };
      } else {
        return { 
          success: false, 
          error: result.detail || 'AI service unavailable',
          fallback: "AI temporarily unavailable - your message was saved."
        };
      }
    } catch (error: any) {
      return { 
        success: false, 
        error: error.message,
        fallback: "Connection error - please try again."
      };
    }
  }

  async saveSettings(settings: Settings): Promise<{ success: boolean; source?: string }> {
    const sessionId = await this.ensureSession();
    
    try {
      const response = await fetch(`${this.baseUrl}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          settings: settings
        })
      });

      if (response.ok) {
        localStorage.setItem('verba_settings', JSON.stringify(settings));
        return { success: true };
      }
    } catch (error) {
      localStorage.setItem('verba_settings', JSON.stringify(settings));
      return { success: true, source: 'local' };
    }
    
    return { success: false };
  }

  async loadSettings(): Promise<Settings> {
    const sessionId = await this.ensureSession();
    
    try {
      const response = await fetch(`${this.baseUrl}/settings?session_id=${sessionId}`);
      const data = await response.json();
      
      if (response.ok && data.settings) {
        return data.settings;
      }
    } catch (error) {
      console.log('Using local settings fallback');
    }
    
    const backup = localStorage.getItem('verba_settings');
    return backup ? JSON.parse(backup) : {
      theme: 'dark',
      model: 'tiny',
      language: 'en',
      auto_save: true,
      vad_enabled: true
    };
  }

  async getTranscriptionHistory(): Promise<any[]> {
    const sessionId = await this.ensureSession();
    
    try {
      const response = await fetch(`${this.baseUrl}/transcriptions?session_id=${sessionId}`);
      const data = await response.json();
      return response.ok ? data.transcriptions : [];
    } catch (error) {
      return [];
    }
  }

  async getConversationHistory(): Promise<any[]> {
    const sessionId = await this.ensureSession();
    
    try {
      const response = await fetch(`${this.baseUrl}/conversations?session_id=${sessionId}`);
      const data = await response.json();
      return response.ok ? data.conversations : [];
    } catch (error) {
      return [];
    }
  }
}

export const verbaAPI = new VerbaAPI();
