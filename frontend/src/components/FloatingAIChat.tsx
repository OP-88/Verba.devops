import React, { useState } from 'react';
import { MessageCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import AIChatArea from './AIChatArea';
import AIChatSidebar from './AIChatSidebar';

const FloatingAIChat: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [showChatSidebar, setShowChatSidebar] = useState(false);

  const handleSelectChat = (chatId: string) => {
    console.log('Selected chat:', chatId);
    setShowChatSidebar(false);
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <Button
          onClick={() => setIsOpen(true)}
          size="lg"
          className="rounded-full pl-4 pr-6 h-14 bg-primary hover:bg-primary/90 shadow-lg hover:shadow-xl transition-all duration-200 flex items-center gap-3"
        >
          <MessageCircle className="h-5 w-5" />
          <span className="text-sm font-medium">AI Assistant</span>
        </Button>
      </div>
    );
  }

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/20 z-40" onClick={() => setIsOpen(false)} />
      
      {/* Chat Container */}
      <div className="fixed bottom-6 right-6 z-50 w-96 h-[600px]">
        <Card className="h-full flex flex-col shadow-2xl">
          {/* Header */}
          <div className="flex items-center justify-between p-3 border-b">
            <h3 className="font-semibold text-sm">AI Assistant</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsOpen(false)}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
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

export default FloatingAIChat;