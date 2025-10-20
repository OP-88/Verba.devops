import React, { useState, useRef, useEffect } from 'react';
import { ArrowLeft, Mic, MicOff, Square, Play, Pause } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';

interface LiveMeetingProps {
  onBack: () => void;
  isOnline: boolean;
}

const LiveMeeting: React.FC<LiveMeetingProps> = ({ onBack, isOnline }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [transcript, setTranscript] = useState('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Auto-scroll effect for transcript
  useEffect(() => {
    if (scrollAreaRef.current && transcript) {
      const viewport = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  }, [transcript]);

  // Simulate live transcript updates when recording
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (isRecording && !isPaused) {
      const sampleTexts = [
        "Welcome everyone to today's meeting.",
        "Let's start by discussing the quarterly results.",
        "As you can see from the data presented...",
        "The growth numbers are quite impressive this quarter.",
        "Moving on to our next agenda item...",
        "I'd like to hear everyone's thoughts on this proposal.",
        "Let's take a moment to review the timeline.",
        "Are there any questions or concerns about this approach?",
        "Thank you for your input on this matter.",
        "Let's schedule a follow-up meeting to discuss next steps."
      ];
      
      let textIndex = 0;
      interval = setInterval(() => {
        if (textIndex < sampleTexts.length) {
          setTranscript(prev => {
            const newText = prev + (prev ? ' ' : '') + sampleTexts[textIndex];
            return newText;
          });
          textIndex++;
        }
      }, 3000); // Add new text every 3 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRecording, isPaused]);

  const handleStartRecording = () => {
    setIsRecording(true);
    setIsPaused(false);
    setTranscript(''); // Clear previous transcript
    // Start recording logic would go here
  };

  const handlePauseRecording = () => {
    setIsPaused(!isPaused);
    // Pause/resume recording logic would go here
  };

  const handleStopRecording = () => {
    setIsRecording(false);
    setIsPaused(false);
    setRecordingTime(0);
    // Keep transcript visible after stopping
    // Stop recording logic would go here
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center mb-8">
          <Button
            variant="ghost"
            size="icon"
            onClick={onBack}
            className="mr-4"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Live Meeting</h1>
            <p className="text-muted-foreground">Real-time transcription</p>
          </div>
        </div>

        {/* Recording Controls */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Recording Controls</span>
              {isRecording && (
                <Badge variant={isPaused ? "secondary" : "default"}>
                  {isPaused ? 'Paused' : 'Recording'}
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center space-x-4">
              {!isRecording ? (
                <Button
                  onClick={handleStartRecording}
                  size="lg"
                  className="bg-green-500 hover:bg-green-600"
                  disabled={!isOnline}
                >
                  <Mic className="h-5 w-5 mr-2" />
                  Start Recording
                </Button>
              ) : (
                <div className="flex space-x-4">
                  <Button
                    onClick={handlePauseRecording}
                    size="lg"
                    variant="outline"
                  >
                    {isPaused ? <Play className="h-5 w-5 mr-2" /> : <Pause className="h-5 w-5 mr-2" />}
                    {isPaused ? 'Resume' : 'Pause'}
                  </Button>
                  <Button
                    onClick={handleStopRecording}
                    size="lg"
                    variant="destructive"
                  >
                    <Square className="h-5 w-5 mr-2" />
                    Stop
                  </Button>
                </div>
              )}
            </div>
            
            {!isOnline && (
              <p className="text-center text-muted-foreground mt-4">
                Please connect to the internet to use live transcription
              </p>
            )}
          </CardContent>
        </Card>

        {/* Live Transcript */}
        <Card>
          <CardHeader>
            <CardTitle>Live Transcript</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea ref={scrollAreaRef} className="h-[400px] w-full">
              <div className="p-4 bg-muted/30 rounded-lg min-h-[350px]">
                {transcript ? (
                  <div className="space-y-2">
                    <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                      {transcript}
                    </p>
                    {isRecording && !isPaused && (
                      <div className="flex items-center gap-2 mt-4">
                        <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                        <span className="text-xs text-muted-foreground">Recording...</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center text-muted-foreground">
                      {isRecording ? (
                        isPaused ? 'Recording paused...' : 'Listening for speech...'
                      ) : (
                        'Start recording to see live transcription'
                      )}
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default LiveMeeting;