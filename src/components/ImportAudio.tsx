import React, { useState } from 'react';
import { ArrowLeft, Upload, File, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface ImportAudioProps {
  onBack: () => void;
  isOnline: boolean;
}

const ImportAudio: React.FC<ImportAudioProps> = ({ onBack, isOnline }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = () => {
    if (!selectedFile) return;
    
    setIsProcessing(true);
    // Simulate upload progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsProcessing(false);
          return 100;
        }
        return prev + 10;
      });
    }, 500);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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
            <h1 className="text-3xl font-bold">Import Audio</h1>
            <p className="text-muted-foreground">Upload audio files for transcription</p>
          </div>
        </div>

        {/* Upload Section */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Upload Audio File</CardTitle>
          </CardHeader>
          <CardContent>
            <div 
              className="border-2 border-dashed border-border rounded-lg p-8 text-center hover:border-primary/50 transition-colors cursor-pointer"
              onClick={() => document.getElementById('file-input')?.click()}
            >
              <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <p className="text-lg font-medium mb-2">
                {selectedFile ? selectedFile.name : 'Click to upload or drag and drop'}
              </p>
              <p className="text-muted-foreground">
                Supported formats: MP3, WAV, M4A, FLAC
              </p>
              {selectedFile && (
                <p className="text-sm text-muted-foreground mt-2">
                  Size: {formatFileSize(selectedFile.size)}
                </p>
              )}
            </div>
            
            <input
              id="file-input"
              type="file"
              accept="audio/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </CardContent>
        </Card>

        {/* Selected File Info */}
        {selectedFile && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Selected File</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-4">
                <File className="h-8 w-8 text-primary" />
                <div className="flex-1">
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatFileSize(selectedFile.size)} • {selectedFile.type}
                  </p>
                </div>
                <Button
                  onClick={handleUpload}
                  disabled={!isOnline || isProcessing}
                  className="bg-blue-500 hover:bg-blue-600"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    'Start Transcription'
                  )}
                </Button>
              </div>
              
              {isProcessing && (
                <div className="mt-4">
                  <Progress value={progress} className="w-full" />
                  <p className="text-sm text-muted-foreground mt-2">
                    Processing: {progress}%
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Offline Message */}
        {!isOnline && (
          <Card className="border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-950">
            <CardContent className="p-6">
              <p className="text-orange-800 dark:text-orange-200">
                Audio transcription requires an internet connection. Please connect to the internet to upload and process your audio files.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default ImportAudio;