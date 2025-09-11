// API type definitions for Verba transcription system

export interface TranscriptionResponse {
  id: string;
  text: string;
  confidence: number;
  language: string;
  duration: number;
  segments?: TranscriptionSegment[];
  processing_time: number;
  filename?: string;
  created_at: string;
}

export interface TranscriptionSegment {
  id: number;
  seek: number;
  start: number;
  end: number;
  text: string;
  tokens: number[];
  temperature: number;
  avg_logprob: number;
  compression_ratio: number;
  no_speech_prob: number;
}

export interface TranscriptionHistoryItem {
  id: string;
  transcription: string;
  confidence: number;
  language: string;
  duration?: number;
  audio_duration?: number;
  processing_time?: number;
  filename?: string;
  content_type?: string;
  model_used?: string;
  created_at: string;
}

export interface HealthResponse {
  status: string;
  model: string;
  model_size: string;
  database: string;
  timestamp: string;
}

export interface ApiError {
  detail: string;
  error_code?: string;
}