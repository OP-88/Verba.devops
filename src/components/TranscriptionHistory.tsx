// ~/verba-frontend-ts/src/components/TranscriptionHistory.tsx
// Fixed to handle session_id requirement

import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { TranscriptionHistoryItem } from '../types/api';

interface TranscriptionHistoryProps {
  refreshTrigger: number;
}

export const TranscriptionHistory: React.FC<TranscriptionHistoryProps> = ({ refreshTrigger }) => {
  const [transcriptions, setTranscriptions] = useState<TranscriptionHistoryItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTranscriptions = async () => {
    setLoading(true);
    setError(null);
    try {
      // Pass default session_id to fix 422 error
      const data = await apiService.getTranscriptions('default');
      setTranscriptions(data);
    } catch (err) {
      setError('Failed to load transcriptions');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTranscriptions();
  }, [refreshTrigger]);

  const handleRefresh = () => {
    fetchTranscriptions();
  };

  if (loading) {
    return <div className="text-center">Loading transcriptions...</div>;
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
        {error}
        <button 
          onClick={handleRefresh}
          className="ml-2 underline hover:no-underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="mt-8">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-white flex items-center">
          📝 Transcriptions ({transcriptions.length})
        </h2>
        <button
          onClick={handleRefresh}
          className="bg-gray-700 text-white px-3 py-1 rounded text-sm hover:bg-gray-600"
        >
          🔄 Refresh
        </button>
      </div>

      {transcriptions.length === 0 ? (
        <p className="text-gray-400 text-center py-8">
          No transcriptions yet. Upload an audio file to get started!
        </p>
      ) : (
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {transcriptions.map((item) => (
            <div 
              key={item.id} 
              className="bg-white/10 backdrop-blur rounded-lg p-4 border border-white/20"
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-medium text-white">
                  {item.filename || 'Unknown file'}
                </h3>
                <span className="text-xs text-gray-300">
                  {new Date(item.created_at).toLocaleString()}
                </span>
              </div>
              
              {/* Enhanced metadata display */}
              <div className="flex gap-4 text-xs text-gray-300 mb-2">
                {item.content_type && (
                  <span className="bg-blue-500/20 px-2 py-1 rounded">
                    {item.content_type}
                  </span>
                )}
                {item.model_used && (
                  <span className="bg-green-500/20 px-2 py-1 rounded">
                    Model: {item.model_used}
                  </span>
                )}
                {item.processing_time && (
                  <span className="bg-purple-500/20 px-2 py-1 rounded">
                    {item.processing_time.toFixed(1)}s
                  </span>
                )}
                {item.audio_duration && (
                  <span className="bg-orange-500/20 px-2 py-1 rounded">
                    {item.audio_duration.toFixed(1)}s audio
                  </span>
                )}
              </div>
              
              <p className="text-gray-200 text-sm line-clamp-3">
                {item.transcription || 'No transcription available'}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
