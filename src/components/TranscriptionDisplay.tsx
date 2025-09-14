import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Copy, Download, Edit, Save, X, Speaker, Clock, FileText } from 'lucide-react';
import { toast } from 'sonner';
import { saveAs } from 'file-saver';
import { TranscriptionResult } from '@/types';

interface TranscriptionDisplayProps {
  transcription: Transcription;
}

const TranscriptionDisplay: React.FC<TranscriptionDisplayProps> = ({
  transcription
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState(transcription.text);

  const handleCopy = () => {
    navigator.clipboard.writeText(transcription.text);
    toast.success('Transcription copied to clipboard');
  };

  const handleSaveEdit = () => {
    setIsEditing(false);
    toast.success('Transcription updated');
  };

  const handleExport = (format: 'txt' | 'json' | 'srt') => {
    let content = '';
    let filename = '';
    let mimeType = '';

    switch (format) {
      case 'txt':
        content = transcription.text;
        filename = `${transcription.file_name}_transcript.txt`;
        mimeType = 'text/plain';
        break;
      case 'json':
        content = JSON.stringify(transcription, null, 2);
        filename = `${transcription.file_name}_transcript.json`;
        mimeType = 'application/json';
        break;
      case 'srt':
        content = generateSRT();
        filename = `${transcription.file_name}_transcript.srt`;
        mimeType = 'text/plain';
        break;
    }

    const blob = new Blob([content], { type: mimeType });
    saveAs(blob, filename);
    toast.success(`Exported as ${format.toUpperCase()}`);
  };

  const generateSRT = () => {
    if (!transcription.segments || transcription.segments.length === 0) {
      return transcription.text;
    }

    return transcription.segments
      .map((segment, index) => {
        const formatTime = (seconds: number) => {
          const date = new Date(seconds * 1000);
          const hours = Math.floor(seconds / 3600);
          const minutes = Math.floor((seconds % 3600) / 60);
          const secs = Math.floor(seconds % 60);
          const ms = Math.floor((seconds % 1) * 1000);
          return `${hours.toString().padStart(2, '0')}:${minutes
            .toString()
            .padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms
            .toString()
            .padStart(3, '0')}`;
        };

        return `${index + 1}\n${formatTime(segment.start)} --> ${formatTime(
          segment.end
        )}\n${segment.text}\n`;
      })
      .join('\n');
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header with metadata */}
      <Card className="p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-xl font-semibold">{transcription.file_name}</h2>
            <p className="text-sm text-muted-foreground">
              {formatDate(transcription.created_at)}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">
              <Clock className="w-3 h-3 mr-1" />
              {formatDuration(transcription.duration)}
            </Badge>
            <Badge variant="outline">
              {transcription.language}
            </Badge>
            <Badge variant="outline">
              {Math.round(transcription.confidence * 100)}% confidence
            </Badge>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" size="sm" onClick={handleCopy}>
            <Copy className="w-4 h-4 mr-2" />
            Copy
          </Button>
          <Button variant="outline" size="sm" onClick={() => setIsEditing(!isEditing)}>
            {isEditing ? <Save className="w-4 h-4 mr-2" /> : <Edit className="w-4 h-4 mr-2" />}
            {isEditing ? 'Save' : 'Edit'}
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport('txt')}>
            <Download className="w-4 h-4 mr-2" />
            TXT
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport('json')}>
            <Download className="w-4 h-4 mr-2" />
            JSON
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport('srt')}>
            <Download className="w-4 h-4 mr-2" />
            SRT
          </Button>
        </div>
      </Card>

      {/* Transcription text */}
      <Card className="p-6">
        <div className="flex items-center gap-2 mb-4">
          <FileText className="w-5 h-5" />
          <h3 className="text-lg font-medium">Transcription</h3>
        </div>
        
        {isEditing ? (
          <div className="space-y-4">
            <Textarea
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
              className="min-h-[200px] resize-none"
              placeholder="Edit transcription..."
            />
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSaveEdit}>
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </Button>
              <Button variant="outline" size="sm" onClick={() => {
                setIsEditing(false);
                setEditedText(transcription.text);
              }}>
                <X className="w-4 h-4 mr-2" />
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="prose max-w-none" aria-live="polite">
            {transcription.text ? (
              <div className="text-sm leading-relaxed whitespace-pre-wrap">
                {/* Parse speaker labels if present */}
                {transcription.text.split('\n').map((line, index) => {
                  const speakerMatch = line.match(/^Speaker (\w+): (.+)$/);
                  if (speakerMatch) {
                    return (
                      <div key={index} className="mb-3 p-3 bg-muted/50 rounded-lg">
                        <Badge variant="outline" className="mb-2">
                          <Speaker className="w-3 h-3 mr-1" />
                          Speaker {speakerMatch[1]}
                        </Badge>
                        <p>{speakerMatch[2]}</p>
                      </div>
                    );
                  }
                  return line.trim() ? <p key={index} className="mb-2">{line}</p> : null;
                })}
              </div>
            ) : (
              <div className="flex items-center justify-center h-20">
                <div className="animate-spin h-6 w-6 border-t-2 border-blue-500 rounded-full"></div>
                <span className="ml-2 text-muted-foreground">Processing transcription...</span>
              </div>
            )}
          </div>
        )}
      </Card>

      {/* Segments if available */}
      {transcription.segments && transcription.segments.length > 0 && (
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Speaker className="w-5 h-5" />
            <h3 className="text-lg font-medium">Segments</h3>
          </div>
          <div className="space-y-3">
            {transcription.segments.map((segment, index) => (
              <div key={index} className="border-l-4 border-primary pl-4 py-2">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline" className="text-xs">
                    {Math.floor(segment.start)}s - {Math.floor(segment.end)}s
                  </Badge>
                </div>
                <p className="text-sm">{segment.text}</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};

export default TranscriptionDisplay;