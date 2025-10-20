// src/components/VerbaComplete.tsx
import React, { useState, useRef, useEffect } from 'react';
import VerbaAPI from '../lib/verba-api';

interface Transcription {
  id: number;
  title: string;
  transcription_text: string;
  duration_seconds: number;
  confidence_score: number;
  created_at: string;
  ai_analysis?: string;
  suggested_questions?: string[];
}

export function VerbaComplete() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcriptions, setTranscriptions] = useState<Transcription[]>([]);
  const [currentTranscription, setCurrentTranscription] = useState<string>('');
  const [aiResponse, setAiResponse] = useState<string>('');
  const [chatMessage, setChatMessage] = useState('');
  const [sessionId, setSessionId] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    initializeSession();
  }, []);

  const initializeSession = async () => {
    try {
      const id = await VerbaAPI.createSession();
      setSessionId(id);
      
      // Load existing transcriptions
      const history = await VerbaAPI.getTranscriptions();
      setTranscriptions(history.transcriptions || []);
    } catch (error) {
      console.error('Session initialization failed:', error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    setCurrentTranscription('');
    setAiResponse('');

    try {
      const result = await VerbaAPI.transcribeAudio(file, `Audio - ${new Date().toLocaleString()}`);
      
      // Display results
      setCurrentTranscription(result.transcription.text);
      if (result.ai_analysis) {
        setAiResponse(result.ai_analysis);
      }

      // Refresh transcription list
      const history = await VerbaAPI.getTranscriptions();
      setTranscriptions(history.transcriptions || []);

      // Show success
      alert('Transcription completed successfully!');

    } catch (error) {
      console.error('Transcription failed:', error);
      alert(`Transcription failed: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleChat = async () => {
    if (!chatMessage.trim()) return;

    try {
      const response = await VerbaAPI.chatWithAI(chatMessage);
      setAiResponse(response);
      setChatMessage('');
    } catch (error) {
      console.error('Chat failed:', error);
      alert(`Chat failed: ${error.message}`);
    }
  };

  const loadTranscription = async (transcription: Transcription) => {
    setCurrentTranscription(transcription.transcription_text);
    setAiResponse('');
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto', fontFamily: 'Arial, sans-serif' }}>
      <h1>🎯 Verba Complete System</h1>
      
      {/* Session Info */}
      <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '5px' }}>
        <p><strong>Session ID:</strong> {sessionId ? `${sessionId.substring(0, 8)}...` : 'Loading...'}</p>
        <p><strong>Status:</strong> {isProcessing ? '🔄 Processing...' : '✅ Ready'}</p>
      </div>

      {/* File Upload */}
      <div style={{ marginBottom: '20px', padding: '15px', border: '2px dashed #ccc', borderRadius: '5px' }}>
        <h3>📤 Upload Audio File</h3>
        <input
          ref={fileInputRef}
          type="file"
          accept=".wav,.mp3,.flac,.m4a"
          onChange={handleFileUpload}
          disabled={isProcessing}
          style={{ marginBottom: '10px' }}
        />
        <p>Supported formats: WAV, MP3, FLAC, M4A</p>
        {isProcessing && <p>🔄 Processing audio with Whisper + VAD...</p>}
      </div>

      {/* Current Transcription */}
      {currentTranscription && (
        <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f9f9f9', borderRadius: '5px' }}>
          <h3>📝 Current Transcription</h3>
          <div style={{ 
            maxHeight: '200px', 
            overflow: 'auto', 
            padding: '10px', 
            backgroundColor: 'white', 
            border: '1px solid #ddd',
            borderRadius: '3px'
          }}>
            {currentTranscription}
          </div>
        </div>
      )}

      {/* AI Chat */}
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#e8f4f8', borderRadius: '5px' }}>
        <h3>🤖 Chat with AI (Claude 3.5 Sonnet)</h3>
        <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
          <input
            type="text"
            value={chatMessage}
            onChange={(e) => setChatMessage(e.target.value)}
            placeholder="Ask about the transcription or anything else..."
            onKeyPress={(e) => e.key === 'Enter' && handleChat()}
            style={{ flex: 1, padding: '8px', borderRadius: '3px', border: '1px solid #ccc' }}
          />
          <button 
            onClick={handleChat}
            disabled={!chatMessage.trim()}
            style={{ padding: '8px 15px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '3px' }}
          >
            Send
          </button>
        </div>

        {/* AI Response */}
        {aiResponse && (
          <div style={{ 
            padding: '10px', 
            backgroundColor: 'white', 
            border: '1px solid #ddd',
            borderRadius: '3px',
            marginTop: '10px',
            maxHeight: '300px',
            overflow: 'auto'
          }}>
            <strong>🤖 AI Response:</strong>
            <div style={{ marginTop: '5px', lineHeight: '1.5' }}>
              {aiResponse.split('\n').map((line, index) => (
                <p key={index}>{line}</p>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Transcription History */}
      <div style={{ padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '5px' }}>
        <h3>📚 Transcription History</h3>
        {transcriptions.length === 0 ? (
          <p>No transcriptions yet. Upload an audio file to get started!</p>
        ) : (
          <div style={{ maxHeight: '300px', overflow: 'auto' }}>
            {transcriptions.map((transcription, index) => (
              <div 
                key={transcription.id}
                style={{ 
                  padding: '10px', 
                  backgroundColor: 'white', 
                  marginBottom: '10px',
                  borderRadius: '3px',
                  border: '1px solid #ddd',
                  cursor: 'pointer'
                }}
                onClick={() => loadTranscription(transcription)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong>{transcription.title}</strong>
                    <p style={{ margin: '5px 0', color: '#666', fontSize: '0.9em' }}>
                      Duration: {transcription.duration_seconds?.toFixed(1)}s | 
                      Confidence: {(transcription.confidence_score * 100)?.toFixed(1)}% |
                      Created: {new Date(transcription.created_at).toLocaleString()}
                    </p>
                  </div>
                  <button 
                    onClick={(e) => { e.stopPropagation(); loadTranscription(transcription); }}
                    style={{ padding: '5px 10px', fontSize: '0.8em' }}
                  >
                    Load
                  </button>
                </div>
                <p style={{ 
                  margin: '5px 0', 
                  fontSize: '0.9em', 
                  maxHeight: '40px', 
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}>
                  {transcription.transcription_text.substring(0, 100)}...
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
