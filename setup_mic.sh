#!/bin/bash
# Setup microphone recording for Verba

echo "🎤 Setting up microphone recording for Verba..."

cd ~/verba-frontend-ts/src/components/

# Create MicrophoneRecorder component
cat > MicrophoneRecorder.tsx << 'EOF'
import React, { useState, useRef, useEffect } from 'react';
import { apiService } from '../services/api';
import { TranscriptionResponse } from '../types/api';

interface MicrophoneRecorderProps {
  onTranscriptionComplete: (transcription: TranscriptionResponse) => void;
  onError: (error: string) => void;
}

export const MicrophoneRecorder: React.FC<MicrophoneRecorderProps> = ({ 
  onTranscriptionComplete, 
  onError 
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const animationRef = useRef<number | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const updateAudioLevel = () => {
    if (analyserRef.current) {
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);
      
      const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
      setAudioLevel(average / 255 * 100);
      
      if (isRecording) {
        animationRef.current = requestAnimationFrame(updateAudioLevel);
      }
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      audioStreamRef.current = stream;
      chunksRef.current = [];

      audioContextRef.current = new AudioContext();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);

      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        await processRecording();
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      updateAudioLevel();

    } catch (error) {
      console.error('Error starting recording:', error);
      onError('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerRef.current) clearInterval(timerRef.current);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    }
  };

  const processRecording = async () => {
    setIsProcessing(true);
    
    try {
      const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
      const audioFile = new File([audioBlob], `recording_${Date.now()}.webm`, {
        type: 'audio/webm'
      });

      const result = await apiService.transcribeAudio(audioFile);
      onTranscriptionComplete(result);
      
    } catch (error) {
      console.error('Error processing recording:', error);
      onError('Failed to process recording. Please try again.');
    } finally {
      setIsProcessing(false);
      setAudioLevel(0);
    }
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-white/10 backdrop-blur rounded-lg p-6 border border-white/20">
      <div className="text-center">
        <h3 className="text-xl font-semibold text-white mb-4 flex items-center justify-center">
          🎤 Voice Recording
        </h3>

        {isRecording && (
          <div className="mb-4">
            <div className="flex items-center justify-center space-x-4 mb-2">
              <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
              <span className="text-red-400 font-mono text-lg">
                REC {formatTime(recordingTime)}
              </span>
            </div>
            
            <div className="w-full max-w-xs mx-auto mb-4">
              <div className="bg-gray-700 h-2 rounded-full overflow-hidden">
                <div 
                  className="bg-green-500 h-full transition-all duration-100"
                  style={{ width: `${Math.min(audioLevel, 100)}%` }}
                ></div>
              </div>
              <p className="text-xs text-gray-400 mt-1">Audio Level</p>
            </div>
          </div>
        )}

        {isProcessing && (
          <div className="mb-4">
            <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full mx-auto mb-2"></div>
            <p className="text-blue-400">Processing recording...</p>
          </div>
        )}

        <div className="space-y-3">
          {!isRecording && !isProcessing && (
            <button
              onClick={startRecording}
              className="bg-red-500 hover:bg-red-600 text-white px-8 py-3 rounded-lg font-semibold transition-colors flex items-center space-x-2 mx-auto"
            >
              <span>🎤</span>
              <span>Start Recording</span>
            </button>
          )}

          {isRecording && (
            <button
              onClick={stopRecording}
              className="bg-gray-600 hover:bg-gray-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors flex items-center space-x-2 mx-auto"
            >
              <span>⏹️</span>
              <span>Stop Recording</span>
            </button>
          )}
        </div>

        <div className="mt-6 text-sm text-gray-300">
          <p>🎯 <strong>Tips for best results:</strong></p>
          <ul className="mt-2 space-y-1 text-left max-w-md mx-auto">
            <li>• Speak clearly and at normal pace</li>
            <li>• Keep background noise minimal</li>
            <li>• Stay close to your microphone</li>
            <li>• Try different content: speech, rap, singing</li>
          </ul>
        </div>
      </div>
    </div>
  );
};
EOF

echo "✅ Created MicrophoneRecorder.tsx"

# Also fix the API service with session_id
cd ../services/
cp api.ts api.ts.backup.$(date +%s)

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

echo "✅ Fixed API service with session_id parameter"
echo ""
echo "🚀 Now restart your frontend:"
echo "cd ~/verba-frontend-ts/"
echo "npm run dev"
echo ""
echo "🎤 You'll now have microphone recording with:"
echo "• Real-time audio level indicator"
echo "• Recording timer"
echo "• Automatic transcription"
echo "• Toggle between mic and file upload"
