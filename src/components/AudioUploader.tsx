import React, { useState, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from '@/hooks/use-toast';
import { Upload, File, X, CheckCircle } from 'lucide-react';
import { apiService } from '@/services/api';

const api = apiService;

interface AudioUploaderProps {
  onTranscriptionComplete?: (result: any) => void;
  isOnline?: boolean;
}

interface UploadedFile {
  file: File;
  status: 'pending' | 'uploading' | 'processing' | 'completed' | 'error';
  progress: number;
  result?: any;
  error?: string;
}

const SUPPORTED_FORMATS = ['wav', 'mp3', 'm4a', 'flac', 'ogg', 'webm'];
const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB

export default function AudioUploader({ onTranscriptionComplete, isOnline = true }: AudioUploaderProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      return `File size must be less than 25MB. Current size: ${(file.size / 1024 / 1024).toFixed(2)}MB`;
    }

    // Check file format
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!extension || !SUPPORTED_FORMATS.includes(extension)) {
      return `Unsupported format. Supported formats: ${SUPPORTED_FORMATS.join(', ')}`;
    }

    // Check MIME type
    if (!file.type.startsWith('audio/') && !file.type.startsWith('video/')) {
      return 'Invalid file type. Please upload an audio file.';
    }

    return null;
  };

  const handleFiles = useCallback((newFiles: FileList | null) => {
    if (!newFiles) return;

    const validFiles: UploadedFile[] = [];
    const errors: string[] = [];

    Array.from(newFiles).forEach(file => {
      const error = validateFile(file);
      if (error) {
        errors.push(`${file.name}: ${error}`);
      } else {
        validFiles.push({
          file,
          status: 'pending',
          progress: 0
        });
      }
    });

    if (errors.length > 0) {
      toast({
        title: "File Validation Error",
        description: errors.join('\n'),
        variant: "destructive"
      });
    }

    if (validFiles.length > 0) {
      setFiles(prev => [...prev, ...validFiles]);
      toast({
        title: "Files Added",
        description: `${validFiles.length} file(s) ready for transcription`
      });
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files);
    if (e.target) {
      e.target.value = '';
    }
  }, [handleFiles]);

  const processFile = async (index: number) => {
    if (!isOnline) {
      toast({
        title: "Connection Error",
        description: "Backend server is not available",
        variant: "destructive"
      });
      return;
    }

    const file = files[index];
    if (!file || file.status !== 'pending') return;

    // Update status to uploading
    setFiles(prev => prev.map((f, i) => 
      i === index ? { ...f, status: 'uploading' as const, progress: 0 } : f
    ));

    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setFiles(prev => prev.map((f, i) => 
          i === index && f.progress < 90 
            ? { ...f, progress: f.progress + 10 } 
            : f
        ));
      }, 200);

      // Upload and transcribe
      const result = await api.transcribeAudio(file.file);
      
      clearInterval(progressInterval);

      // Update status to completed
      setFiles(prev => prev.map((f, i) => 
        i === index 
          ? { ...f, status: 'completed' as const, progress: 100, result } 
          : f
      ));

      toast({
        title: "Transcription Complete",
        description: `Successfully transcribed ${file.file.name}`
      });

      // Notify parent component
      if (onTranscriptionComplete) {
        onTranscriptionComplete(result);
      }

    } catch (error) {
      setFiles(prev => prev.map((f, i) => 
        i === index 
          ? { 
              ...f, 
              status: 'error' as const, 
              progress: 0, 
              error: error instanceof Error ? error.message : 'Transcription failed' 
            } 
          : f
      ));

      toast({
        title: "Transcription Failed",
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: "destructive"
      });
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const processAllFiles = async () => {
    const pendingFiles = files.map((_, index) => index).filter(index => 
      files[index].status === 'pending'
    );
    
    for (const index of pendingFiles) {
      await processFile(index);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'error':
        return <X className="w-5 h-5 text-red-400" />;
      default:
        return <File className="w-5 h-5 text-blue-400" />;
    }
  };

  const getStatusColor = (status: UploadedFile['status']) => {
    switch (status) {
      case 'completed': return 'text-green-400';
      case 'error': return 'text-red-400';
      case 'uploading': 
      case 'processing': return 'text-yellow-400';
      default: return 'text-blue-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <Card className="backdrop-blur-md bg-white/5 border-white/10">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Upload Audio Files
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 cursor-pointer
              ${isDragOver 
                ? 'border-blue-400 bg-blue-400/10' 
                : 'border-white/30 hover:border-white/50 hover:bg-white/5'
              }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="w-12 h-12 text-white/60 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">
              Drop audio files here or click to browse
            </h3>
            <p className="text-sm text-white/60 mb-4">
              Supports: WAV, MP3, M4A, FLAC, OGG, WebM (Max 25MB each)
            </p>
            <Button variant="outline" className="border-white/20 text-white hover:bg-white/10">
              Select Files
            </Button>
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="audio/*,video/*"
            onChange={handleFileInput}
            className="hidden"
          />
        </CardContent>
      </Card>

      {/* File List */}
      {files.length > 0 && (
        <Card className="backdrop-blur-md bg-white/5 border-white/10">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-white">Upload Queue ({files.length})</CardTitle>
            <Button
              onClick={processAllFiles}
              disabled={!isOnline || files.every(f => f.status !== 'pending')}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              Process All
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {files.map((uploadedFile, index) => (
              <div
                key={index}
                className="flex items-center gap-4 p-4 rounded-lg bg-white/5 border border-white/10"
              >
                {getStatusIcon(uploadedFile.status)}
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-white font-medium truncate">
                      {uploadedFile.file.name}
                    </p>
                    <button
                      onClick={() => removeFile(index)}
                      className="text-white/60 hover:text-red-400 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-white/60">
                      {formatFileSize(uploadedFile.file.size)}
                    </span>
                    <span className={`capitalize ${getStatusColor(uploadedFile.status)}`}>
                      {uploadedFile.status}
                    </span>
                  </div>
                  
                  {(uploadedFile.status === 'uploading' || uploadedFile.status === 'processing') && (
                    <Progress value={uploadedFile.progress} className="mt-2 h-2" />
                  )}
                  
                  {uploadedFile.error && (
                    <p className="text-red-400 text-sm mt-2">{uploadedFile.error}</p>
                  )}
                </div>
                
                <div className="flex gap-2">
                  {uploadedFile.status === 'pending' && (
                    <Button
                      size="sm"
                      onClick={() => processFile(index)}
                      disabled={!isOnline}
                      className="bg-blue-600 hover:bg-blue-700 text-white"
                    >
                      Process
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Help */}
      {!isOnline && (
        <Alert className="bg-orange-500/10 border-orange-500/20 text-orange-200">
          <AlertDescription>
            Backend server is not available. Please ensure the FastAPI server is running.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}