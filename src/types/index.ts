// Core API Response Types
export interface TranscriptionResult {
  id: number;
  text: string;
  confidence: number;
  language: string;
  duration: number;
  created_at: string;
  file_name: string;
  file_size: number;
  segments: TranscriptionSegment[];
  summary?: string;
  chatbot?: string;
  metadata: { speakers: number; mode?: string };
}

export interface TranscriptionSegment {
  start: number;
  end: number;
  text: string;
}

export interface HealthStatus {
  status: string;
  model: string;
  database: string;
  model_size: string;
  enhanced_features: boolean;
  librosa_available: boolean;
  timestamp: string;
}

// UI Component Types
export interface AudioFile {
  file: File;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  result?: TranscriptionResult;
  error?: string;
}

export interface RecordingState {
  isRecording: boolean;
  isPaused: boolean;
  recordingTime: number;
  audioLevel: number;
  audioBlob: Blob | null;
}

export interface TranscriptionDisplayData {
  segments: Array<{
    speaker: string;
    text: string;
    start: number;
    end: number;
    confidence?: number;
  }>;
  fullText: string;
  confidence: number;
  language: string;
  duration: number;
}

// Export formats
export type ExportFormat = 'txt' | 'json' | 'srt';

// API Error types
export interface ApiError {
  detail: string;
  status_code?: number;
}

// Settings and configuration
export interface AppSettings {
  autoSave: boolean;
  exportFormat: ExportFormat;
  maxFileSize: number;
  supportedFormats: string[];
}