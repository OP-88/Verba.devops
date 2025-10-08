import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Mic, Upload, History, WifiOff, Wifi, FileText, Clock, Download, User, Play } from 'lucide-react';
import { toast } from 'sonner';
import { saveAs } from 'file-saver';

// Types
interface Transcription {
  id?: number;
  text: string;
  summary: string;
  metadata: { speakers: number };
  timestamp?: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// API Functions
async function transcribeAudio(audioBlob: Blob): Promise<Transcription> {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.wav');
  const response = await fetch(`${API_BASE_URL}/transcribe?mode=offline`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) throw new Error(`Transcription failed: ${response.status}`);
  return response.json();
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
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

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

  // Microphone Recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/wav' });
        try {
          const result = await transcribeAudio(blob);
          setCurrentTranscription(result);
          setTranscriptions(prev => [{ ...result, timestamp: new Date().toISOString() }, ...prev]);
          setActiveTab('result');
          toast.success('Transcription complete');
        } catch (error) {
          toast.error('Transcription failed');
        }
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
      toast.success('Recording started');
    } catch (error) {
      toast.error('Microphone access denied');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
      setMediaRecorder(null);
      toast.info('Processing transcription...');
    }
  };

  // File Upload
  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !['audio/mpeg', 'audio/wav', 'audio/x-m4a'].includes(file.type)) {
      toast.error('Invalid file format (MP3/WAV/M4A only)');
      return;
    }

    const formData = new FormData();
    formData.append('audio', file);
    
    try {
      setUploadProgress(50);
      toast.info('Uploading and processing...');
      const response = await fetch(`${API_BASE_URL}/transcribe?mode=offline`, {
        method: 'POST',
        body: formData,
      });
      setUploadProgress(100);
      
      if (!response.ok) throw new Error('Upload failed');
      const result = await response.json();
      setCurrentTranscription(result);
      setTranscriptions(prev => [{ ...result, timestamp: new Date().toISOString() }, ...prev]);
      setActiveTab('result');
      toast.success('Transcription complete');
      setTimeout(() => setUploadProgress(0), 1000);
    } catch (error) {
      toast.error('Upload failed');
      setUploadProgress(0);
    }
  };

  // Export
  const exportNote = (text: string, id?: number) => {
    saveAs(new Blob([text], { type: 'text/plain' }), `transcript-${id || 'current'}.md`);
    toast.success('Transcript exported');
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