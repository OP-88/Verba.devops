import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { 
  Copy, Download, Edit, Save, X, Speaker, Clock, FileText, 
  FileDown, FileType, Hash, Eye 
} from 'lucide-react';
import { toast } from 'sonner';
import { saveAs } from 'file-saver';
import { useHotkeys } from 'react-hotkeys-hook';
import { TranscriptionResult } from '@/types';
import { Transcription, apiService } from '@/services/api';

interface TranscriptionDisplayProps {
  transcription: Transcription;
}

const TranscriptionDisplay: React.FC<TranscriptionDisplayProps> = ({
  transcription
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedText, setEditedText] = useState(transcription.text);
  const [isExporting, setIsExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState<string>('markdown');
  const [showExportOptions, setShowExportOptions] = useState(false);

  // Keyboard shortcuts
  useHotkeys('ctrl+c', (e) => {
    e.preventDefault();
    handleCopy();
  });
  
  useHotkeys('ctrl+e', (e) => {
    e.preventDefault();
    setIsEditing(!isEditing);
  });
  
  useHotkeys('ctrl+s', (e) => {
    e.preventDefault();
    if (isEditing) {
      handleSaveEdit();
    } else {
      handleExport('markdown');
    }
  });
  
  useHotkeys('esc', (e) => {
    if (isEditing) {
      setIsEditing(false);
      setEditedText(transcription.text);
    }
    if (showExportOptions) {
      setShowExportOptions(false);
    }
  });

  const handleCopy = () => {
    navigator.clipboard.writeText(transcription.text);
    toast.success('📋 Transcription copied to clipboard');
  };

  const handleSaveEdit = () => {
    setIsEditing(false);
    toast.success('✏️ Transcription updated');
  };

  const handleExport = async (format: 'txt' | 'json' | 'srt' | 'markdown' | 'pdf') => {
    if (format === 'srt') {
      // Handle SRT locally for backwards compatibility
      const content = generateSRT();
      const blob = new Blob([content], { type: 'text/plain' });
      saveAs(blob, `${transcription.file_name}_transcript.srt`);
      toast.success('📁 Exported as SRT');
      return;
    }

    setIsExporting(true);
    try {
      // Use backend export API for comprehensive formatting
      const url = `${apiService.baseURL}/export/${transcription.id}?format=${format}&include_metadata=true&include_speaker_labels=true&include_summary=true`;
      
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`);
      }
      
      const blob = await response.blob();
      const filename = response.headers.get('content-disposition')?.split('filename=')[1]?.replace(/"/g, '') || 
        `${transcription.file_name}_transcript.${format}`;
      
      saveAs(blob, filename);
      toast.success(`📁 Exported as ${format.toUpperCase()}`);
    } catch (error) {
      console.error('Export failed:', error);
      toast.error('❌ Export failed. Please try again.');
      
      // Fallback to local export
      const content = format === 'json' ? 
        JSON.stringify(transcription, null, 2) : 
        transcription.text;
      const blob = new Blob([content], { type: format === 'json' ? 'application/json' : 'text/plain' });
      saveAs(blob, `${transcription.file_name}_transcript.${format}`);
      toast.success('📁 Exported with basic formatting');
    } finally {
      setIsExporting(false);
    }
  };
  
  const handleQuickExport = () => {
    setShowExportOptions(!showExportOptions);
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
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleCopy}
              aria-label="Copy transcription text (Ctrl+C)"
            >
              <Copy className="w-4 h-4 mr-2" />
              Copy
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setIsEditing(!isEditing)}
              aria-label={isEditing ? 'Save changes (Ctrl+S)' : 'Edit transcription (Ctrl+E)'}
            >
              {isEditing ? <Save className="w-4 h-4 mr-2" /> : <Edit className="w-4 h-4 mr-2" />}
              {isEditing ? 'Save' : 'Edit'}
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleQuickExport}
              aria-label="Show export options"
            >
              <FileDown className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
          
          {/* Keyboard shortcut hints */}
          <div className="text-xs text-muted-foreground space-x-4">
            <span>Ctrl+C: Copy</span>
            <span>Ctrl+E: Edit</span>
            <span>Ctrl+S: {isEditing ? 'Save' : 'Export'}</span>
            <span>Esc: Cancel</span>
          </div>
          
          {/* Export options */}
          {showExportOptions && (
            <div className="border border-border rounded-lg p-4 bg-muted/30">
              <h4 className="font-medium text-sm mb-3">Export Options</h4>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => handleExport('markdown')}
                  disabled={isExporting}
                  aria-label="Export as Markdown with metadata"
                >
                  {isExporting ? (
                    <div className="animate-spin h-3 w-3 border-t border-current rounded-full mr-2" />
                  ) : (
                    <FileType className="w-4 h-4 mr-2" />
                  )}
                  Markdown
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => handleExport('pdf')}
                  disabled={isExporting}
                  aria-label="Export as PDF document"
                >
                  {isExporting ? (
                    <div className="animate-spin h-3 w-3 border-t border-current rounded-full mr-2" />
                  ) : (
                    <FileDown className="w-4 h-4 mr-2" />
                  )}
                  PDF
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => handleExport('json')}
                  disabled={isExporting}
                  aria-label="Export as JSON with full data"
                >
                  {isExporting ? (
                    <div className="animate-spin h-3 w-3 border-t border-current rounded-full mr-2" />
                  ) : (
                    <Hash className="w-4 h-4 mr-2" />
                  )}
                  JSON
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => handleExport('txt')}
                  disabled={isExporting}
                  aria-label="Export as plain text"
                >
                  {isExporting ? (
                    <div className="animate-spin h-3 w-3 border-t border-current rounded-full mr-2" />
                  ) : (
                    <FileText className="w-4 h-4 mr-2" />
                  )}
                  TXT
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => handleExport('srt')}
                  disabled={isExporting}
                  aria-label="Export as SRT subtitle file"
                >
                  {isExporting ? (
                    <div className="animate-spin h-3 w-3 border-t border-current rounded-full mr-2" />
                  ) : (
                    <Clock className="w-4 h-4 mr-2" />
                  )}
                  SRT
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-3">
                💡 Markdown and PDF include metadata, speaker labels, and summaries when available
              </p>
            </div>
          )}
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