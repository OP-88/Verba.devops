import React, { useState, useEffect, useRef, useCallback, forwardRef } from 'react';
import { useHotkeys } from 'react-hotkeys-hook';
import { saveAs } from 'file-saver';
import { jsPDF } from 'jspdf';
import { 
  Mic, 
  MicOff, 
  Play, 
  Pause, 
  Upload, 
  FileText, 
  Bookmark, 
  GraduationCap, 
  Coffee, 
  MessageCircle, 
  Send, 
  Bot, 
  User, 
  ArrowLeft, 
  Settings, 
  Trash2,
  Edit3,
  Save,
  X,
  Plus,
  Download,
  Volume2,
  Calendar,
  Clock,
  Wifi,
  WifiOff,
  Brain,
  Sparkles,
  Cloud,
  CloudUpload,
  Check,
  Camera,
  Home,
  Users,
  BarChart3,
  Bell,
  Search,
  Filter,
  MoreHorizontal,
  ChevronDown,
  ChevronRight,
  Lightbulb,
  Target,
  Zap,
  Square,
  Globe,
  Headphones,
  FileAudio,
  Share2,
  Moon,
  Sun,
  Loader2
} from 'lucide-react';
import { cva, type VariantProps } from 'class-variance-authority';
import './App.css';

// ============================================
// TYPES AND INTERFACES
// ============================================

interface TranscriptionSegment {
  start_time: number;
  end_time: number;
  text: string;
  speaker?: string;
  confidence: number;
}

interface TranscriptionResult {
  id: string;
  text: string;
  summary: string;
  segments: TranscriptionSegment[];
  speakers: string[];
  processing_time: number;
  audio_duration: number;
  quality_metrics: {
    speech_ratio: number;
    avg_confidence: number;
    processing_speed: number;
  };
  created_at: string;
  filename: string;
}

interface AppState {
  isRecording: boolean;
  isProcessing: boolean;
  transcriptions: TranscriptionResult[];
  currentTranscription: TranscriptionResult | null;
  isOnline: boolean;
  isDarkMode: boolean;
  settings: {
    includeDiarization: boolean;
    includeSummary: boolean;
    autoSave: boolean;
    keyboardShortcuts: boolean;
  };
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function cn(...inputs: (string | undefined | null | boolean)[]): string {
  return inputs.filter(Boolean).join(' ');
}

// ============================================
// UI COMPONENTS
// ============================================

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-red-500 text-white hover:bg-red-600",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);

const Card = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("rounded-lg border bg-card text-card-foreground shadow-sm", className)}
      {...props}
    />
  )
);

const CardHeader = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("flex flex-col space-y-1.5 p-6", className)}
      {...props}
    />
  )
);

const CardTitle = forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn("text-2xl font-semibold leading-none tracking-tight", className)}
      {...props}
    />
  )
);

const CardDescription = forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  )
);

const CardContent = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
  )
);

const Input = forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);

const Badge = ({ children, variant = "default", className }: { 
  children: React.ReactNode; 
  variant?: "default" | "secondary" | "destructive" | "outline";
  className?: string;
}) => {
  const variants = {
    default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
    secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
    destructive: "border-transparent bg-red-500 text-white hover:bg-red-600",
    outline: "text-foreground border-current",
  };

  return (
    <div className={cn(
      "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
      variants[variant],
      className
    )}>
      {children}
    </div>
  );
};

const Progress = ({ value, className }: { value?: number; className?: string }) => (
  <div className={cn("relative h-2 w-full overflow-hidden rounded-full bg-secondary", className)}>
    <div 
      className="h-full w-full flex-1 bg-primary transition-all"
      style={{ 
        transform: `translateX(-${100 - (value || 0)}%)`,
        animation: value === undefined ? 'pulse 2s ease-in-out infinite alternate' : 'none'
      }}
    />
  </div>
);

const ScrollArea = ({ children, className }: { children: React.ReactNode; className?: string }) => (
  <div className={cn("relative overflow-auto", className)}>
    {children}
  </div>
);

const Separator = ({ className }: { className?: string }) => (
  <div className={cn("shrink-0 bg-border h-[1px] w-full", className)} />
);

// Tabs Components
const Tabs = ({ children, defaultValue, className }: { 
  children: React.ReactNode; 
  defaultValue: string;
  className?: string;
}) => {
  const [activeTab, setActiveTab] = useState(defaultValue);
  
  return (
    <div className={cn("w-full", className)} data-active-tab={activeTab}>
      {React.Children.map(children, child => 
        React.isValidElement(child) 
          ? React.cloneElement(child as React.ReactElement<any>, { activeTab, setActiveTab })
          : child
      )}
    </div>
  );
};

const TabsList = ({ children, className, activeTab, setActiveTab }: { 
  children: React.ReactNode; 
  className?: string;
  activeTab?: string;
  setActiveTab?: (tab: string) => void;
}) => (
  <div className={cn("inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground", className)}>
    {React.Children.map(children, child => 
      React.isValidElement(child) 
        ? React.cloneElement(child as React.ReactElement<any>, { activeTab, setActiveTab })
        : child
    )}
  </div>
);

const TabsTrigger = ({ children, value, className, activeTab, setActiveTab }: { 
  children: React.ReactNode; 
  value: string;
  className?: string;
  activeTab?: string;
  setActiveTab?: (tab: string) => void;
}) => (
  <button
    className={cn(
      "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
      activeTab === value ? "bg-background text-foreground shadow-sm" : "",
      className
    )}
    onClick={() => setActiveTab?.(value)}
  >
    {children}
  </button>
);

const TabsContent = ({ children, value, className, activeTab }: { 
  children: React.ReactNode; 
  value: string;
  className?: string;
  activeTab?: string;
}) => {
  if (activeTab !== value) return null;
  
  return (
    <div className={cn("mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2", className)}>
      {children}
    </div>
  );
};

// ============================================
// WEBSOCKET CONNECTION MANAGER
// ============================================

class TranscriptionWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private onMessage: (data: any) => void;
  private onError: (error: any) => void;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor(url: string, onMessage: (data: any) => void, onError: (error: any) => void) {
    this.url = url;
    this.onMessage = onMessage;
    this.onError = onError;
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        console.log('✅ WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.onMessage(data);
        } catch (e) {
          console.error('❌ Failed to parse WebSocket message:', e);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.onError(error);
      };

      this.ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        this.handleReconnect();
      };
    } catch (error) {
      console.error('❌ Failed to create WebSocket:', error);
      this.onError(error);
    }
  }

  private handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      console.log(`🔄 Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);
      
      setTimeout(() => {
        this.connect();
      }, delay);
    }
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('⚠️ WebSocket not connected, cannot send message');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// ============================================
// CUSTOM HOOKS
// ============================================

const useToast = () => {
  const [toasts, setToasts] = useState<Array<{ id: string; title?: string; description?: string; variant?: string }>>([]);

  const toast = ({ title, description, variant = "default" }: { title?: string; description?: string; variant?: string }) => {
    const id = Math.random().toString(36).substring(7);
    setToasts(prev => [...prev, { id, title, description, variant }]);
    
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 5000);
  };

  return { toast, toasts };
};

// ============================================
// MAIN COMPONENTS
// ============================================

// Enhanced Splash Screen
const SplashScreen = ({ onFinish }: { onFinish: () => void }) => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(onFinish, 500);
          return 100;
        }
        return prev + 2;
      });
    }, 60);

    return () => clearInterval(interval);
  }, [onFinish]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800 flex items-center justify-center">
      <div className="text-center space-y-8 max-w-md mx-auto px-4">
        <div className="bounce-logo">
          <div className="relative">
            <Headphones className="h-20 w-20 text-white mx-auto" />
            <div className="absolute -top-2 -right-2">
              <Brain className="h-8 w-8 text-yellow-300" />
            </div>
          </div>
        </div>
        <div className="space-y-4">
          <h1 className="text-4xl font-bold text-white">Verba AI</h1>
          <p className="text-xl text-white/80">AI-powered transcription & learning</p>
          <div className="space-y-2">
            <Progress value={progress} className="h-1" />
            <p className="text-sm text-white/60">{progress}% loaded</p>
          </div>
        </div>
        <div className="text-sm text-white/40">
          Initializing AI services...
        </div>
      </div>
    </div>
  );
};

// Enhanced Dashboard Card
const DashboardCard = ({ 
  icon: Icon, 
  title, 
  description, 
  onClick, 
  disabled = false,
  badge,
  accent = false
}: { 
  icon: any; 
  title: string; 
  description: string; 
  onClick: () => void; 
  disabled?: boolean;
  badge?: string;
  accent?: boolean;
}) => (
  <Card 
    className={cn(
      "cursor-pointer transition-all duration-200 hover:scale-105 hover:shadow-lg group",
      disabled && "opacity-50 cursor-not-allowed",
      accent && "border-primary/50 bg-primary/5"
    )}
    onClick={disabled ? undefined : onClick}
  >
    <CardHeader className="text-center space-y-4">
      <div className="mx-auto p-4 bg-gradient-to-br from-primary/10 to-primary/5 rounded-full w-fit relative group-hover:from-primary/20 group-hover:to-primary/10 transition-all">
        <Icon className={cn("h-8 w-8", accent ? "text-primary" : "text-primary")} />
        {badge && (
          <Badge className="absolute -top-2 -right-2 px-2 py-1 text-xs" variant="destructive">
            {badge}
          </Badge>
        )}
      </div>
      <div>
        <CardTitle className="text-lg">{title}</CardTitle>
        <CardDescription className="mt-2">{description}</CardDescription>
      </div>
    </CardHeader>
  </Card>
);

// Enhanced Transcription Component
const TranscriptionDisplay = ({ 
  transcription, 
  onExportMarkdown, 
  onExportPDF 
}: {
  transcription: TranscriptionResult;
  onExportMarkdown: () => void;
  onExportPDF: () => void;
}) => {
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatConfidence = (confidence: number): string => {
    return `${Math.round(confidence * 100)}%`;
  };

  return (
    <div className="space-y-6">
      {/* Header with Export Options */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Transcription Results</h2>
          <p className="text-muted-foreground">
            Processed in {transcription.processing_time.toFixed(2)}s • 
            {transcription.quality_metrics.processing_speed.toFixed(1)}x real-time
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onExportMarkdown}>
            <FileText className="h-4 w-4" />
            Markdown
          </Button>
          <Button variant="outline" size="sm" onClick={onExportPDF}>
            <Download className="h-4 w-4" />
            PDF
          </Button>
        </div>
      </div>

      <Tabs defaultValue="transcript" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="transcript">Transcript</TabsTrigger>
          <TabsTrigger value="summary">Summary</TabsTrigger>
          <TabsTrigger value="speakers">Speakers</TabsTrigger>
          <TabsTrigger value="details">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="transcript">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileAudio className="h-5 w-5" />
                Full Transcript
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96 w-full rounded border p-4">
                <div 
                  className="whitespace-pre-wrap text-sm leading-relaxed"
                  role="document"
                  aria-label="Transcription text"
                >
                  {transcription.text}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="summary">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                AI Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg">
                {transcription.summary || 'No summary generated'}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="speakers">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Speaker Analysis ({transcription.speakers.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96 w-full">
                <div className="space-y-4">
                  {transcription.segments.map((segment, index) => (
                    <div key={index} className="p-3 border rounded-lg hover:bg-muted/50 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant="outline">
                          {segment.speaker || 'Unknown Speaker'}
                        </Badge>
                        <div className="text-xs text-muted-foreground">
                          {formatTime(segment.start_time)} - {formatTime(segment.end_time)}
                          {' '}•{' '}
                          {formatConfidence(segment.confidence)} confidence
                        </div>
                      </div>
                      <div className="text-sm">{segment.text}</div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="details">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Quality Metrics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span>Speech Ratio</span>
                  <span className="font-medium">{Math.round(transcription.quality_metrics.speech_ratio * 100)}%</span>
                </div>
                <Progress value={transcription.quality_metrics.speech_ratio * 100} />
                
                <div className="flex justify-between">
                  <span>Avg Confidence</span>
                  <span className="font-medium">{formatConfidence(transcription.quality_metrics.avg_confidence)}</span>
                </div>
                <Progress value={transcription.quality_metrics.avg_confidence * 100} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Processing Info
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="font-medium">File</div>
                  <div className="text-muted-foreground">{transcription.filename}</div>
                </div>
                <div>
                  <div className="font-medium">Duration</div>
                  <div className="text-muted-foreground">{formatTime(transcription.audio_duration)}</div>
                </div>
                <div>
                  <div className="font-medium">Processing Time</div>
                  <div className="text-muted-foreground">{transcription.processing_time.toFixed(2)}s</div>
                </div>
                <div>
                  <div className="font-medium">Speed</div>
                  <div className="text-muted-foreground">{transcription.quality_metrics.processing_speed.toFixed(1)}x</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Enhanced Live Transcription
const LiveTranscription = ({ onBack, isOnline }: { onBack: () => void; isOnline: boolean }) => {
  const [state, setState] = useState<AppState>({
    isRecording: false,
    isProcessing: false,
    transcriptions: [],
    currentTranscription: null,
    isOnline: navigator.onLine,
    isDarkMode: localStorage.getItem('darkMode') === 'true',
    settings: {
      includeDiarization: true,
      includeSummary: true,
      autoSave: true,
      keyboardShortcuts: true
    }
  });

  const [duration, setDuration] = useState(0);
  const [liveTranscript, setLiveTranscript] = useState('');
  
  const wsRef = useRef<TranscriptionWebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const { toast } = useToast();

  // Initialize WebSocket
  useEffect(() => {
    const wsUrl = `ws://localhost:8000/ws/transcribe?client_id=${Date.now()}`;
    
    wsRef.current = new TranscriptionWebSocket(
      wsUrl,
      handleWebSocketMessage,
      (error) => console.error('WebSocket error:', error)
    );

    wsRef.current.connect();

    return () => {
      wsRef.current?.disconnect();
    };
  }, []);

  const handleWebSocketMessage = useCallback((data: any) => {
    console.log('📨 WebSocket message:', data);

    switch (data.type) {
      case 'connection_established':
        console.log('✅ Connected to transcription service');
        break;
      
      case 'live_transcription':
        setLiveTranscript(prev => prev + ' ' + data.text);
        break;
      
      case 'transcription_chunk':
        if (data.text?.trim()) {
          const result: TranscriptionResult = {
            id: data.chunk_id || Date.now().toString(),
            text: data.text,
            summary: data.summary || '',
            segments: data.segments || [],
            speakers: data.speakers || [],
            processing_time: data.processing_time || 0,
            audio_duration: data.audio_duration || 0,
            quality_metrics: data.quality_metrics || {
              speech_ratio: 0,
              avg_confidence: 0,
              processing_speed: 0
            },
            created_at: new Date().toISOString(),
            filename: 'live_recording.wav'
          };

          setState(prev => ({
            ...prev,
            currentTranscription: result,
            isProcessing: false
          }));
        }
        break;

      case 'error':
        console.error('❌ Transcription error:', data.error);
        setState(prev => ({ ...prev, isProcessing: false }));
        toast({ title: "Transcription error", description: data.error, variant: "destructive" });
        break;
    }
  }, [toast]);

  // Timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (state.isRecording) {
      interval = setInterval(() => {
        setDuration(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [state.isRecording]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        } 
      });

      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4'
      });
      
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { 
          type: mediaRecorderRef.current?.mimeType || 'audio/wav' 
        });
        processAudioBlob(audioBlob, 'live_recording.wav');
      };

      mediaRecorderRef.current.start(1000); // Collect data every second
      setState(prev => ({ ...prev, isRecording: true }));
      setLiveTranscript('');
      
    } catch (error) {
      console.error('❌ Failed to start recording:', error);
      toast({ title: "Microphone Error", description: "Failed to access microphone. Please check permissions.", variant: "destructive" });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && state.isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setState(prev => ({ ...prev, isRecording: false, isProcessing: true }));
    }
  };

  const processAudioBlob = async (blob: Blob, filename: string) => {
    try {
      const base64Data = await blobToBase64(blob);
      
      wsRef.current?.send({
        type: 'audio_file',
        data: base64Data,
        filename: filename,
        include_diarization: state.settings.includeDiarization,
        include_summary: state.settings.includeSummary,
        file_id: Date.now().toString()
      });

    } catch (error) {
      console.error('❌ Failed to process audio:', error);
      setState(prev => ({ ...prev, isProcessing: false }));
    }
  };

  const blobToBase64 = (blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        resolve(result.split(',')[1]);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  };

  const exportAsMarkdown = () => {
    if (!state.currentTranscription) return;
    const markdown = generateMarkdown(state.currentTranscription);
    const blob = new Blob([markdown], { type: 'text/markdown' });
    saveAs(blob, `transcription_${Date.now()}.md`);
  };

  const exportAsPDF = () => {
    if (!state.currentTranscription) return;
    const pdf = new jsPDF();
    pdf.text('Transcription', 20, 20);
    pdf.text(state.currentTranscription.text, 20, 40);
    pdf.save(`transcription_${Date.now()}.pdf`);
  };

  const generateMarkdown = (transcription: TranscriptionResult): string => {
    let markdown = `# Audio Transcription\n\n`;
    markdown += `**File:** ${transcription.filename}\n`;
    markdown += `**Duration:** ${formatTime(transcription.audio_duration)}\n\n`;
    markdown += `## Transcript\n\n${transcription.text}\n\n`;
    return markdown;
  };

  return (
    <div className="min-h-screen bg-background p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Button variant="ghost" size="icon" onClick={onBack}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-r from-red-500 to-pink-500 rounded-full">
              <Mic className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold">Live Transcription</h1>
              <p className="text-muted-foreground">Real-time AI-powered transcription</p>
            </div>
          </div>
        </div>

        {!isOnline && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center gap-2 text-yellow-800">
              <WifiOff className="h-4 w-4" />
              <span className="text-sm">You're offline. Recording will be processed when connection is restored.</span>
            </div>
          </div>
        )}

        {/* Main Interface */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Panel - Controls */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Recording Controls</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Timer Display */}
                <div className="text-center">
                  <div className="text-4xl font-mono font-bold mb-2">
                    {formatTime(duration)}
                  </div>
                  <div className="flex items-center justify-center gap-2">
                    {state.isRecording && (
                      <>
                        <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                        <span className="text-sm text-muted-foreground">Recording</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Recording Button */}
                <Button
                  onClick={state.isRecording ? stopRecording : startRecording}
                  disabled={state.isProcessing}
                  className={cn(
                    "w-full h-16 text-lg font-semibold rounded-full",
                    state.isRecording 
                      ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse' 
                      : 'bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white'
                  )}
                  aria-label={state.isRecording ? "Stop recording" : "Start recording"}
                >
                  {state.isRecording ? (
                    <><Square className="w-6 h-6 mr-2" /> Stop Recording</>
                  ) : (
                    <><Mic className="w-6 h-6 mr-2" /> Start Recording</>
                  )}
                </Button>

                {/* Processing Status */}
                {state.isProcessing && (
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Processing audio...</span>
                    </div>
                    <Progress value={undefined} className="w-full" />
                  </div>
                )}

                {/* Settings */}
                <Separator />
                <div className="space-y-4">
                  <h3 className="text-sm font-semibold">AI Features</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <label htmlFor="diarization" className="text-sm">Speaker Diarization</label>
                      <input
                        id="diarization"
                        type="checkbox"
                        checked={state.settings.includeDiarization}
                        onChange={(e) => setState(prev => ({
                          ...prev,
                          settings: { ...prev.settings, includeDiarization: e.target.checked }
                        }))}
                        className="rounded"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <label htmlFor="summary" className="text-sm">AI Summary</label>
                      <input
                        id="summary"
                        type="checkbox"
                        checked={state.settings.includeSummary}
                        onChange={(e) => setState(prev => ({
                          ...prev,
                          settings: { ...prev.settings, includeSummary: e.target.checked }
                        }))}
                        className="rounded"
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Panel - Results */}
          <div className="lg:col-span-2">
            {state.currentTranscription ? (
              <TranscriptionDisplay
                transcription={state.currentTranscription}
                onExportMarkdown={exportAsMarkdown}
                onExportPDF={exportAsPDF}
              />
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center h-96 text-center">
                  <div className="mb-6">
                    <div className="relative">
                      <div className="w-24 h-24 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full flex items-center justify-center mb-4">
                        <Headphones className="w-12 h-12 text-muted-foreground" />
                      </div>
                      {state.isRecording && (
                        <div className="absolute inset-0 w-24 h-24 border-2 border-red-500 rounded-full animate-ping" />
                      )}
                    </div>
                  </div>
                  <h2 className="text-xl font-semibold mb-2">Ready for Transcription</h2>
                  <p className="text-muted-foreground mb-4">
                    {state.isRecording 
                      ? "Recording in progress... Speak clearly for best results."
                      : "Click the microphone to start recording your audio."
                    }
                  </p>
                  {/* Live transcript preview */}
                  {liveTranscript && (
                    <div className="mt-4 p-4 bg-muted rounded-lg max-w-md">
                      <p className="text-sm text-muted-foreground mb-2">Live Transcript:</p>
                      <p className="text-sm">{liveTranscript}</p>
                    </div>
                  )}
                  <div className="text-xs text-muted-foreground mt-4">
                    <p>Features: Real-time transcription • Speaker identification • AI summarization</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Enhanced Dashboard
const Dashboard = ({ onNavigate, isOnline }: { onNavigate: (page: string) => void; isOnline: boolean }) => {
  const [isDarkMode, setIsDarkMode] = useState(localStorage.getItem('darkMode') === 'true');
  const [name] = useState(() => localStorage.getItem('userProfile_name') || '');
  const [avatar] = useState(() => localStorage.getItem('userProfile_avatar') || '');

  const toggleTheme = () => {
    const newDarkMode = !isDarkMode;
    setIsDarkMode(newDarkMode);
    localStorage.setItem('darkMode', newDarkMode.toString());
    
    if (newDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    }
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Enhanced Header */}
      <header className="border-b bg-card/50 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg">
                <Headphones className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Verba AI
                </h1>
                <p className="text-xs text-muted-foreground">AI-Powered Transcription</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Online Status */}
              <div className="flex items-center gap-2">
                <Badge variant={isOnline ? "default" : "destructive"} className="text-xs">
                  {isOnline ? (
                    <><Globe className="w-3 h-3 mr-1" /> Online</>
                  ) : (
                    <><WifiOff className="w-3 h-3 mr-1" /> Offline</>
                  )}
                </Badge>
              </div>

              {/* Theme Toggle */}
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
                aria-label={isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
              >
                {isDarkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </Button>

              {/* Profile */}
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center overflow-hidden">
                  {avatar ? (
                    <img src={avatar} alt="Avatar" className="w-full h-full object-cover" />
                  ) : (
                    <User className="h-4 w-4 text-white" />
                  )}
                </div>
                <span className="text-sm font-medium">{name || 'Welcome'}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">Welcome back!</h2>
          <p className="text-muted-foreground">Choose how you'd like to transcribe your audio today.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <DashboardCard
            icon={Mic}
            title="Live Transcription"
            description="Record and transcribe meetings in real-time with AI"
            onClick={() => onNavigate('live-transcription')}
            disabled={!isOnline}
            badge={!isOnline ? "Offline" : undefined}
            accent={true}
          />
          
          <DashboardCard
            icon={Upload}
            title="Import Audio Files"
            description="Upload audio files for batch transcription processing"
            onClick={() => onNavigate('import-audio')}
          />
          
          <DashboardCard
            icon={FileText}
            title="Transcript Library"
            description="View, edit, and manage your transcription history"
            onClick={() => onNavigate('transcripts')}
          />
          
          <DashboardCard
            icon={Brain}
            title="AI Study Assistant"
            description="Chat with AI about your transcribed content"
            onClick={() => onNavigate('ai-chat')}
          />
          
          <DashboardCard
            icon={Bookmark}
            title="Notes & Reminders"
            description="Keep track of important insights and follow-ups"
            onClick={() => onNavigate('notes')}
          />
          
          <DashboardCard
            icon={Settings}
            title="Settings"
            description="Customize AI features and application preferences"
            onClick={() => onNavigate('settings')}
          />
        </div>

        {/* Quick Stats */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-2xl font-bold text-blue-600">42</div>
              <div className="text-sm text-muted-foreground">Hours Transcribed</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-2xl font-bold text-green-600">98%</div>
              <div className="text-sm text-muted-foreground">Average Accuracy</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6 text-center">
              <div className="text-2xl font-bold text-purple-600">156</div>
              <div className="text-sm text-muted-foreground">Files Processed</div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

// Main App Component
export default function App(): JSX.Element {
  const [showSplash, setShowSplash] = useState(true);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnlineStatus = () => setIsOnline(navigator.onLine);

    window.addEventListener('online', handleOnlineStatus);
    window.addEventListener('offline', handleOnlineStatus);

    return () => {
      window.removeEventListener('online', handleOnlineStatus);
      window.removeEventListener('offline', handleOnlineStatus);
    };
  }, []);

  const handleSplashFinish = () => {
    setShowSplash(false);
  };

  const handleNavigate = (page: string) => {
    setCurrentPage(page);
  };

  const handleBack = () => {
    setCurrentPage('dashboard');
  };

  if (showSplash) {
    return <SplashScreen onFinish={handleSplashFinish} />;
  }

  switch (currentPage) {
    case 'live-transcription':
      return <LiveTranscription onBack={handleBack} isOnline={isOnline} />;
    // Add other pages here...
    default:
      return <Dashboard onNavigate={handleNavigate} isOnline={isOnline} />;
  }
}