import React, { useState } from 'react';
import { ArrowLeft, Search, FileText, Calendar, Clock, Download, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

interface SavedTranscriptsProps {
  onBack: () => void;
}

interface Transcript {
  id: string;
  title: string;
  date: string;
  duration: string;
  type: 'live' | 'imported';
  content: string;
}

const SavedTranscripts: React.FC<SavedTranscriptsProps> = ({ onBack }) => {
  const [searchTerm, setSearchTerm] = useState('');
  
  // Mock data - in real app this would come from storage/API
  const [transcripts] = useState<Transcript[]>([
    {
      id: '1',
      title: 'Team Meeting - Project Alpha',
      date: '2024-01-15',
      duration: '45:30',
      type: 'live',
      content: 'Discussion about project milestones and deliverables...'
    },
    {
      id: '2',
      title: 'Client Call - Budget Review',
      date: '2024-01-14',
      duration: '32:15',
      type: 'imported',
      content: 'Review of quarterly budget and resource allocation...'
    },
    {
      id: '3',
      title: 'Training Session - New Features',
      date: '2024-01-12',
      duration: '1:15:20',
      type: 'live',
      content: 'Comprehensive overview of new product features...'
    }
  ]);

  const filteredTranscripts = transcripts.filter(transcript =>
    transcript.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    transcript.content.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDownload = (transcript: Transcript) => {
    // Implementation for downloading transcript
    console.log('Downloading transcript:', transcript.id);
  };

  const handleDelete = (transcriptId: string) => {
    // Implementation for deleting transcript
    console.log('Deleting transcript:', transcriptId);
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto">
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
            <h1 className="text-3xl font-bold">Saved Transcripts</h1>
            <p className="text-muted-foreground">Manage your meeting transcriptions</p>
          </div>
        </div>

        {/* Search */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search transcripts..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </CardContent>
        </Card>

        {/* Transcripts List */}
        <div className="space-y-4">
          {filteredTranscripts.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <FileText className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-lg font-medium mb-2">No transcripts found</p>
                <p className="text-muted-foreground">
                  {searchTerm ? 'Try adjusting your search terms' : 'Start recording meetings to see transcripts here'}
                </p>
              </CardContent>
            </Card>
          ) : (
            filteredTranscripts.map((transcript) => (
              <Card key={transcript.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-xl mb-2">{transcript.title}</CardTitle>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <div className="flex items-center">
                          <Calendar className="h-4 w-4 mr-1" />
                          {transcript.date}
                        </div>
                        <div className="flex items-center">
                          <Clock className="h-4 w-4 mr-1" />
                          {transcript.duration}
                        </div>
                        <Badge variant={transcript.type === 'live' ? 'default' : 'secondary'}>
                          {transcript.type === 'live' ? 'Live Recording' : 'Imported Audio'}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownload(transcript)}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(transcript.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground line-clamp-2">
                    {transcript.content}
                  </p>
                  <Button variant="link" className="mt-2 p-0 h-auto text-primary">
                    View full transcript →
                  </Button>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default SavedTranscripts;