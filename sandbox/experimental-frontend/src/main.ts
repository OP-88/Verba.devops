// src/main.ts - TypeScript support for Verba Advanced Frontend
import './style.css'

// Type definitions for Verba API
interface TranscriptionResult {
  text: string;
  confidence: number;
  duration: number;
  processing_time: number;
  model_used: string;
  chunks_processed?: number;
  vad_segments?: number;
  metadata?: Record<string, any>;
}

interface TranscriptionResponse {
  transcription_id: number;
  transcription: TranscriptionResult;
  ai_analysis?: string;
  suggested_questions?: string[];
  session_id: string;
}

interface ChatResponse {
  response: string;
  session_id: string;
}

interface Transcription {
  id: number;
  session_id: string;
  title: string;
  transcription_text: string;
  audio_file_path?: string;
  duration_seconds: number;
  confidence_score: number;
  processing_time_ms: number;
  model_used: string;
  chunks_processed: number;
  vad_segments: number;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

interface Reminder {
  id: number;
  session_id: string;
  title: string;
  description?: string;
  due_date?: string;
  reminder_time?: string;
  status: 'pending' | 'completed' | 'overdue';
  priority: 'low' | 'medium' | 'high';
  source_transcription_id?: number;
  created_at: string;
  updated_at: string;
}

interface HealthResponse {
  service: string;
  version: string;
  status: string;
  features: {
    transcription: boolean;
    vad_optimization: boolean;
    ai_analysis: boolean;
    database_storage: boolean;
    conversation_history: boolean;
    reminders: boolean;
    settings: boolean;
  };
}

// Enhanced Verba API Client with TypeScript
class VerbaAPIClient {
  private baseUrl: string;
  public sessionId: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.sessionId = this.generateSessionId();
  }

  private generateSessionId(): string {
    return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
  }

  async checkHealth(): Promise<HealthResponse | null> {
    try {
      const response = await fetch(`${this.baseUrl}/`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json() as HealthResponse;
    } catch (error) {
      console.error('Health check failed:', error);
      return null;
    }
  }

  async transcribeAudio(file: File, title: string = 'Meeting Transcript'): Promise<TranscriptionResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('session_id', this.sessionId);
    formData.append('title', title);

    const response = await fetch(`${this.baseUrl}/transcribe`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Transcription failed: ${response.status} ${response.statusText}`);
    }

    return await response.json() as TranscriptionResponse;
  }

  async chatWithAI(message: string, transcriptionId?: number): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: this.sessionId,
        context_type: 'general_chat',
        transcription_id: transcriptionId || null
      })
    });

    if (!response.ok) {
      throw new Error(`Chat failed: ${response.status} ${response.statusText}`);
    }

    return await response.json() as ChatResponse;
  }

  async getTranscriptions(limit: number = 20, offset: number = 0): Promise<{ transcriptions: Transcription[], session_id: string, count: number }> {
    const response = await fetch(
      `${this.baseUrl}/transcriptions?session_id=${this.sessionId}&limit=${limit}&offset=${offset}`
    );

    if (!response.ok) {
      throw new Error(`Failed to get transcriptions: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  }

  async getTranscription(transcriptionId: number): Promise<Transcription> {
    const response = await fetch(
      `${this.baseUrl}/transcriptions/${transcriptionId}?session_id=${this.sessionId}`
    );

    if (!response.ok) {
      throw new Error(`Failed to get transcription: ${response.status} ${response.statusText}`);
    }

    return await response.json() as Transcription;
  }

  async createReminder(
    title: string,
    description: string = '',
    dueDate?: string,
    priority: 'low' | 'medium' | 'high' = 'medium',
    sourceTranscriptionId?: number
  ): Promise<{ reminder_id: number; message: string; session_id: string }> {
    const response = await fetch(`${this.baseUrl}/reminders`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title,
        description,
        due_date: dueDate || null,
        priority,
        session_id: this.sessionId,
        source_transcription_id: sourceTranscriptionId || null
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to create reminder: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  }

  async getReminders(status?: 'pending' | 'completed' | 'overdue'): Promise<{ reminders: Reminder[], session_id: string, count: number }> {
    let url = `${this.baseUrl}/reminders?session_id=${this.sessionId}`;
    if (status) {
      url += `&status=${status}`;
    }

    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to get reminders: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  }

  async updateReminderStatus(reminderId: number, status: 'pending' | 'completed' | 'overdue'): Promise<{ message: string }> {
    const response = await fetch(
      `${this.baseUrl}/reminders/${reminderId}?status=${status}&session_id=${this.sessionId}`,
      { method: 'PUT' }
    );

    if (!response.ok) {
      throw new Error(`Failed to update reminder: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  }

  async getStats(days: number = 30): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/stats?session_id=${this.sessionId}&days=${days}`
    );

    if (!response.ok) {
      throw new Error(`Failed to get stats: ${response.status} ${response.statusText}`);
    }

    return await response.json();
  }
}

// Application State Management
class VerbaAppState {
  public currentTranscriptionId: number | null = null;
  public isTranscribing: boolean = false;
  public connectionStatus: 'connected' | 'disconnected' | 'error' = 'disconnected';
  
  setTranscriptionId(id: number | null): void {
    this.currentTranscriptionId = id;
  }
  
  setTranscribing(status: boolean): void {
    this.isTranscribing = status;
  }
  
  setConnectionStatus(status: 'connected' | 'disconnected' | 'error'): void {
    this.connectionStatus = status;
  }
}

// UI Controller Class
class VerbaUIController {
  private api: VerbaAPIClient;
  private state: VerbaAppState;

  constructor(api: VerbaAPIClient) {
    this.api = api;
    this.state = new VerbaAppState();
    this.initializeEventListeners();
  }

  private initializeEventListeners(): void {
    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn') as NodeListOf<HTMLButtonElement>;
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const tabId = btn.id.replace('tab-', '');
        this.switchTab(tabId);
      });
    });

    // Transcription
    const transcribeBtn = document.getElementById('transcribeBtn') as HTMLButtonElement;
    transcribeBtn?.addEventListener('click', () => this.handleTranscription());

    const audioInput = document.getElementById('audioInput') as HTMLInputElement;
    audioInput?.addEventListener('change', (e) => this.handleAudioInputChange(e));

    // Chat
    const sendChatBtn = document.getElementById('send-chat') as HTMLButtonElement;
    sendChatBtn?.addEventListener('click', () => this.handleChatMessage());

    const chatInput = document.getElementById('chat-input') as HTMLInputElement;
    chatInput?.addEventListener('keypress', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.handleChatMessage();
      }
    });

    // Reminders
    const addReminderBtn = document.getElementById('add-reminder-btn') as HTMLButtonElement;
    addReminderBtn?.addEventListener('click', () => this.showAddReminderForm());

    const saveReminderBtn = document.getElementById('save-reminder') as HTMLButtonElement;
    saveReminderBtn?.addEventListener('click', () => this.handleCreateReminder());

    const cancelReminderBtn = document.getElementById('cancel-reminder') as HTMLButtonElement;
    cancelReminderBtn?.addEventListener('click', () => this.hideAddReminderForm());

    // History refresh
    const refreshHistoryBtn = document.getElementById('refresh-history') as HTMLButtonElement;
    refreshHistoryBtn?.addEventListener('click', () => this.loadTranscriptionHistory());
  }

  private switchTab(tabId: string): void {
    // Update button states
    const tabBtns = document.querySelectorAll('.tab-btn') as NodeListOf<HTMLButtonElement>;
    tabBtns.forEach(btn => {
      if (btn.id === `tab-${tabId}`) {
        btn.classList.add('active', 'bg-white/20');
        btn.classList.remove('text-white/70');
      } else {
        btn.classList.remove('active', 'bg-white/20');
        btn.classList.add('text-white/70');
      }
    });

    // Update content visibility
    const tabContents = document.querySelectorAll('.tab-content') as NodeListOf<HTMLDivElement>;
    tabContents.forEach(content => {
      if (content.id === `${tabId}-content`) {
        content.classList.remove('hidden');
      } else {
        content.classList.add('hidden');
      }
    });

    // Load data when switching to certain tabs
    if (tabId === 'history') {
      this.loadTranscriptionHistory();
    } else if (tabId === 'reminders') {
      this.loadReminders();
    }
  }

  private handleAudioInputChange(e: Event): void {
    const input = e.target as HTMLInputElement;
    const transcribeBtn = document.getElementById('transcribeBtn') as HTMLButtonElement;
    
    if (input.files && input.files.length > 0) {
      transcribeBtn.disabled = false;
      transcribeBtn.textContent = `🎙️ Transcribe ${input.files[0].name}`;
    }
  }

  private async handleTranscription(): Promise<void> {
    const audioInput = document.getElementById('audioInput') as HTMLInputElement;
    const transcriptionTitle = document.getElementById('transcriptionTitle') as HTMLInputElement;

    if (!audioInput.files || audioInput.files.length === 0) {
      alert('Please select an audio file first');
      return;
    }

    const file = audioInput.files[0];
    const title = transcriptionTitle.value || 'Meeting Transcript';

    try {
      this.state.setTranscribing(true);
      this.showTranscriptionProgress();
      
      const result = await this.api.transcribeAudio(file, title);
      console.log('Transcription result:', result);

      this.hideTranscriptionProgress();
      this.displayTranscriptionResults(result);
      
      this.state.setTranscriptionId(result.transcription_id);

    } catch (error) {
      this.hideTranscriptionProgress();
      console.error('Transcription failed:', error);
      alert(`Transcription failed: ${(error as Error).message}`);
    } finally {
      this.state.setTranscribing(false);
    }
  }

  private showTranscriptionProgress(): void {
    const progress = document.getElementById('transcription-progress') as HTMLDivElement;
    progress.classList.remove('hidden');
    
    const progressBar = progress.querySelector('div div') as HTMLDivElement;
    let width = 0;
    
    const interval = setInterval(() => {
      width += 2;
      progressBar.style.width = `${Math.min(width, 90)}%`;
      
      if (width >= 90) {
        clearInterval(interval);
      }
    }, 100);
  }

  private hideTranscriptionProgress(): void {
    const progress = document.getElementById('transcription-progress') as HTMLDivElement;
    progress.classList.add('hidden');
  }

  private displayTranscriptionResults(result: TranscriptionResponse): void {
    const resultsDiv = document.getElementById('transcription-results') as HTMLDivElement;
    const textDiv = document.getElementById('transcription-text') as HTMLDivElement;
    const aiAnalysisDiv = document.getElementById('ai-analysis') as HTMLDivElement;
    const aiAnalysisText = document.getElementById('ai-analysis-text') as HTMLDivElement;
    const questionsDiv = document.getElementById('suggested-questions') as HTMLDivElement;
    const questionsList = document.getElementById('questions-list') as HTMLDivElement;

    // Show transcription text
    textDiv.textContent = result.transcription.text;
    resultsDiv.classList.remove('hidden');

    // Show AI analysis if available
    if (result.ai_analysis) {
      aiAnalysisText.textContent = result.ai_analysis;
      aiAnalysisDiv.classList.remove('hidden');
    }

    // Show suggested questions if available
    if (result.suggested_questions && result.suggested_questions.length > 0) {
      questionsList.innerHTML = '';
      result.suggested_questions.forEach(question => {
        const questionBtn = document.createElement('button');
        questionBtn.className = 'w-full text-left p-3 bg-white/10 rounded-lg text-white hover:bg-white/20 transition-all';
        questionBtn.textContent = question;
        questionBtn.addEventListener('click', () => {
          this.switchTab('chat');
          const chatInput = document.getElementById('chat-input') as HTMLInputElement;
          chatInput.value = question;
        });
        questionsList.appendChild(questionBtn);
      });
      questionsDiv.classList.remove('hidden');
    }
  }

  private async handleChatMessage(): Promise<void> {
    const chatInput = document.getElementById('chat-input') as HTMLInputElement;
    const message = chatInput.value.trim();
    
    if (!message) return;

    // Add user message to chat
    this.addChatMessage(message, 'user');
    chatInput.value = '';

    try {
      // Send to AI
      const response = await this.api.chatWithAI(message, this.state.currentTranscriptionId || undefined);
      
      // Add AI response to chat
      this.addChatMessage(response.response, 'assistant');

    } catch (error) {
      console.error('Chat failed:', error);
      this.addChatMessage(`Sorry, I encountered an error: ${(error as Error).message}`, 'error');
    }
  }

  private addChatMessage(message: string, type: 'user' | 'assistant' | 'error'): void {
    const chatMessages = document.getElementById('chat-messages') as HTMLDivElement;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message flex ${type === 'user' ? 'justify-end' : 'justify-start'}`;

    const bubble = document.createElement('div');
    bubble.className = `max-w-xs lg:max-w-md px-4 py-2 rounded-xl ${
      type === 'user' 
        ? 'bg-gradient-to-r from-green-400 to-blue-500 text-white' 
        : type === 'error'
        ? 'bg-red-500/80 text-white'
        : 'bg-white/20 text-white'
    }`;
    bubble.textContent = message;

    messageDiv.appendChild(bubble);
    chatMessages.appendChild(messageDiv);

    // Clear welcome message if it exists
    const welcome = chatMessages.querySelector('.text-white\\/60');
    if (welcome?.parentElement) {
      welcome.parentElement.remove();
    }

    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  private async loadTranscriptionHistory(): Promise<void> {
    try {
      const historyData = await this.api.getTranscriptions(20, 0);
      this.displayTranscriptionHistory(historyData.transcriptions);
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  }

  private displayTranscriptionHistory(transcriptions: Transcription[]): void {
    const historyList = document.getElementById('history-list') as HTMLDivElement;
    historyList.innerHTML = '';

    if (transcriptions.length === 0) {
      historyList.innerHTML = `
        <div class="text-center text-white/60 py-12">
          <div class="text-4xl mb-4">📋</div>
          <p>No transcriptions yet. Upload your first audio file!</p>
        </div>
      `;
      return;
    }

    transcriptions.forEach(transcription => {
      const card = document.createElement('div');
      card.className = 'transcription-card bg-white/10 rounded-xl p-6 cursor-pointer';
      
      const date = new Date(transcription.created_at).toLocaleDateString();
      const preview = transcription.transcription_text.substring(0, 150) + '...';
      
      card.innerHTML = `
        <div class="flex justify-between items-start mb-3">
          <h3 class="text-lg font-semibold text-white">${transcription.title}</h3>
          <span class="text-sm text-white/60">${date}</span>
        </div>
        <p class="text-white/80 text-sm mb-3">${preview}</p>
        <div class="flex justify-between items-center">
          <div class="text-xs text-white/60">
            Duration: ${transcription.duration_seconds}s | 
            Confidence: ${(transcription.confidence_score * 100).toFixed(1)}%
          </div>
          <button class="text-blue-300 hover:text-blue-200 text-sm">View Details →</button>
        </div>
      `;
      
      card.addEventListener('click', () => {
        console.log('View transcription:', transcription.id);
        // Could implement detailed view here
      });
      
      historyList.appendChild(card);
    });
  }

  private showAddReminderForm(): void {
    const addReminderForm = document.getElementById('add-reminder-form') as HTMLDivElement;
    addReminderForm.classList.remove('hidden');
  }

  private hideAddReminderForm(): void {
    const addReminderForm = document.getElementById('add-reminder-form') as HTMLDivElement;
    addReminderForm.classList.add('hidden');
    this.clearReminderForm();
  }

  private clearReminderForm(): void {
    (document.getElementById('reminder-title') as HTMLInputElement).value = '';
    (document.getElementById('reminder-description') as HTMLTextAreaElement).value = '';
    (document.getElementById('reminder-due-date') as HTMLInputElement).value = '';
    (document.getElementById('reminder-priority') as HTMLSelectElement).value = 'medium';
  }

  private async handleCreateReminder(): Promise<void> {
    const titleInput = document.getElementById('reminder-title') as HTMLInputElement;
    const descriptionInput = document.getElementById('reminder-description') as HTMLTextAreaElement;
    const dueDateInput = document.getElementById('reminder-due-date') as HTMLInputElement;
    const priorityInput = document.getElementById('reminder-priority') as HTMLSelectElement;

    const title = titleInput.value.trim();
    const description = descriptionInput.value.trim();
    const dueDate = dueDateInput.value;
    const priority = priorityInput.value as 'low' | 'medium' | 'high';

    if (!title) {
      alert('Please enter a reminder title');
      return;
    }

    try {
      await this.api.createReminder(
        title, 
        description, 
        dueDate || undefined, 
        priority, 
        this.state.currentTranscriptionId || undefined
      );
      
      this.hideAddReminderForm();
      this.loadReminders();
    } catch (error) {
      console.error('Failed to create reminder:', error);
      alert(`Failed to create reminder: ${(error as Error).message}`);
    }
  }

  private async loadReminders(): Promise<void> {
    try {
      const remindersData = await this.api.getReminders();
      this.displayReminders(remindersData.reminders);
    } catch (error) {
      console.error('Failed to load reminders:', error);
    }
  }

  private displayReminders(reminders: Reminder[]): void {
    const remindersList = document.getElementById('reminders-list') as HTMLDivElement;
    remindersList.innerHTML = '';

    if (reminders.length === 0) {
      remindersList.innerHTML = `
        <div class="text-center text-white/60 py-12">
          <div class="text-4xl mb-4">⏰</div>
          <p>No reminders yet. Add your first reminder!</p>
        </div>
      `;
      return;
    }

    reminders.forEach(reminder => {
      const card = document.createElement('div');
      card.className = 'bg-white/10 rounded-xl p-6 mb-4';
      
      const dueDate = reminder.due_date ? new Date(reminder.due_date).toLocaleDateString() : 'No due date';
      const priorityColors = {
        low: 'bg-green-500',
        medium: 'bg-yellow-500', 
        high: 'bg-red-500'
      };
      
      card.innerHTML = `
        <div class="flex justify-between items-start mb-3">
          <div class="flex items-center gap-3">
            <span class="w-3 h-3 rounded-full ${priorityColors[reminder.priority]}"></span>
            <h3 class="text-lg font-semibold text-white">${reminder.title}</h3>
          </div>
          <div class="flex gap-2">
            ${reminder.status === 'pending' ? 
              `<button class="complete-reminder bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600" data-id="${reminder.id}">✅ Complete</button>` : 
              `<span class="text-green-400 text-sm">✅ Completed</span>`
            }
          </div>
        </div>
        ${reminder.description ? `<p class="text-white/80 text-sm mb-3">${reminder.description}</p>` : ''}
        <div class="text-xs text-white/60">
          Due: ${dueDate} | Priority: ${reminder.priority.charAt(0).toUpperCase() + reminder.priority.slice(1)}
        </div>
      `;
      
      // Add complete button functionality
      const completeBtn = card.querySelector('.complete-reminder') as HTMLButtonElement;
      if (completeBtn) {
        completeBtn.addEventListener('click', async () => {
          try {
            await this.api.updateReminderStatus(reminder.id, 'completed');
            this.loadReminders(); // Refresh the list
          } catch (error) {
            console.error('Failed to complete reminder:', error);
          }
        });
      }
      
      remindersList.appendChild(card);
    });
  }

  async updateConnectionStatus(): Promise<void> {
    const connectionStatus = document.getElementById('connection-status') as HTMLDivElement;
    
    try {
      const health = await this.api.checkHealth();
      if (health) {
        connectionStatus.innerHTML = '✅ Connected to Verba API';
        connectionStatus.className = 'mt-4 p-2 rounded-lg glass text-green-300 text-sm';
        this.state.setConnectionStatus('connected');
        console.log('Verba API Status:', health);
      } else {
        connectionStatus.innerHTML = '❌ Failed to connect to Verba API';
        connectionStatus.className = 'mt-4 p-2 rounded-lg glass text-red-300 text-sm';
        this.state.setConnectionStatus('error');
      }
    } catch (error) {
      connectionStatus.innerHTML = '❌ Connection error - Check if backend is running on port 8000';
      connectionStatus.className = 'mt-4 p-2 rounded-lg glass text-red-300 text-sm';
      this.state.setConnectionStatus('error');
      console.error('Connection error:', error);
    }
  }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
  const api = new VerbaAPIClient('http://localhost:8000');
  const uiController = new VerbaUIController(api);
  
  // Update connection status
  uiController.updateConnectionStatus();
  
  // Add initial welcome message to chat
  setTimeout(() => {
    const chatMessages = document.getElementById('chat-messages') as HTMLDivElement;
    if (chatMessages.children.length <= 1) {
      const messageDiv = document.createElement('div');
      messageDiv.className = 'chat-message flex justify-start';

      const bubble = document.createElement('div');
      bubble.className = 'max-w-xs lg:max-w-md px-4 py-2 rounded-xl bg-white/20 text-white';
      bubble.textContent = "Hi! I'm your AI meeting assistant. I can help you analyze transcriptions, answer questions, and manage your meetings. Try uploading an audio file first!";

      messageDiv.appendChild(bubble);
      chatMessages.appendChild(messageDiv);
    }
  }, 1000);
});

// Export types and classes for potential use in other modules
export {
  VerbaAPIClient,
  VerbaUIController,
  VerbaAppState,
  type TranscriptionResult,
  type TranscriptionResponse,
  type ChatResponse,
  type Transcription,
  type Reminder,
  type HealthResponse
};
