import React, { useState } from 'react';
import { ArrowLeft, Plus, Bell, Edit, Trash2, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';

interface RemindersNotesProps {
  onBack: () => void;
}

interface Note {
  id: string;
  title: string;
  content: string;
  date: string;
  type: 'note' | 'reminder';
  priority: 'low' | 'medium' | 'high';
}

const RemindersNotes: React.FC<RemindersNotesProps> = ({ onBack }) => {
  const [isCreating, setIsCreating] = useState(false);
  const [newNote, setNewNote] = useState({ title: '', content: '', type: 'note' as 'note' | 'reminder' });
  
  // Mock data
  const [notes] = useState<Note[]>([
    {
      id: '1',
      title: 'Follow up with client',
      content: 'Need to send proposal by end of week',
      date: '2024-01-15',
      type: 'reminder',
      priority: 'high'
    },
    {
      id: '2',
      title: 'Meeting Notes - Budget Discussion',
      content: 'Key points from budget meeting: 1. Increase marketing spend 2. Reduce operational costs 3. Focus on ROI metrics',
      date: '2024-01-14',
      type: 'note',
      priority: 'medium'
    }
  ]);

  const handleCreateNote = () => {
    if (!newNote.title.trim()) return;
    
    // Implementation for creating note would go here
    console.log('Creating note:', newNote);
    setIsCreating(false);
    setNewNote({ title: '', content: '', type: 'note' });
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center">
            <Button
              variant="ghost"
              size="icon"
              onClick={onBack}
              className="mr-4"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-3xl font-bold">Reminders & Notes</h1>
              <p className="text-muted-foreground">Manage your meeting notes and reminders</p>
            </div>
          </div>
          
          <Button
            onClick={() => setIsCreating(true)}
            className="bg-orange-500 hover:bg-orange-600"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Note
          </Button>
        </div>

        {/* Create Note Form */}
        {isCreating && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Create New Note</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                placeholder="Note title..."
                value={newNote.title}
                onChange={(e) => setNewNote({ ...newNote, title: e.target.value })}
              />
              <Textarea
                placeholder="Note content..."
                value={newNote.content}
                onChange={(e) => setNewNote({ ...newNote, content: e.target.value })}
                rows={4}
              />
              <div className="flex items-center justify-between">
                <div className="flex space-x-2">
                  <Button
                    variant={newNote.type === 'note' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setNewNote({ ...newNote, type: 'note' })}
                  >
                    Note
                  </Button>
                  <Button
                    variant={newNote.type === 'reminder' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setNewNote({ ...newNote, type: 'reminder' })}
                  >
                    Reminder
                  </Button>
                </div>
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    onClick={() => setIsCreating(false)}
                  >
                    Cancel
                  </Button>
                  <Button onClick={handleCreateNote}>
                    Create
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Notes List */}
        <div className="space-y-4">
          {notes.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <Bell className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-lg font-medium mb-2">No notes or reminders</p>
                <p className="text-muted-foreground">
                  Create your first note to get started
                </p>
              </CardContent>
            </Card>
          ) : (
            notes.map((note) => (
              <Card key={note.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg mb-2">{note.title}</CardTitle>
                      <div className="flex items-center space-x-2">
                        <Badge variant={note.type === 'reminder' ? 'default' : 'secondary'}>
                          {note.type === 'reminder' ? (
                            <><Bell className="h-3 w-3 mr-1" />Reminder</>
                          ) : (
                            'Note'
                          )}
                        </Badge>
                        <Badge variant="outline" className={getPriorityColor(note.priority)}>
                          {note.priority}
                        </Badge>
                        <div className="flex items-center text-sm text-muted-foreground">
                          <Calendar className="h-4 w-4 mr-1" />
                          {note.date}
                        </div>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">{note.content}</p>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default RemindersNotes;