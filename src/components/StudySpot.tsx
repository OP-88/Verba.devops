import React, { useState } from 'react';
import { ArrowLeft, BookOpen, Brain, MessageSquare, Lightbulb, Search, GraduationCap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import AISummaryModal from './AISummaryModal';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import ExpandableAIChat from './ExpandableAIChat';
import StudyProfileButton from './StudyProfileButton';

interface StudySpotProps {
  onBack: () => void;
}

interface StudySession {
  id: string;
  transcript: string;
  summary: string;
  keyPoints: string[];
  questions: string[];
}

const StudySpot: React.FC<StudySpotProps> = ({ onBack }) => {
  const [showSummaryModal, setShowSummaryModal] = useState(false);
  const [selectedTranscript, setSelectedTranscript] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [studySession, setStudySession] = useState<StudySession | null>(null);
  const [customQuestion, setCustomQuestion] = useState('');
  
  // Mock transcripts
  const availableTranscripts = [
    'Team Meeting - Project Alpha',
    'Training Session - New Features',
    'Client Call - Budget Review'
  ];

  const handleAnalyze = () => {
    if (!selectedTranscript) return;
    
    setIsAnalyzing(true);
    
    // Simulate AI analysis
    setTimeout(() => {
      setStudySession({
        id: '1',
        transcript: selectedTranscript,
        summary: 'This meeting covered project milestones, resource allocation, and timeline adjustments. Key decisions were made regarding budget reallocation and team responsibilities.',
        keyPoints: [
          'Project deadline moved to end of Q2',
          'Budget increased by 15% for additional resources',
          'New team member to be hired for backend development',
          'Weekly check-ins scheduled every Tuesday'
        ],
        questions: [
          'What are the main deliverables for Q2?',
          'How will the budget increase affect other projects?',
          'What skills should the new team member have?',
          'Who will lead the weekly check-ins?'
        ]
      });
      setIsAnalyzing(false);
    }, 2000);
  };

  const handleAskQuestion = () => {
    if (!customQuestion.trim()) return;
    console.log('Asking question:', customQuestion);
    // Here you would implement the AI question functionality
    setCustomQuestion('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/20">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center">
            <Button
              variant="ghost"
              size="icon"
              onClick={onBack}
              className="mr-4 hover:bg-accent/50"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <GraduationCap className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">StudySpot</h1>
                <p className="text-sm text-muted-foreground">AI-powered learning assistant</p>
              </div>
            </div>
          </div>
          <StudyProfileButton />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Input */}
          <div className="space-y-6">
            {/* Transcript Selection */}
            <Card className="border-border/20 shadow-sm">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center text-lg font-semibold">
                  <BookOpen className="h-5 w-5 mr-3 text-primary" />
                  Select Transcript
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  {availableTranscripts.map((transcript) => (
                    <div
                      key={transcript}
                      className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 ${
                        selectedTranscript === transcript
                          ? 'border-primary bg-primary/5 shadow-sm'
                          : 'border-border/30 hover:bg-accent/30 hover:border-border/50'
                      }`}
                      onClick={() => setSelectedTranscript(transcript)}
                    >
                      <span className="font-medium text-foreground">{transcript}</span>
                    </div>
                  ))}
                </div>
                
                <Button
                  onClick={handleAnalyze}
                  disabled={!selectedTranscript || isAnalyzing}
                  className="w-full h-11 bg-primary hover:bg-primary/90 text-primary-foreground font-medium"
                >
                  <Brain className="h-4 w-4 mr-2" />
                  {isAnalyzing ? 'Analyzing...' : 'Analyze with AI'}
                </Button>
              </CardContent>
            </Card>

            {/* Custom Question */}
            <Card className="border-border/20 shadow-sm">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center text-lg font-semibold">
                  <MessageSquare className="h-5 w-5 mr-3 text-primary" />
                  Ask a Question
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  placeholder="Ask anything about your transcript..."
                  rows={4}
                  value={customQuestion}
                  onChange={(e) => setCustomQuestion(e.target.value)}
                  className="resize-none border-border/30 focus:border-primary/50 bg-background"
                />
                <Button 
                  onClick={handleAskQuestion}
                  disabled={!customQuestion.trim()}
                  variant="outline" 
                  className="w-full h-11 border-border/30 hover:bg-accent/50"
                >
                  <Search className="h-4 w-4 mr-2" />
                  Ask AI
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Results */}
          <div className="space-y-6">
            {studySession ? (
              <>
                {/* Summary */}
                <Card className="border-border/20 shadow-sm cursor-pointer hover:shadow-md transition-all duration-200" onClick={() => setShowSummaryModal(true)}>
                  <CardHeader className="pb-4">
                    <CardTitle className="flex items-center text-lg font-semibold">
                      <Brain className="h-5 w-5 mr-3 text-primary" />
                      AI Summary
                      <span className="ml-auto text-xs text-muted-foreground bg-accent/50 px-2 py-1 rounded-full">
                        Click to expand
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground leading-relaxed line-clamp-4">
                      {studySession.summary}
                    </p>
                  </CardContent>
                </Card>

                {/* Key Points */}
                <Card className="border-border/20 shadow-sm">
                  <CardHeader className="pb-4">
                    <CardTitle className="flex items-center text-lg font-semibold">
                      <Lightbulb className="h-5 w-5 mr-3 text-primary" />
                      Key Points
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-3">
                      {studySession.keyPoints.map((point, index) => (
                        <li key={index} className="flex items-start gap-3">
                          <Badge variant="secondary" className="min-w-6 h-6 text-xs font-medium flex items-center justify-center">
                            {index + 1}
                          </Badge>
                          <span className="text-sm leading-relaxed text-foreground">{point}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                {/* Study Questions */}
                <Card className="border-border/20 shadow-sm">
                  <CardHeader className="pb-4">
                    <CardTitle className="flex items-center text-lg font-semibold">
                      <MessageSquare className="h-5 w-5 mr-3 text-primary" />
                      Study Questions
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {studySession.questions.map((question, index) => (
                        <div
                          key={index}
                          className="p-4 bg-accent/20 border border-border/20 rounded-xl cursor-pointer hover:bg-accent/30 hover:border-border/30 transition-all duration-200"
                        >
                          <p className="text-sm font-medium text-foreground leading-relaxed">{question}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="border-border/20 shadow-sm">
                <CardContent className="p-12 text-center">
                  <div className="p-4 bg-primary/10 rounded-full w-fit mx-auto mb-6">
                    <Brain className="h-12 w-12 text-primary" />
                  </div>
                  <h3 className="text-xl font-semibold mb-3 text-foreground">Ready to Learn</h3>
                  <p className="text-muted-foreground leading-relaxed max-w-sm mx-auto">
                    Select a transcript and let AI help you understand and learn from your content
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
      
      {/* AI Summary Modal */}
      <AISummaryModal
        isOpen={showSummaryModal}
        onClose={() => setShowSummaryModal(false)}
        summary={studySession?.summary || ''}
        title="AI Summary"
      />
      
      {/* Expandable AI Chat */}
      <ExpandableAIChat />
    </div>
  );
};

export default StudySpot;