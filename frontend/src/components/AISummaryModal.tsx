import React from 'react';
import { X, Brain, Download, Copy } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';

interface AISummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  summary: string;
  title?: string;
}

const AISummaryModal: React.FC<AISummaryModalProps> = ({ 
  isOpen, 
  onClose, 
  summary, 
  title = "AI Summary" 
}) => {
  if (!isOpen) return null;

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(summary);
  };

  const handleDownload = () => {
    const blob = new Blob([summary], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ai-summary.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/50 z-50" onClick={onClose} />
      
      {/* Modal */}
      <div className="fixed inset-4 md:inset-8 lg:inset-16 z-50 flex items-center justify-center">
        <Card className="w-full h-full max-w-4xl max-h-full flex flex-col shadow-2xl">
          {/* Header */}
          <CardHeader className="flex-shrink-0 border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center text-xl">
                <Brain className="h-6 w-6 mr-3 text-primary" />
                {title}
              </CardTitle>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCopyToClipboard}
                  className="flex items-center gap-2"
                >
                  <Copy className="h-4 w-4" />
                  Copy
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleDownload}
                  className="flex items-center gap-2"
                >
                  <Download className="h-4 w-4" />
                  Download
                </Button>
                <Separator orientation="vertical" className="h-6" />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          
          {/* Content */}
          <CardContent className="flex-1 overflow-hidden p-0">
            <ScrollArea className="h-full">
              <div className="p-6">
                <div className="prose prose-sm max-w-none">
                  <p className="text-foreground leading-loose whitespace-pre-wrap">
                    {summary}
                  </p>
                </div>
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </>
  );
};

export default AISummaryModal;