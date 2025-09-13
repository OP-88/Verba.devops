import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Search, Trash2, Calendar, Clock, FileText } from 'lucide-react';
import { TranscriptionResult } from '@/types';
import { apiService } from '@/services/api';
import { toast } from 'sonner';

interface TranscriptionHistoryProps {
  onSelectTranscription: (transcription: TranscriptionResult) => void;
}

export default function TranscriptionHistory({ onSelectTranscription }: TranscriptionHistoryProps) {
  const [transcriptions, setTranscriptions] = useState<TranscriptionResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [deleting, setDeleting] = useState<number | null>(null);

  useEffect(() => {
    loadTranscriptions();
  }, []);

  const loadTranscriptions = async () => {
    try {
      setLoading(true);
      const data = await apiService.getHistory();
      setTranscriptions(data);
    } catch (error) {
      toast.error('Failed to load transcriptions');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      setDeleting(id);
      await apiService.deleteTranscription(id);
      setTranscriptions(prev => prev.filter(t => t.id !== id));
      toast.success('Transcription deleted');
    } catch (error) {
      toast.error('Failed to delete transcription');
    } finally {
      setDeleting(null);
    }
  };

  const filteredTranscriptions = transcriptions.filter(t =>
    t.text.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.file_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
        <Input
          placeholder="Search transcriptions..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Stats */}
      <div className="flex gap-4">
        <Badge variant="outline" className="text-sm">
          <FileText className="w-3 h-3 mr-1" />
          {transcriptions.length} transcriptions
        </Badge>
        <Badge variant="outline" className="text-sm">
          <Clock className="w-3 h-3 mr-1" />
          {Math.round(transcriptions.reduce((acc, t) => acc + t.duration, 0) / 60)} min total
        </Badge>
      </div>

      {/* Transcription List */}
      <div className="space-y-4">
        {filteredTranscriptions.length === 0 ? (
          <Card className="p-8 text-center">
            <div className="text-gray-500">
              {searchTerm ? 'No transcriptions match your search' : 'No transcriptions found'}
            </div>
          </Card>
        ) : (
          filteredTranscriptions.map((transcription) => (
            <Card
              key={transcription.id}
              className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              onClick={() => onSelectTranscription(transcription)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-base font-medium truncate">
                      {transcription.file_name}
                    </CardTitle>
                    <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {formatDate(transcription.created_at)}
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatDuration(transcription.duration)}
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {transcription.language}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {Math.round(transcription.confidence * 100)}% confidence
                      </Badge>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(transcription.id);
                    }}
                    disabled={deleting === transcription.id}
                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-sm text-gray-600 dark:text-gray-300 line-clamp-3">
                  {transcription.text}
                </p>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}