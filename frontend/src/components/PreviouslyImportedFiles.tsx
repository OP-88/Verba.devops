import React, { useState } from 'react';
import { File, Play, Trash2, Download, Edit, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface ImportedFile {
  id: string;
  name: string;
  size: string;
  duration: string;
  uploadDate: string;
  status: 'completed' | 'processing' | 'failed';
  transcriptId?: string;
}

const PreviouslyImportedFiles: React.FC = () => {
  const [files] = useState<ImportedFile[]>([
    {
      id: '1',
      name: 'meeting-recording-01.mp3',
      size: '15.2 MB',
      duration: '45:30',
      uploadDate: '2024-01-15',
      status: 'completed',
      transcriptId: 'transcript-1'
    },
    {
      id: '2',
      name: 'lecture-physics-chapter5.wav',
      size: '28.7 MB',
      duration: '1:20:15',
      uploadDate: '2024-01-14',
      status: 'completed',
      transcriptId: 'transcript-2'
    },
    {
      id: '3',
      name: 'interview-candidate-a.m4a',
      size: '12.1 MB',
      duration: '35:45',
      uploadDate: '2024-01-12',
      status: 'processing'
    }
  ]);

  const handlePlay = (fileId: string) => {
    console.log(`Playing file: ${fileId}`);
    // Implement audio playback functionality
  };

  const handleDelete = (fileId: string) => {
    console.log(`Deleting file: ${fileId}`);
    // Implement delete functionality
  };

  const handleDownload = (fileId: string) => {
    console.log(`Downloading file: ${fileId}`);
    // Implement download functionality
  };

  const handleEditTranscript = (transcriptId: string) => {
    console.log(`Editing transcript: ${transcriptId}`);
    // Navigate to transcript editor
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'processing': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  if (files.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <File className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No previously imported files</p>
        <p className="text-sm">Your uploaded audio files will appear here</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {files.map((file) => (
        <div key={file.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors">
          <div className="flex items-center space-x-4 flex-1">
            <File className="h-8 w-8 text-primary" />
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{file.name}</p>
              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                <span>{file.size}</span>
                <span className="flex items-center">
                  <Clock className="h-3 w-3 mr-1" />
                  {file.duration}
                </span>
                <span>{file.uploadDate}</span>
              </div>
            </div>
            <Badge className={getStatusColor(file.status)}>
              {file.status}
            </Badge>
          </div>
          
          <div className="flex items-center space-x-2 ml-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handlePlay(file.id)}
              title="Play audio"
            >
              <Play className="h-4 w-4" />
            </Button>
            
            {file.transcriptId && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => handleEditTranscript(file.transcriptId!)}
                title="Edit transcript"
              >
                <Edit className="h-4 w-4" />
              </Button>
            )}
            
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleDownload(file.id)}
              title="Download file"
            >
              <Download className="h-4 w-4" />
            </Button>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleDelete(file.id)}
              title="Delete file"
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default PreviouslyImportedFiles;