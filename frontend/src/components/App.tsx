import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useHotkeys } from 'react-hotkeys-hook';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Mic, Upload, History, WifiOff, Wifi, FileText, Clock, Download, User, Play, Pause, Square, Volume2, Users, Brain, Zap, MessageSquare } from 'lucide-react';
import { toast } from 'sonner';
import { saveAs } from 'file-saver';

// Enhanced Types
interface TranscriptionSegment {
  start: number;
  end: number;
  text: string;
  speaker?: string;
  confidence?: number;
}

interface TranscriptionMetadata {
  speakers: number;
  duration: number;
  language: string;
  confidence: number;
  processing_time?: number;
  model_used?: string;
}

interface AIAnalysis {
  summary: string;
  key_points: string[];
  action_items: string[];
  sentiment?: 'positive' | 'negative' | 'neutral';
  topics?: string[];
}

interface Transcription {
  id?: string;
  text: string;
  segments?: TranscriptionSegment[];
  metadata: TranscriptionMetadata;
  ai_analysis?: AIAnalysis;
  timestamp?: string;
  file_name?: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Enhanced API Functions
async function transcribeAudioEnhanced(audioBlob: Blob, options?: {
  vad?: boolean;
  diarization?: boolean;
  summarization?: boolean;
  model?: string;
}): Promise<Transcription> {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  
  const params = new URLSearchParams({
    mode: 'offline',
    vad: String(options?.vad ?? true),
    diarization: String(options?.diarization ?? true),
    summarization: String(options?.summarization ?? true),
    model: options?.model ?? 'base',
    format: 'enhanced'
  });
  
  const response = await fetch(`${API_BASE_URL}/transcribe?${params}`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Transcription failed: ${response.status} - ${error}`);
  }
  
  return response.json();
}

// Legacy function for compatibility
async function transcribeAudio(audioBlob: Blob): Promise<Transcription> {
  return transcribeAudioEnhanced(audioBlob);
}

async function getHistory(): Promise<Transcription[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/transcriptions?session_id=default`);
    if (!response.ok) throw new Error('Failed to fetch history');
    return response.json();
  } catch {
    return [];
  }
}

async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}


export default function App() {
  const [activeTab, setActiveTab] = useState('record');
  const [currentTranscription, setCurrentTranscription] = useState<Transcription | null>(null);
  const [backendStatus, setBackendStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [transcriptions, setTranscriptions] = useState<Transcription[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showAIAnalysis, setShowAIAnalysis] = useState(false);
  const [exportFormat, setExportFormat] = useState<'txt' | 'md' | 'json' | 'srt'>('md');
  const [vadEnabled, setVadEnabled] = useState(true);
  const [diarizationEnabled, setDiarizationEnabled] = useState(true);
  const [summarizationEnabled, setSummarizationEnabled] = useState(true);
  
  // Refs
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const recordingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const animationRef = useRef<number>();

  // Keyboard Shortcuts
  useHotkeys('ctrl+r', (e) => {
    e.preventDefault();
    if (!isRecording) {
      startRecording();
    } else {
      stopRecording();
    }
  }, { enableOnFormTags: true });
  
  useHotkeys('ctrl+p', (e) => {
    e.preventDefault();
    if (isRecording) {
      togglePause();
    }
  }, { enableOnFormTags: true });
  
  useHotkeys('ctrl+s', (e) => {
    e.preventDefault();
    if (currentTranscription) {
      exportTranscription(currentTranscription, exportFormat);
    }
  }, { enableOnFormTags: true });
  
  useHotkeys('ctrl+e', (e) => {
    e.preventDefault();
    setShowAIAnalysis(!showAIAnalysis);
  }, { enableOnFormTags: true });
  
  useHotkeys('tab', (e) => {
    if (e.shiftKey) {
      // Shift+Tab - previous tab
      e.preventDefault();
      const tabs = ['record', 'upload', 'history'];
      const currentIndex = tabs.indexOf(activeTab);
      const prevIndex = (currentIndex - 1 + tabs.length) % tabs.length;
      setActiveTab(tabs[prevIndex]);
    } else {
      // Tab - next tab
      const tabs = ['record', 'upload', 'history'];
      const currentIndex = tabs.indexOf(activeTab);
      const nextIndex = (currentIndex + 1) % tabs.length;
      setActiveTab(tabs[nextIndex]);
    }
  }, { enableOnFormTags: false });

  useEffect(() => {
    // Check backend connection and load history
    checkBackendConnection();
    loadHistory();
    
    // Check every 30 seconds
    const interval = setInterval(checkBackendConnection, 30000);
    
    // Monitor online status
    const handleOnlineStatus = () => setIsOnline(navigator.onLine);
    window.addEventListener('online', handleOnlineStatus);
    window.addEventListener('offline', handleOnlineStatus);
    
    return () => {
      clearInterval(interval);
      window.removeEventListener('online', handleOnlineStatus);
      window.removeEventListener('offline', handleOnlineStatus);
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  const checkBackendConnection = async () => {
    const isHealthy = await checkHealth();
    setBackendStatus(isHealthy ? 'connected' : 'error');
  };

  const loadHistory = async () => {
    const history = await getHistory();
    setTranscriptions(history);
  };

  // Audio level monitoring
  const updateAudioLevel = useCallback(() => {
    if (analyserRef.current) {
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);
      
      const average = dataArray.reduce((sum, value) => sum + value) / dataArray.length;
      setAudioLevel(Math.min(100, (average / 255) * 100));
      
      animationRef.current = requestAnimationFrame(updateAudioLevel);
    }
  }, []);

  // Microphone Recording with enhanced features
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: vadEnabled,
          autoGainControl: true,
          sampleRate: 16000
        }
      });
      
      // Set up audio analysis
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      updateAudioLevel();
      
      const recorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      const chunks: Blob[] = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };
      
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setIsProcessing(true);
        
        try {
          const result = await transcribeAudioEnhanced(blob);
          setCurrentTranscription(result);
          setTranscriptions(prev => [{ ...result, timestamp: new Date().toISOString() }, ...prev]);
          setActiveTab('record');
          toast.success('✨ Transcription complete with AI analysis!');
        } catch (error) {
          console.error('Transcription failed:', error);
          toast.error('❌ Transcription failed. Please try again.');
        } finally {
          setIsProcessing(false);
        }
        
        // Cleanup
        stream.getTracks().forEach(track => track.stop());
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current);
        }
        if (audioContextRef.current) {
          audioContextRef.current.close();
        }
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      setRecordingTime(0);
      
      // Start recording timer
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
      toast.success('🎙️ Recording started (Ctrl+R to stop, Ctrl+P to pause)');
    } catch (error) {
      console.error('Recording failed:', error);
      toast.error('❌ Microphone access denied or not available.');
    }
  };

  const togglePause = () => {
    if (mediaRecorder && isRecording) {
      if (isPaused) {
        mediaRecorder.resume();
        recordingTimerRef.current = setInterval(() => {
          setRecordingTime(prev => prev + 1);
        }, 1000);
        toast.info('▶️ Recording resumed');
      } else {
        mediaRecorder.pause();
        if (recordingTimerRef.current) {
          clearInterval(recordingTimerRef.current);
        }
        toast.info('⏸️ Recording paused');
      }
      setIsPaused(!isPaused);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
      setIsPaused(false);
      setMediaRecorder(null);
      
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
      
      toast.info('🔄 Processing transcription with AI analysis...');
    }
  };

  // Enhanced File Upload
  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    const supportedTypes = [
      'audio/mpeg', 'audio/wav', 'audio/x-m4a', 'audio/mp4', 
      'audio/webm', 'audio/ogg', 'audio/flac', 'audio/aac'
    ];
    
    if (!supportedTypes.includes(file.type) && !file.name.match(/\.(mp3|wav|m4a|mp4|webm|ogg|flac|aac)$/i)) {
      toast.error('❌ Invalid file format. Supported: MP3, WAV, M4A, MP4, WebM, OGG, FLAC, AAC');
      return;
    }

    if (file.size > 100 * 1024 * 1024) { // 100MB limit
      toast.error('❌ File too large. Maximum size: 100MB');
      return;
    }
    
    try {
      setUploadProgress(10);
      setIsProcessing(true);
      toast.info('🚀 Uploading and processing with AI analysis...');
      
      const result = await transcribeAudioEnhanced(file, {
        vad: vadEnabled,
        diarization: diarizationEnabled,
        summarization: summarizationEnabled
      });
      
      // Add file name to the result
      result.file_name = file.name.replace(/\.[^/.]+$/, ""); // Remove extension
      
      setUploadProgress(100);
      setCurrentTranscription(result);
      setTranscriptions(prev => [{ ...result, timestamp: new Date().toISOString() }, ...prev]);
      setActiveTab('record');
      
      toast.success('✨ Transcription complete with AI analysis!');
      setTimeout(() => setUploadProgress(0), 2000);
    } catch (error) {
      console.error('Upload failed:', error);
      toast.error(`❌ Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setUploadProgress(0);
    } finally {
      setIsProcessing(false);
      // Clear the input
      event.target.value = '';
    }
  };

  // Enhanced Export Functions
  const exportTranscription = (transcription: Transcription, format: 'txt' | 'md' | 'json' | 'srt') => {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${transcription.file_name || 'transcription'}-${timestamp}`;
    
    let content: string;
    let mimeType: string;
    let extension: string;
    
    switch (format) {
      case 'md':
        content = generateMarkdown(transcription);
        mimeType = 'text/markdown';
        extension = 'md';
        break;
      case 'json':
        content = JSON.stringify(transcription, null, 2);
        mimeType = 'application/json';
        extension = 'json';
        break;
      case 'srt':
        content = generateSRT(transcription);
        mimeType = 'text/plain';
        extension = 'srt';
        break;
      default:
        content = generatePlainText(transcription);
        mimeType = 'text/plain';
        extension = 'txt';
    }
    
    const blob = new Blob([content], { type: mimeType });
    saveAs(blob, `${filename}.${extension}`);
    toast.success(`📁 Exported as ${format.toUpperCase()}`);
  };
  
  const generateMarkdown = (transcription: Transcription): string => {
    let md = `# Transcription Export\n\n`;
    md += `**Created:** ${transcription.timestamp ? new Date(transcription.timestamp).toLocaleString() : 'Now'}\n`;
    md += `**Duration:** ${transcription.metadata.duration?.toFixed(1) || 'Unknown'} seconds\n`;
    md += `**Language:** ${transcription.metadata.language || 'Auto-detected'}\n`;
    md += `**Speakers:** ${transcription.metadata.speakers}\n`;
    md += `**Confidence:** ${(transcription.metadata.confidence * 100).toFixed(1)}%\n\n`;
    
    if (transcription.ai_analysis?.summary) {
      md += `## Summary\n\n${transcription.ai_analysis.summary}\n\n`;
      
      if (transcription.ai_analysis.key_points?.length) {
        md += `## Key Points\n\n`;
        transcription.ai_analysis.key_points.forEach(point => {
          md += `- ${point}\n`;
        });
        md += '\n';
      }
      
      if (transcription.ai_analysis.action_items?.length) {
        md += `## Action Items\n\n`;
        transcription.ai_analysis.action_items.forEach(item => {
          md += `- [ ] ${item}\n`;
        });
        md += '\n';
      }
    }
    
    md += `## Transcript\n\n`;
    
    if (transcription.segments?.length) {
      transcription.segments.forEach(segment => {
        const timeStr = `[${segment.start.toFixed(1)}s - ${segment.end.toFixed(1)}s]`;
        const speaker = segment.speaker ? `**${segment.speaker}:** ` : '';
        md += `${timeStr} ${speaker}${segment.text}\n\n`;
      });
    } else {
      md += transcription.text;
    }
    
    return md;
  };
  
  const generateSRT = (transcription: Transcription): string => {
    if (!transcription.segments?.length) {
      return `1\n00:00:00,000 --> 00:00:10,000\n${transcription.text}`;
    }
    
    return transcription.segments.map((segment, index) => {
      const start = formatSRTTime(segment.start);
      const end = formatSRTTime(segment.end);
      return `${index + 1}\n${start} --> ${end}\n${segment.text}\n`;
    }).join('\n');
  };
  
  const formatSRTTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 1000);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`;
  };
  
  const generatePlainText = (transcription: Transcription): string => {
    let text = `TRANSCRIPTION EXPORT\n`;
    text += `${'='.repeat(50)}\n\n`;
    text += `Created: ${transcription.timestamp ? new Date(transcription.timestamp).toLocaleString() : 'Now'}\n`;
    text += `Duration: ${transcription.metadata.duration?.toFixed(1) || 'Unknown'} seconds\n`;
    text += `Speakers: ${transcription.metadata.speakers}\n\n`;
    
    if (transcription.ai_analysis?.summary) {
      text += `SUMMARY\n${'='.repeat(20)}\n${transcription.ai_analysis.summary}\n\n`;
    }
    
    text += `TRANSCRIPT\n${'='.repeat(20)}\n\n`;
    
    if (transcription.segments?.length) {
      transcription.segments.forEach(segment => {
        const speaker = segment.speaker ? `${segment.speaker}: ` : '';
        text += `[${segment.start.toFixed(1)}s] ${speaker}${segment.text}\n\n`;
      });
    } else {
      text += transcription.text;
    }
    
    return text;
  };
  
  // Legacy export function
  const exportNote = (text: string, id?: string) => {
    const transcription: Transcription = {
      id,
      text,
      metadata: { speakers: 1, duration: 0, language: 'unknown', confidence: 1 }
    };
    exportTranscription(transcription, 'md');
  };

  const getStatusColor = () => {
    if (!isOnline) return 'bg-orange-500';
    switch (backendStatus) {
      case 'connected': return 'bg-green-500';
      case 'connecting': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    if (!isOnline) return 'Offline Mode';
    switch (backendStatus) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      case 'error': return 'Backend Error';
      default: return 'Unknown';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-20" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%239C92AC' fill-opacity='0.03'%3E%3Ccircle cx='30' cy='30' r='1'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`
      }}></div>
      
      <div className="relative z-10 container mx-auto px-2 sm:px-4 py-4 sm:py-6 max-w-7xl min-h-screen flex flex-col lg:flex-row gap-6">
        {/* Main Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">
                Verba Audio Transcription
              </h1>
              <p className="text-slate-300 text-sm sm:text-base">
                Offline-first audio transcription with speaker diarization
              </p>
            </div>
            
            {/* Status Badge */}
            <Badge variant="outline" className="border-white/20 text-white">
              <div className={`w-2 h-2 rounded-full ${getStatusColor()} mr-2`}></div>
              {isOnline ? <Wifi className="w-3 h-3 mr-1" /> : <WifiOff className="w-3 h-3 mr-1" />}
              {getStatusText()}
            </Badge>
          </div>

        {/* Connection Alert */}
        {backendStatus === 'error' && (
          <Alert className="mb-6 bg-red-500/10 border-red-500/20 text-red-200">
            <AlertDescription>
              Unable to connect to backend server. Please ensure the FastAPI server is running on http://localhost:8000
            </AlertDescription>
          </Alert>
        )}

          {/* Connection Alert */}
          {backendStatus === 'error' && (
            <Alert className="mb-6 bg-red-500/10 border-red-500/20 text-red-200">
              <AlertDescription>
                Unable to connect to backend server. Please ensure the FastAPI server is running on http://localhost:8000
              </AlertDescription>
            </Alert>
          )}

          {/* Main Interface */}
          <Card className="backdrop-blur-md bg-white/10 border-white/20 shadow-2xl">
            <CardHeader className="pb-6">
              <CardTitle className="text-white text-xl">Audio Processing</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-3 bg-white/5 border border-white/10">
                  <TabsTrigger 
                    value="record" 
                    className="text-white data-[state=active]:bg-white/20 data-[state=active]:text-white"
                  >
                    <Mic className="w-4 h-4 mr-2" />
                    <span className="hidden sm:inline">Record</span>
                  </TabsTrigger>
                  <TabsTrigger 
                    value="upload" 
                    className="text-white data-[state=active]:bg-white/20 data-[state=active]:text-white"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    <span className="hidden sm:inline">Upload</span>
                  </TabsTrigger>
                  <TabsTrigger 
                    value="history" 
                    className="text-white data-[state=active]:bg-white/20 data-[state=active]:text-white"
                  >
                    <History className="w-4 h-4 mr-2" />
                    <span className="hidden sm:inline">History</span>
                  </TabsTrigger>
                </TabsList>

                {/* Record Tab */}
                <TabsContent value="record" className="mt-6 space-y-4">
                  <div className="flex gap-2">
                    <Button
                      onClick={startRecording}
                      disabled={isRecording || backendStatus !== 'connected'}
                      className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                      size="lg"
                    >
                      <Mic className="h-5 w-5 mr-2" />
                      Start Recording
                    </Button>
                    <Button
                      onClick={stopRecording}
                      disabled={!isRecording}
                      variant="destructive"
                      className="flex-1"
                      size="lg"
                    >
                      Stop Recording
                    </Button>
                  </div>
                  {isRecording && (
                    <div className="flex items-center justify-center gap-2 text-red-400 animate-pulse">
                      <div className="h-3 w-3 bg-red-500 rounded-full" />
                      Recording in progress...
                    </div>
                  )}
                  <p className="text-sm text-slate-300 text-center">
                    Click Start to begin recording from your microphone
                  </p>
                </TabsContent>

                {/* Upload Tab */}
                <TabsContent value="upload" className="mt-6 space-y-4">
                  <input
                    type="file"
                    accept="audio/mpeg,audio/wav,audio/x-m4a"
                    onChange={handleUpload}
                    disabled={backendStatus !== 'connected'}
                    className="block w-full text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-gradient-to-r file:from-blue-600 file:to-purple-600 file:text-white hover:file:from-blue-700 hover:file:to-purple-700 cursor-pointer disabled:opacity-50"
                  />
                  {uploadProgress > 0 && uploadProgress < 100 && (
                    <div className="space-y-2">
                      <div className="w-full bg-white/10 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-300" 
                          style={{ width: `${uploadProgress}%` }}
                        />
                      </div>
                      <p className="text-sm text-center text-slate-300">{uploadProgress}%</p>
                    </div>
                  )}
                  <p className="text-sm text-slate-300 text-center">
                    Supported formats: MP3, WAV, M4A
                  </p>
                </TabsContent>

                {/* History Tab */}
                <TabsContent value="history" className="mt-6">
                  {transcriptions.length === 0 ? (
                    <p className="text-sm text-slate-300 text-center py-8">
                      No transcriptions yet
                    </p>
                  ) : (
                    <div className="space-y-3 max-h-[500px] overflow-y-auto">
                      {transcriptions.map((t, idx) => (
                        <div 
                          key={t.id || idx} 
                          className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors cursor-pointer"
                          onClick={() => {
                            setCurrentTranscription(t);
                            setActiveTab('record');
                          }}
                        >
                          <p className="text-xs text-slate-400 mb-2">
                            {t.timestamp ? new Date(t.timestamp).toLocaleString() : 'Recent'}
                          </p>
                          <p className="text-sm text-white line-clamp-3 mb-2">{t.text}</p>
                          {t.summary && (
                            <p className="text-xs text-slate-400 italic mb-2 line-clamp-2">
                              {t.summary}
                            </p>
                          )}
                          <div className="flex gap-2">
                            <Button
                              onClick={(e) => {
                                e.stopPropagation();
                                exportNote(t.text, t.id);
                              }}
                              variant="ghost"
                              size="sm"
                              className="flex-1 text-white hover:bg-white/10"
                            >
                              <Download className="h-3 w-3 mr-1" />
                              Export
                            </Button>
                            <Badge variant="outline" className="border-white/20 text-white">
                              <User className="h-3 w-3 mr-1" />
                              {t.metadata.speakers}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>
              </Tabs>

              {/* Current Transcription Display */}
              {currentTranscription && activeTab !== 'history' && (
                <div className="mt-6 space-y-4 border-t border-white/10 pt-6">
                  <div className="flex items-center justify-between">
                    <h3 className="text-white font-semibold flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      Transcription Result
                    </h3>
                    <Button
                      onClick={() => exportNote(currentTranscription.text, currentTranscription.id)}
                      variant="outline"
                      size="sm"
                      className="border-white/20 text-white hover:bg-white/10"
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Export
                    </Button>
                  </div>

                  <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                    <h4 className="text-white font-semibold mb-2">Transcript</h4>
                    <pre className="whitespace-pre-wrap text-sm text-slate-300">
                      {currentTranscription.text}
                    </pre>
                  </div>

                  {currentTranscription.summary && (
                    <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                      <h4 className="text-white font-semibold mb-2">Summary</h4>
                      <p className="text-sm text-slate-300">{currentTranscription.summary}</p>
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t border-white/10">
                    <Badge variant="outline" className="border-white/20 text-white flex items-center gap-1">
                      <User className="h-3 w-3" />
                      {currentTranscription.metadata.speakers} Speaker{currentTranscription.metadata.speakers !== 1 ? 's' : ''}
                    </Badge>
                    {currentTranscription.timestamp && (
                      <Badge variant="outline" className="border-white/20 text-white flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {new Date(currentTranscription.timestamp).toLocaleString()}
                      </Badge>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Footer */}
        <div className="text-center text-slate-400 text-sm mt-8">
          <p>Verba AI Transcription - Completely offline, privacy-first audio processing</p>
        </div>
      </div>
    </div>
  );
}