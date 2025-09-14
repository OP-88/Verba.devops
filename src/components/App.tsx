import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Mic, Upload, History, WifiOff, Wifi, MessageSquare } from 'lucide-react';
import MicrophoneRecorder from './MicrophoneRecorder';
import AudioUploader from './AudioUploader';
import TranscriptionHistory from './TranscriptionHistory';
import TranscriptionDisplay from './TranscriptionDisplay';
import { apiService, Transcription } from '@/services/api';
import { toast } from 'sonner';


export default function App() {
  const [activeTab, setActiveTab] = useState('record');
  const [currentTranscription, setCurrentTranscription] = useState<Transcription | null>(null);
  const [backendStatus, setBackendStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [mode, setMode] = useState<'offline' | 'hybrid'>('offline');
  const [chatQuery, setChatQuery] = useState('');
  const [chatResponse, setChatResponse] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);

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
      await apiService.checkHealth();
      setBackendStatus('connected');
    } catch (error) {
      setBackendStatus('error');
    }
  };

  const handleTranscriptionComplete = (result: Transcription) => {
    setCurrentTranscription(result);
    setActiveTab('result');
  };

  const handleChat = async () => {
    if (mode === 'offline') {
      toast.error('Chatbot available in hybrid mode only');
      return;
    }
    
    if (!chatQuery.trim()) {
      toast.error('Please enter a question');
      return;
    }

    setIsChatLoading(true);
    try {
      const response = await apiService.chatWithAI(chatQuery);
      setChatResponse(response);
      toast.success('AI response received');
    } catch (error) {
      toast.error('Failed to get AI response');
      setChatResponse('Failed to connect to AI assistant');
    } finally {
      setIsChatLoading(false);
    }
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
                Verba AI Transcription
              </h1>
              <p className="text-slate-300 text-sm sm:text-base">
                Offline-first audio transcription with speaker diarization
              </p>
            </div>
            
            {/* Status and Mode Toggle */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <div className="flex items-center gap-2">
                <span className="text-white text-sm">Hybrid Mode</span>
                <Switch 
                  checked={mode === 'hybrid'} 
                  onCheckedChange={(checked) => setMode(checked ? 'hybrid' : 'offline')} 
                  aria-label="Toggle offline/hybrid mode" 
                />
              </div>
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
                    mode={mode}
                  />
                </TabsContent>

                <TabsContent value="upload" className="mt-6">
                  <AudioUploader 
                    onTranscriptionComplete={handleTranscriptionComplete}
                    isOnline={backendStatus === 'connected'}
                    mode={mode}
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
        </div>

        {/* AI Chatbot Sidebar (Hybrid Mode Only) */}
        {mode === 'hybrid' && (
          <div className="w-full lg:w-80 xl:w-96">
            <Card className="backdrop-blur-md bg-white/10 border-white/20 shadow-2xl h-fit">
              <CardHeader className="pb-4">
                <CardTitle className="text-white text-lg flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  AI Assistant
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  value={chatQuery}
                  onChange={(e) => setChatQuery(e.target.value)}
                  placeholder="Ask about the transcript (e.g., 'Summarize this meeting')"
                  className="bg-white/5 border-white/20 text-white placeholder:text-slate-400 min-h-[100px] resize-none"
                  aria-label="Chat query input"
                />
                <Button 
                  onClick={handleChat} 
                  disabled={isChatLoading || !chatQuery.trim()}
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                  aria-label="Send chat query"
                >
                  {isChatLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      Processing...
                    </>
                  ) : (
                    'Ask AI Assistant'
                  )}
                </Button>
                
                {chatResponse && (
                  <div 
                    className="bg-white/5 border border-white/20 rounded-lg p-4 text-white text-sm"
                    aria-live="polite"
                  >
                    <h4 className="font-semibold mb-2">AI Response:</h4>
                    <p className="whitespace-pre-wrap">{chatResponse}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-slate-400 text-sm mt-8">
          <p>Verba AI Transcription - Completely offline, privacy-first audio processing</p>
        </div>
      </div>
    </div>
  );
}