import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, History } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: string;
}

interface AIChatAreaProps {
  onShowSidebar: () => void;
}

const AIChatArea: React.FC<AIChatAreaProps> = ({ onShowSidebar }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'ai',
      content: 'Hello! I\'m your AI assistant. I can help you analyze your transcripts, answer questions, and provide insights. How can I help you today?',
      timestamp: new Date().toLocaleTimeString()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

    const newUserMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, newUserMessage]);
    setInputMessage('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: 'I understand your question. Based on the transcript analysis, here are my insights: ' + inputMessage.substring(0, 100) + '... This is a simulated response for demonstration purposes.',
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, aiResponse]);
      setIsTyping(false);
    }, 1500);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  useEffect(() => {
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  }, [messages]);

  return (
    <div className="h-full flex flex-col">
      {/* Fixed Header */}
      <div className="sticky top-0 z-10 bg-card border-b border-border px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center text-lg font-semibold">
            <Bot className="h-5 w-5 mr-2 text-primary" />
            AI Assistant
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={onShowSidebar}
            className="flex items-center gap-2 bg-background hover:bg-accent"
          >
            <History className="h-4 w-4" />
            Past Chats
          </Button>
        </div>
      </div>
      
      {/* Scrollable Messages Area */}
      <div className="flex-1 flex flex-col min-h-0">
        <ScrollArea ref={scrollAreaRef} className="flex-1 px-6 py-4">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] p-3 rounded-lg ${
                    message.type === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-accent text-accent-foreground'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {message.type === 'ai' && (
                      <Bot className="h-4 w-4 mt-0.5 text-primary" />
                    )}
                    {message.type === 'user' && (
                      <User className="h-4 w-4 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className="text-sm">{message.content}</p>
                      <span className="text-xs opacity-70 mt-1 block">
                        {message.timestamp}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-accent text-accent-foreground p-3 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Bot className="h-4 w-4 text-primary" />
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-primary rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-100"></div>
                      <div className="w-2 h-2 bg-primary rounded-full animate-pulse delay-200"></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
        
        {/* Fixed Input Area */}
        <div className="sticky bottom-0 bg-card border-t border-border px-6 py-4 shadow-sm">
          <div className="flex gap-2">
            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me anything about your transcripts..."
              className="flex-1"
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isTyping}
              size="icon"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIChatArea;