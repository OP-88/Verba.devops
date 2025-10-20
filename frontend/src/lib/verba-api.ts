// src/lib/verba-api.ts - Connects to your ACTUAL backend
interface TranscriptionRequest {
  title?: string;
  session_id?: string;
}

interface ChatRequest {
  message: string;
  session_id: string;
  context_type?: string;
  transcription_id?: number;
}

interface ReminderRequest {
  title: string;
  description?: string;
  due_date?: string;
  priority?: 'low' | 'medium' | 'high';
  session_id: string;
  source_transcription_id?: number;
}

class VerbaRealAPI {
  private baseUrl: string;
  private sessionId: string | null = null;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  // Create new session
  async createSession(): Promise<string> {
    const response = await fetch(`${this.baseUrl}/session/new`);
    const data = await response.json();
    this.sessionId = data.session_id;
    return this.sessionId;
  }

  // Get or create session ID
  async getSessionId(): Promise<string> {
    if (!this.sessionId) {
      await this.createSession();
    }
    return this.sessionId!;
  }

  // Transcribe audio file
  async transcribeAudio(file: File, title: string = "Meeting Transcript"): Promise<any> {
    const sessionId = await this.getSessionId();
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(
      `${this.baseUrl}/transcribe?session_id=${sessionId}&title=${encodeURIComponent(title)}`,
      {
        method: 'POST',
        body: formData
      }
    );

    if (!response.ok) {
      throw new Error(`Transcription failed: ${response.statusText}`);
    }

    return response.json();
  }

  // Chat with AI
  async chatWithAI(message: string, transcriptionId?: number): Promise<string> {
    const sessionId = await this.getSessionId();
    
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        context_type: 'general_chat',
        transcription_id: transcriptionId
      })
    });

    if (!response.ok) {
      throw new Error(`Chat failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.response;
  }

  // Get transcription history
  async getTranscriptions(limit: number = 20, offset: number = 0): Promise<any> {
    const sessionId = await this.getSessionId();
    
    const response = await fetch(
      `${this.baseUrl}/transcriptions?session_id=${sessionId}&limit=${limit}&offset=${offset}`
    );
    
    return response.json();
  }

  // Get single transcription
  async getTranscription(transcriptionId: number): Promise<any> {
    const sessionId = await this.getSessionId();
    
    const response = await fetch(
      `${this.baseUrl}/transcriptions/${transcriptionId}?session_id=${sessionId}`
    );
    
    return response.json();
  }

  // Create reminder
  async createReminder(reminder: Omit<ReminderRequest, 'session_id'>): Promise<any> {
    const sessionId = await this.getSessionId();
    
    const response = await fetch(`${this.baseUrl}/reminders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...reminder,
        session_id: sessionId
      })
    });

    return response.json();
  }

  // Get reminders
  async getReminders(status?: string): Promise<any> {
    const sessionId = await this.getSessionId();
    
    const url = `${this.baseUrl}/reminders?session_id=${sessionId}${status ? `&status=${status}` : ''}`;
    const response = await fetch(url);
    
    return response.json();
  }

  // Update reminder status
  async updateReminderStatus(reminderId: number, status: 'pending' | 'completed' | 'overdue'): Promise<any> {
    const sessionId = await this.getSessionId();
    
    const response = await fetch(
      `${this.baseUrl}/reminders/${reminderId}?status=${status}&session_id=${sessionId}`,
      { method: 'PUT' }
    );

    return response.json();
  }

  // Get conversation history
  async getConversations(conversationId?: string, limit: number = 50): Promise<any> {
    const sessionId = await this.getSessionId();
    
    const url = `${this.baseUrl}/conversations?session_id=${sessionId}&limit=${limit}${
      conversationId ? `&conversation_id=${conversationId}` : ''
    }`;
    
    const response = await fetch(url);
    return response.json();
  }

  // Save settings
  async saveSettings(settings: Record<string, any>): Promise<any> {
    const sessionId = await this.getSessionId();
    
    const response = await fetch(`${this.baseUrl}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        settings
      })
    });

    return response.json();
  }

  // Get settings
  async getSettings(): Promise<any> {
    const sessionId = await this.getSessionId();
    
    const response = await fetch(`${this.baseUrl}/settings?session_id=${sessionId}`);
    return response.json();
  }

  // Get usage statistics
  async getStats(days: number = 30): Promise<any> {
    const sessionId = await this.getSessionId();
    
    const response = await fetch(`${this.baseUrl}/stats?session_id=${sessionId}&days=${days}`);
    return response.json();
  }
}

export default new VerbaRealAPI();
