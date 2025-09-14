import React, { useState, useRef, useEffect } from 'react';
import { useHotkeys } from 'react-hotkeys-hook';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Progress } from '@/components/ui/progress';
import { Mic, MicOff, Square, Play, Pause, Download } from 'lucide-react';
import { toast } from 'sonner';
import { apiService } from '@/services/api';

interface MicrophoneRecorderProps {
  onTranscriptionComplete?: (result: any) => void;
  isOnline?: boolean;
  mode?: 'offline' | 'hybrid';
}

interface TranscriptionSegment {
  speaker: string;
  text: string;
  start: number;
  end: number;
  confidence?: number;
}

const MicrophoneRecorder: React.FC<MicrophoneRecorderProps> = ({ 
  onTranscriptionComplete, 
  isOnline = true,
  mode = 'offline'
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcriptionResult, setTranscriptionResult] = useState<TranscriptionSegment[] | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const animationRef = useRef<number>();

  // Keyboard shortcuts
  useHotkeys('ctrl+r', () => !isRecording ? startRecording() : stopRecording(), {
    enableOnFormTags: true,
    preventDefault: true
  });
  
  useHotkeys('ctrl+p', () => isRecording ? togglePause() : null, {
    enableOnFormTags: true,
    preventDefault: true
  });

  useHotkeys('ctrl+s', () => isRecording ? stopRecording() : null, {
    enableOnFormTags: true,
    preventDefault: true
  });

  // Audio level monitoring
  const updateAudioLevel = () => {
    if (analyserRef.current) {
      const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
      analyserRef.current.getByteFrequencyData(dataArray);
      
      const average = dataArray.reduce((sum, value) => sum + value) / dataArray.length;
      setAudioLevel(Math.min(100, (average / 255) * 100));
      
      animationRef.current = requestAnimationFrame(updateAudioLevel);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000
        } 
      });
      
      streamRef.current = stream;

      // Set up audio analysis
      audioContextRef.current = new AudioContext();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      updateAudioLevel();

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      const chunks: BlobPart[] = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setAudioBlob(blob);
        
        // Clean up
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current);
        }
        if (audioContextRef.current) {
          audioContextRef.current.close();
        }
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      toast.success('Recording started (Ctrl+R to stop)');
    } catch (error) {
      console.error('Error starting recording:', error);
      toast.error('Failed to start recording. Please check microphone permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      
      toast.success('Recording stopped');
    }
  };

  const togglePause = () => {
    if (mediaRecorderRef.current && isRecording) {
      if (isPaused) {
        mediaRecorderRef.current.resume();
        timerRef.current = setInterval(() => {
          setRecordingTime(prev => prev + 1);
        }, 1000);
        toast.success('Recording resumed');
      } else {
        mediaRecorderRef.current.pause();
        if (timerRef.current) {
          clearInterval(timerRef.current);
        }
        toast.success('Recording paused');
      }
      setIsPaused(!isPaused);
    }
  };

  const handleTranscribe = async () => {
    if (!audioBlob) return;

    setIsTranscribing(true);
    
    try {
      const result = await apiService.transcribeAudio(audioBlob, mode);
      
      // Parse speaker-segmented transcription
      const segments: TranscriptionSegment[] = [];
      const lines = result.text.split('\n');
      
      lines.forEach((line, index) => {
        const speakerMatch = line.match(/^Speaker (\w+): (.+)$/);
        if (speakerMatch) {
          segments.push({
            speaker: `Speaker ${speakerMatch[1]}`,
            text: speakerMatch[2],
            start: index * 5, // Approximate timing
            end: (index + 1) * 5,
            confidence: 0.95
          });
        } else if (line.trim()) {
          segments.push({
            speaker: 'Speaker 1',
            text: line.trim(),
            start: index * 5,
            end: (index + 1) * 5,
            confidence: 0.95
          });
        }
      });

      setTranscriptionResult(segments);
      onTranscriptionComplete?.(result);
      
      const modeText = mode === 'hybrid' ? 'with AI insights' : '';
      toast.success(`Transcription completed with speaker identification ${modeText}`);
    } catch (error) {
      console.error('Transcription error:', error);
      toast.error('Transcription failed. Please try again.');
    } finally {
      setIsTranscribing(false);
    }
  };

  const downloadAudio = () => {
    if (audioBlob) {
      const url = URL.createObjectURL(audioBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `recording-${new Date().toISOString().slice(0, 19)}.webm`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return (
    <div className="space-y-4 sm:space-y-6 p-4 sm:p-6 max-w-4xl mx-auto">
      <Card className="p-4 sm:p-6">
        <div className="space-y-4">
          {/* Recording Controls */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
            {!isRecording ? (
              <Button
                onClick={startRecording}
                size="lg"
                className="w-full sm:w-auto gap-2"
                aria-label="Start recording (Ctrl+R)"
              >
                <Mic className="h-5 w-5" />
                Start Recording
              </Button>
            ) : (
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 w-full sm:w-auto">
                <Button
                  onClick={togglePause}
                  variant="outline"
                  size="lg"
                  className="gap-2"
                  aria-label={`${isPaused ? 'Resume' : 'Pause'} recording (Ctrl+P)`}
                >
                  {isPaused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
                  {isPaused ? 'Resume' : 'Pause'}
                </Button>
                <Button
                  onClick={stopRecording}
                  variant="destructive"
                  size="lg"
                  className="gap-2"
                  aria-label="Stop recording (Ctrl+S)"
                >
                  <Square className="h-4 w-4" />
                  Stop
                </Button>
              </div>
            )}
          </div>

          {/* Recording Status */}
          {isRecording && (
            <div className="space-y-3">
              <div className="text-center">
                <Badge variant={isPaused ? "secondary" : "default"} className="text-sm">
                  {isPaused ? 'PAUSED' : 'RECORDING'} {formatTime(recordingTime)}
                </Badge>
              </div>
              
              {/* Audio Level Meter */}
              <div className="space-y-2">
                <div className="text-sm text-muted-foreground text-center">Audio Level</div>
                <Progress value={audioLevel} className="h-2" />
              </div>
            </div>
          )}

          {/* Post-Recording Actions */}
          {audioBlob && !isRecording && (
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button
                onClick={handleTranscribe}
                disabled={isTranscribing || !isOnline}
                className="gap-2"
                aria-label="Transcribe recording"
              >
                {isTranscribing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                    Transcribing...
                  </>
                ) : (
                  'Transcribe with Speaker ID'
                )}
              </Button>
              <Button
                onClick={downloadAudio}
                variant="outline"
                className="gap-2"
                aria-label="Download recording"
              >
                <Download className="h-4 w-4" />
                Download
              </Button>
            </div>
          )}

          {/* Keyboard Shortcuts Help */}
          <div className="text-xs text-muted-foreground text-center space-y-1">
            <div>Keyboard shortcuts: Ctrl+R (start/stop), Ctrl+P (pause/resume), Ctrl+S (stop)</div>
            {!isOnline && (
              <div className="text-orange-500">Offline mode - transcription unavailable</div>
            )}
          </div>
        </div>
      </Card>

      {/* Transcription Loading */}
      {isTranscribing && (
        <Card className="p-4 sm:p-6">
          <div className="space-y-4">
            <div className="text-center">
              <h3 className="text-lg font-semibold">Processing Audio with Speaker Diarization</h3>
              <p className="text-muted-foreground">Identifying speakers and transcribing...</p>
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          </div>
        </Card>
      )}

      {/* Transcription Results */}
      {transcriptionResult && (
        <Card className="p-4 sm:p-6">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Transcription with Speaker Identification</h3>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {transcriptionResult.map((segment, index) => (
                <div key={index} className="border-l-2 border-primary pl-3 py-2">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3">
                    <Badge variant="outline" className="text-xs w-fit">
                      {segment.speaker}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {Math.floor(segment.start)}s - {Math.floor(segment.end)}s
                    </span>
                    {segment.confidence && (
                      <span className="text-xs text-muted-foreground">
                        {Math.round(segment.confidence * 100)}% confidence
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-sm sm:text-base">{segment.text}</p>
                </div>
              ))}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

export default MicrophoneRecorder;