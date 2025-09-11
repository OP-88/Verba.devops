import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { 
  Search, 
  Download, 
  Copy, 
  Trash2, 
  RefreshCw, 
  FileText,
  Speaker,
  Calendar,
  Clock
} from 'lucide-react';
import { toast } from 'sonner';
import { saveAs } from 'file-saver';
import { apiService } from '../services/api';
import { TranscriptionHistoryItem } from '../types/api';

interface TranscriptionHistoryProps {
  refreshTrigger?: number;
  className?: string;
}

interface TranscriptionItem extends TranscriptionHistoryItem {
  segments?: Array<{
    speaker: string;
    text: string;
    start: number;
    end: number;
  }>;
  summary?: string;
}

export const TranscriptionHistory: React.FC<TranscriptionHistoryProps> = ({ 
  refreshTrigger = 0,
  className = ''
}) => {
  const [transcriptions, setTranscriptions] = useState<TranscriptionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'date' | 'duration' | 'filename'>('date');

  const fetchTranscriptions = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getTranscriptions('default');
      setTranscriptions(data);
    } catch (err) {
      setError('Failed to load transcription history');
      console.error('Error fetching transcriptions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTranscriptions();
  }, [refreshTrigger]);

  const filteredAndSortedTranscriptions = React.useMemo(() => {
    let filtered = transcriptions.filter(t => 
      t.transcription.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.summary?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return filtered.sort((a, b) => {
      switch (sortBy) {
        case 'date':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'duration':
          return (b.audio_duration || 0) - (a.audio_duration || 0);
        case 'filename':
          return (a.filename || '').localeCompare(b.filename || '');
        default:
          return 0;
      }
    });
  }, [transcriptions, searchTerm, sortBy]);

  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success('Copied to clipboard');
    } catch (error) {
      toast.error('Failed to copy to clipboard');
    }
  };

  const exportNote = (transcription: TranscriptionItem, format: 'txt' | 'md' | 'json') => {
    let content = '';
    let filename = '';
    let mimeType = '';

    const timestamp = new Date(transcription.created_at).toLocaleString();
    
    switch (format) {
      case 'txt':
        content = `Transcription from ${timestamp}\n`;
        content += `File: ${transcription.filename || 'Unknown'}\n`;
        if (transcription.summary) {
          content += `\nSummary:\n${transcription.summary}\n`;
        }
        content += `\nTranscript:\n${transcription.transcription}`;
        filename = `transcript-${transcription.id}.txt`;
        mimeType = 'text/plain';
        break;
      
      case 'md':
        content = `# Transcription Report\n\n`;
        content += `**Date:** ${timestamp}  \n`;
        content += `**File:** ${transcription.filename || 'Unknown'}  \n`;
        content += `**Duration:** ${transcription.audio_duration ? Math.round(transcription.audio_duration) + 's' : 'Unknown'}  \n`;
        content += `**Model:** ${transcription.model_used || 'Unknown'}  \n`;
        content += `**Confidence:** ${Math.round(transcription.confidence * 100)}%  \n\n`;
        
        if (transcription.summary) {
          content += `## Summary\n\n${transcription.summary}\n\n`;
        }
        
        content += `## Transcript\n\n`;
        if (transcription.segments && transcription.segments.length > 0) {
          transcription.segments.forEach(segment => {
            const timeRange = `[${Math.floor(segment.start)}s - ${Math.floor(segment.end)}s]`;
            content += `### ${segment.speaker} ${timeRange}\n\n${segment.text}\n\n`;
          });
        } else {
          content += transcription.transcription;
        }
        
        filename = `transcript-${transcription.id}.md`;
        mimeType = 'text/markdown';
        break;
      
      case 'json':
        content = JSON.stringify(transcription, null, 2);
        filename = `transcript-${transcription.id}.json`;
        mimeType = 'application/json';
        break;
    }

    const blob = new Blob([content], { type: mimeType });
    saveAs(blob, filename);
    toast.success(`Exported as ${format.toUpperCase()}`);
  };

  const deleteTranscription = async (id: string) => {
    if (!confirm('Are you sure you want to delete this transcription?')) return;
    
    try {
      // Implement delete API call here
      setTranscriptions(prev => prev.filter(t => t.id !== id));
      toast.success('Transcription deleted');
    } catch (error) {
      toast.error('Failed to delete transcription');
    }
  };

  const formatTime = (seconds?: number) => {
    if (!seconds) return 'Unknown';
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

  if (loading) {
    return (
      <Card className={`p-4 sm:p-6 ${className}`}>
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary" />
            <h3 className="text-lg font-semibold">Loading History...</h3>
          </div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="border rounded-lg p-4 space-y-2">
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-2/3" />
              </div>
            ))}
          </div>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={`p-4 sm:p-6 ${className}`}>
        <div className="text-center space-y-4">
          <div className="text-red-500">
            <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>{error}</p>
          </div>
          <Button onClick={fetchTranscriptions} variant="outline" className="gap-2">
            <RefreshCw className="h-4 w-4" />
            Retry
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card className={`p-4 sm:p-6 ${className}`}>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <h3 className="text-lg font-semibold">Transcription History</h3>
          <Button
            onClick={fetchTranscriptions}
            variant="outline"
            size="sm"
            className="gap-2 w-fit"
            aria-label="Refresh transcription history"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>

        {/* Controls */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search transcriptions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              aria-label="Search transcriptions"
            />
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant={sortBy === 'date' ? 'default' : 'outline'}
              onClick={() => setSortBy('date')}
              className="gap-1"
            >
              <Calendar className="h-3 w-3" />
              Date
            </Button>
            <Button
              size="sm"
              variant={sortBy === 'duration' ? 'default' : 'outline'}
              onClick={() => setSortBy('duration')}
              className="gap-1"
            >
              <Clock className="h-3 w-3" />
              Duration
            </Button>
            <Button
              size="sm"
              variant={sortBy === 'filename' ? 'default' : 'outline'}
              onClick={() => setSortBy('filename')}
              className="gap-1"
            >
              <FileText className="h-3 w-3" />
              File
            </Button>
          </div>
        </div>

        {/* Results Count */}
        <div className="text-sm text-muted-foreground">
          {filteredAndSortedTranscriptions.length} of {transcriptions.length} transcriptions
        </div>

        {/* Transcription List */}
        {filteredAndSortedTranscriptions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>No transcriptions found</p>
            {searchTerm && (
              <Button
                variant="link"
                onClick={() => setSearchTerm('')}
                className="mt-2"
              >
                Clear search
              </Button>
            )}
          </div>
        ) : (
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {filteredAndSortedTranscriptions.map((item) => (
              <div key={item.id} className="border rounded-lg p-4 space-y-3">
                {/* Item Header */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                  <div className="space-y-1">
                    <h4 className="font-medium text-sm">
                      {item.filename || `Transcription ${item.id.slice(0, 8)}`}
                    </h4>
                    <div className="flex flex-wrap gap-2 text-xs">
                      <Badge variant="outline">
                        {formatDate(item.created_at)}
                      </Badge>
                      {item.audio_duration && (
                        <Badge variant="secondary">
                          <Clock className="h-3 w-3 mr-1" />
                          {formatTime(item.audio_duration)}
                        </Badge>
                      )}
                      {item.segments && item.segments.length > 0 && (
                        <Badge variant="secondary">
                          <Speaker className="h-3 w-3 mr-1" />
                          {new Set(item.segments.map(s => s.speaker)).size} speakers
                        </Badge>
                      )}
                      <Badge variant="outline">
                        {Math.round(item.confidence * 100)}% confidence
                      </Badge>
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleCopy(item.transcription)}
                      className="h-8 w-8 p-0"
                      aria-label="Copy transcription"
                    >
                      <Copy className="h-3 w-3" />
                    </Button>
                    <div className="relative group">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 w-8 p-0"
                        aria-label="Download options"
                      >
                        <Download className="h-3 w-3" />
                      </Button>
                      <div className="absolute right-0 top-full mt-1 bg-background border rounded-md shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                        <div className="p-1 space-y-1 min-w-20">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => exportNote(item, 'txt')}
                            className="w-full justify-start text-xs"
                          >
                            TXT
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => exportNote(item, 'md')}
                            className="w-full justify-start text-xs"
                          >
                            Markdown
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => exportNote(item, 'json')}
                            className="w-full justify-start text-xs"
                          >
                            JSON
                          </Button>
                        </div>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => deleteTranscription(item.id)}
                      className="h-8 w-8 p-0 text-red-500 hover:text-red-700"
                      aria-label="Delete transcription"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>

                {/* Summary */}
                {item.summary && (
                  <div className="bg-blue-50 dark:bg-blue-950/20 p-3 rounded text-sm">
                    <div className="font-medium mb-1">Summary:</div>
                    <p className="text-muted-foreground">{item.summary}</p>
                  </div>
                )}

                {/* Transcription Preview */}
                <div className="bg-muted p-3 rounded text-sm">
                  <p className="line-clamp-3">
                    {item.transcription.substring(0, 200)}
                    {item.transcription.length > 200 && '...'}
                  </p>
                </div>

                {/* Speaker Segments Preview */}
                {item.segments && item.segments.length > 0 && (
                  <div className="text-xs text-muted-foreground">
                    Speakers: {new Set(item.segments.map(s => s.speaker)).size} detected
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
};
