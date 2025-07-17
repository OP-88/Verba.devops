import React from 'react';
import { X, MessageSquare, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

interface ChatSession {
  id: string;
  title: string;
  timestamp: string;
  preview: string;
}

interface AIChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectChat: (chatId: string) => void;
}

const AIChatSidebar: React.FC<AIChatSidebarProps> = ({ 
  isOpen, 
  onClose, 
  onSelectChat 
}) => {
  // Mock past chats data
  const pastChats: ChatSession[] = [
    {
      id: '1',
      title: 'Project Alpha Discussion',
      timestamp: '2 hours ago',
      preview: 'What are the key deliverables mentioned in the meeting?'
    },
    {
      id: '2',
      title: 'Budget Review Analysis',
      timestamp: '1 day ago',
      preview: 'Can you summarize the budget allocation decisions?'
    },
    {
      id: '3',
      title: 'Training Session Notes',
      timestamp: '3 days ago',
      preview: 'What were the main topics covered in the training?'
    }
  ];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-80 bg-background border-l border-border shadow-lg">
      <div className="flex items-center justify-between p-4 border-b border-border">
        <h2 className="text-lg font-semibold">Past AI Chats</h2>
        <Button variant="ghost" size="icon" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>
      
      <ScrollArea className="h-[calc(100vh-80px)]">
        <div className="p-4 space-y-3">
          {pastChats.map((chat) => (
            <Card 
              key={chat.id} 
              className="cursor-pointer hover:bg-accent/50 transition-colors"
              onClick={() => onSelectChat(chat.id)}
            >
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <CardTitle className="text-sm font-medium line-clamp-1">
                    {chat.title}
                  </CardTitle>
                  <MessageSquare className="h-4 w-4 text-muted-foreground mt-0.5" />
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                  {chat.preview}
                </p>
                <div className="flex items-center text-xs text-muted-foreground">
                  <Clock className="h-3 w-3 mr-1" />
                  {chat.timestamp}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};

export default AIChatSidebar;