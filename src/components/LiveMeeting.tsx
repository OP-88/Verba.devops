import React, { useState } from 'react';
import { ArrowLeft, Mic, MicOff, Square, Play, Pause } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface LiveMeetingProps {
  onBack: () => void;
  isOnline: boolean;
}

const LiveMeeting: React.FC<LiveMeetingProps> = ({ onBack, isOnline }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);

  const handleStartRecording = () => {
    setIsRecording(true);
    setIsPaused(false);
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
            <div className="min-h-[300px] p-4 bg-muted/30 rounded-lg">
              {isRecording ? (
                <div className="text-center text-muted-foreground">
                  {isPaused ? 'Recording paused...' : 'Listening for speech...'}
                </div>
              ) : (
                <div className="text-center text-muted-foreground">
                  Start recording to see live transcription
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default LiveMeeting;