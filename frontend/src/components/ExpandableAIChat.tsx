import React, { useState } from 'react';
import { MessageCircle, X, Maximize2, Minimize2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import AIChatArea from './AIChatArea';
import AIChatSidebar from './AIChatSidebar';

const ExpandableAIChat: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showChatSidebar, setShowChatSidebar] = useState(false);

  const handleSelectChat = (chatId: string) => {
    console.log('Selected chat:', chatId);
    setShowChatSidebar(false);
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-8 right-8 z-50">
        <Button
          onClick={() => setIsOpen(true)}
          size="lg"
          className="rounded-full pl-4 pr-6 h-12 bg-primary hover:bg-primary/90 shadow-lg hover:shadow-xl transition-all duration-300 flex items-center gap-2"
        >
          <MessageCircle className="h-5 w-5" />
          <span className="text-sm font-medium">AI Assistant</span>
        </Button>
      </div>
    );
  }

  return (
    <>
      {/* Backdrop */}
      {isExpanded && (
        <div className="fixed inset-0 bg-black/10 z-40" onClick={() => setIsExpanded(false)} />
      )}
      
      {/* Chat Container */}
      <div className={`fixed z-50 transition-all duration-300 ${
        isExpanded 
          ? 'inset-8 lg:inset-16' 
          : 'bottom-8 right-8 w-96 h-[500px]'
      }`}>
        <Card className="h-full flex flex-col shadow-2xl border-border/20 bg-background/95 backdrop-blur-sm">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border/10">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
              <h3 className="font-medium text-foreground">AI Assistant</h3>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(!isExpanded)}
                className="h-8 w-8 p-0 hover:bg-accent/50"
              >
                {isExpanded ? (
                  <Minimize2 className="h-4 w-4" />
                ) : (
                  <Maximize2 className="h-4 w-4" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsOpen(false)}
                className="h-8 w-8 p-0 hover:bg-accent/50"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          {/* Chat Area */}
          <div className="flex-1 overflow-hidden">
            <AIChatArea onShowSidebar={() => setShowChatSidebar(true)} />
          </div>
        </Card>
      </div>

      {/* AI Chat Sidebar */}
      <AIChatSidebar 
        isOpen={showChatSidebar}
        onClose={() => setShowChatSidebar(false)}
        onSelectChat={handleSelectChat}
      />
    </>
  );
};

export default ExpandableAIChat;