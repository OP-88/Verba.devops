import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Mic, Upload, History, WifiOff, Wifi } from 'lucide-react';
import MicrophoneRecorder from './MicrophoneRecorder';
import AudioUploader from './AudioUploader';
import TranscriptionHistory from './TranscriptionHistory';
import TranscriptionDisplay from './TranscriptionDisplay';
import { apiService } from '@/services/api';
import { TranscriptionResult } from '@/types';

const api = apiService;


export default function App() {
  const [activeTab, setActiveTab] = useState('record');
  const [currentTranscription, setCurrentTranscription] = useState<TranscriptionResult | null>(null);
  const [backendStatus, setBackendStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    // Check backend connection on startup
    checkBackendConnection();
    
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
    try {
      await api.checkHealth();
      setBackendStatus('connected');
    } catch (error) {
      setBackendStatus('error');
    }
  };

  const handleTranscriptionComplete = (result: TranscriptionResult) => {
    setCurrentTranscription(result);
    setActiveTab('result');
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
      
      <div className="relative z-10 container mx-auto px-4 py-6 max-w-6xl">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">
              Verba AI Transcription
            </h1>
            <p className="text-slate-300 text-sm sm:text-base">
              Offline-first audio transcription with speaker diarization
            </p>
          </div>
          
          {/* Status Indicator */}
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="border-white/20 text-white">
              <div className={`w-2 h-2 rounded-full ${getStatusColor()} mr-2`}></div>
              {isOnline ? <Wifi className="w-3 h-3 mr-1" /> : <WifiOff className="w-3 h-3 mr-1" />}
              {getStatusText()}
            </Badge>
          </div>
        </div>

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
            <CardTitle className="text-white text-xl">AI Audio Processing</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-4 bg-white/5 border border-white/10">
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
                <TabsTrigger 
                  value="result" 
                  className="text-white data-[state=active]:bg-white/20 data-[state=active]:text-white"
                  disabled={!currentTranscription}
                >
                  <span className="hidden sm:inline">Result</span>
                  <span className="sm:hidden">📝</span>
                </TabsTrigger>
              </TabsList>

              <TabsContent value="record" className="mt-6">
                <MicrophoneRecorder 
                  onTranscriptionComplete={handleTranscriptionComplete}
                  isOnline={backendStatus === 'connected'}
                />
              </TabsContent>

              <TabsContent value="upload" className="mt-6">
                <AudioUploader 
                  onTranscriptionComplete={handleTranscriptionComplete}
                  isOnline={backendStatus === 'connected'}
                />
              </TabsContent>

              <TabsContent value="history" className="mt-6">
                <TranscriptionHistory onSelectTranscription={setCurrentTranscription} />
              </TabsContent>

              <TabsContent value="result" className="mt-6">
                {currentTranscription && (
                  <TranscriptionDisplay transcription={currentTranscription} />
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-slate-400 text-sm mt-8">
          <p>Verba AI Transcription - Completely offline, privacy-first audio processing</p>
        </div>
      </div>
    </div>
  );
}