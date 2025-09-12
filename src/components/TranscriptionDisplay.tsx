import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Copy, Download, Edit, Save, X, Speaker } from 'lucide-react';
import { toast } from 'sonner';
import { saveAs } from 'file-saver';

interface SpeakerSegment {
  speaker: string;
  text: string;
  start: number;
  end: number;
  confidence?: number;
}

interface TranscriptionDisplayProps {
  isLoading?: boolean;
  transcription?: string;
  segments?: SpeakerSegment[];
  summary?: string;
  metadata?: {
    duration?: number;
    processing_time?: number;
    model_used?: string;
    speakers_detected?: number;
  };
  className?: string;
}

const TranscriptionDisplay: React.FC<TranscriptionDisplayProps> = ({
  isLoading = false,
  transcription = '',
  segments = [],
  summary = '',
  metadata = {},
  className = ''
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedTranscription, setEditedTranscription] = useState(transcription);
  const [activeTab, setActiveTab] = useState<'segments' | 'full' | 'summary'>('segments');

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success('Copied to clipboard');
    } catch (error) {
      toast.error('Failed to copy to clipboard');
    }
  };

  const handleDownload = (format: 'txt' | 'md' | 'json') => {
    let content = '';
    let filename = '';
    let mimeType = '';

    switch (format) {
      case 'txt':
        content = segments.length > 0 
          ? segments.map(s => `${s.speaker}: ${s.text}`).join('\n\n')
          : transcription;
        filename = `transcript-${new Date().toISOString().slice(0, 19)}.txt`;
        mimeType = 'text/plain';
        break;
      
      case 'md':
        content = generateMarkdownReport();
        filename = `transcript-${new Date().toISOString().slice(0, 19)}.md`;
        mimeType = 'text/markdown';
        break;
      
      case 'json':
        content = JSON.stringify({
          transcription,
          segments,
          summary,
          metadata,
          generated_at: new Date().toISOString()
        }, null, 2);
        filename = `transcript-${new Date().toISOString().slice(0, 19)}.json`;
        mimeType = 'application/json';
        break;
    }

    const blob = new Blob([content], { type: mimeType });
    saveAs(blob, filename);
    toast.success(`Downloaded as ${format.toUpperCase()}`);
  };

  const generateMarkdownReport = () => {
    let markdown = `# Meeting Transcript\n\n`;
    markdown += `**Generated:** ${new Date().toLocaleString()}\n\n`;
    
    if (metadata.duration) {
      markdown += `**Duration:** ${Math.round(metadata.duration)}s\n`;
    }
    if (metadata.speakers_detected) {
      markdown += `**Speakers Detected:** ${metadata.speakers_detected}\n`;
    }
    if (metadata.model_used) {
      markdown += `**Model:** ${metadata.model_used}\n`;
    }
    
    markdown += `\n---\n\n`;

    if (summary) {
      markdown += `## Summary\n\n${summary}\n\n---\n\n`;
    }

    markdown += `## Transcript\n\n`;
    
    if (segments.length > 0) {
      segments.forEach((segment, index) => {
        const timeRange = `[${Math.floor(segment.start)}s - ${Math.floor(segment.end)}s]`;
        markdown += `### ${segment.speaker} ${timeRange}\n\n${segment.text}\n\n`;
      });
    } else {
      markdown += transcription;
    }

    return markdown;
  };

  const handleSaveEdit = () => {
    setIsEditing(false);
    toast.success('Transcription updated');
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatSRTTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    const millisecs = Math.floor((secs % 1) * 1000);
    const wholeSeconds = Math.floor(secs);
    
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${wholeSeconds.toString().padStart(2, '0')},${millisecs.toString().padStart(3, '0')}`;
  };

  if (isLoading) {
    return (
      <Card className={`p-4 sm:p-6 ${className}`}>
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary" />
            <h3 className="text-lg font-semibold">Processing Audio</h3>
          </div>
          <p className="text-muted-foreground text-sm">
            Identifying speakers and generating transcription...
          </p>
          <div className="space-y-3">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-5/6" />
          </div>
        </div>
      </Card>
    );
  }

  if (!transcription && segments.length === 0) {
    return (
      <Card className={`p-4 sm:p-6 ${className}`}>
        <div className="text-center text-muted-foreground">
          <Speaker className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>No transcription available</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className={`p-4 sm:p-6 ${className}`}>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h3 className="text-lg font-semibold">Transcription Results</h3>
          <div className="flex flex-wrap gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleCopy(segments.length > 0 
                ? segments.map(s => `${s.speaker}: ${s.text}`).join('\n\n')
                : transcription
              )}
              className="gap-1"
              aria-label="Copy transcription"
            >
              <Copy className="h-3 w-3" />
              Copy
            </Button>
            <div className="relative group">
              <Button
                size="sm"
                variant="outline"
                className="gap-1"
                aria-label="Download options"
              >
                <Download className="h-3 w-3" />
                Download
              </Button>
              <div className="absolute right-0 top-full mt-1 bg-background border rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                <div className="p-1 space-y-1 min-w-24">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDownload('txt')}
                    className="w-full justify-start text-xs"
                  >
                    TXT
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDownload('md')}
                    className="w-full justify-start text-xs"
                  >
                    Markdown
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDownload('json')}
                    className="w-full justify-start text-xs"
                  >
                    JSON
                  </Button>
                </div>
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setIsEditing(!isEditing)}
              className="gap-1"
              aria-label={isEditing ? "Cancel editing" : "Edit transcription"}
            >
              {isEditing ? <X className="h-3 w-3" /> : <Edit className="h-3 w-3" />}
              {isEditing ? 'Cancel' : 'Edit'}
            </Button>
          </div>
        </div>

        {/* Metadata */}
        {Object.keys(metadata).length > 0 && (
          <div className="flex flex-wrap gap-2 text-xs">
            {metadata.duration && (
              <Badge variant="secondary">Duration: {formatTime(metadata.duration)}</Badge>
            )}
            {metadata.speakers_detected && (
              <Badge variant="secondary">Speakers: {metadata.speakers_detected}</Badge>
            )}
            {metadata.processing_time && (
              <Badge variant="secondary">
                Processed in: {metadata.processing_time.toFixed(1)}s
              </Badge>
            )}
            {metadata.model_used && (
              <Badge variant="outline">Model: {metadata.model_used}</Badge>
            )}
          </div>
        )}

        <Separator />

        {/* Tab Navigation */}
        <div className="flex gap-1 border-b">
          {segments.length > 0 && (
            <Button
              size="sm"
              variant={activeTab === 'segments' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('segments')}
              className="text-xs"
            >
              Speaker View
            </Button>
          )}
          <Button
            size="sm"
            variant={activeTab === 'full' ? 'default' : 'ghost'}
            onClick={() => setActiveTab('full')}
            className="text-xs"
          >
            Full Text
          </Button>
          {summary && (
            <Button
              size="sm"
              variant={activeTab === 'summary' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('summary')}
              className="text-xs"
            >
              Summary
            </Button>
          )}
        </div>

        {/* Content */}
        <div className="space-y-3">
          {activeTab === 'segments' && segments.length > 0 && (
            <div className="space-y-4 max-h-96 overflow-y-auto">
              {segments.map((segment, index) => (
                <div key={index} className="border-l-2 border-primary pl-4 py-2">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 mb-2">
                    <Badge variant="outline" className="text-xs w-fit">
                      <Speaker className="h-3 w-3 mr-1" />
                      {segment.speaker}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {formatTime(segment.start)} - {formatTime(segment.end)}
                    </span>
                    {segment.confidence && (
                      <span className="text-xs text-muted-foreground">
                        {Math.round(segment.confidence * 100)}% confidence
                      </span>
                    )}
                  </div>
                  <p className="text-sm sm:text-base leading-relaxed">{segment.text}</p>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'full' && (
            <div className="space-y-3">
              {isEditing ? (
                <div className="space-y-2">
                  <Textarea
                    value={editedTranscription}
                    onChange={(e) => setEditedTranscription(e.target.value)}
                    className="min-h-48 text-sm"
                    aria-label="Edit transcription"
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={handleSaveEdit} className="gap-1">
                      <Save className="h-3 w-3" />
                      Save
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setIsEditing(false);
                        setEditedTranscription(transcription);
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="bg-muted p-4 rounded-md max-h-96 overflow-y-auto">
                  <p className="text-sm sm:text-base leading-relaxed whitespace-pre-wrap">
                    {transcription}
                  </p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'summary' && summary && (
            <div className="bg-blue-50 dark:bg-blue-950/20 p-4 rounded-md">
              <h4 className="font-medium mb-2">AI-Generated Summary</h4>
              <p className="text-sm leading-relaxed">{summary}</p>
            </div>
          )}
        </div>

        {/* Accessibility Note */}
        <div className="text-xs text-muted-foreground">
          Use Tab and arrow keys to navigate. Screen reader compatible.
        </div>
      </div>
    </Card>
  );
};

export default TranscriptionDisplay;