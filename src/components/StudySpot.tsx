import React, { useState } from 'react';
import { ArrowLeft, BookOpen, Brain, MessageSquare, Lightbulb, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';

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
  const [selectedTranscript, setSelectedTranscript] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [studySession, setStudySession] = useState<StudySession | null>(null);
  
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
            <h1 className="text-3xl font-bold">StudySpot</h1>
            <p className="text-muted-foreground">AI-powered study assistant for your transcripts</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Input */}
          <div className="space-y-6">
            {/* Transcript Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BookOpen className="h-5 w-5 mr-2" />
                  Select Transcript
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  {availableTranscripts.map((transcript) => (
                    <div
                      key={transcript}
                      className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                        selectedTranscript === transcript
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:bg-accent/50'
                      }`}
                      onClick={() => setSelectedTranscript(transcript)}
                    >
                      {transcript}
                    </div>
                  ))}
                </div>
                
                <Button
                  onClick={handleAnalyze}
                  disabled={!selectedTranscript || isAnalyzing}
                  className="w-full bg-cyan-500 hover:bg-cyan-600"
                >
                  <Brain className="h-4 w-4 mr-2" />
                  {isAnalyzing ? 'Analyzing...' : 'Analyze with AI'}
                </Button>
              </CardContent>
            </Card>

            {/* Custom Question */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <MessageSquare className="h-5 w-5 mr-2" />
                  Ask a Question
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  placeholder="Ask anything about your transcript..."
                  rows={3}
                />
                <Button variant="outline" className="w-full">
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
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Brain className="h-5 w-5 mr-2" />
                      AI Summary
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground leading-relaxed">
                      {studySession.summary}
                    </p>
                  </CardContent>
                </Card>

                {/* Key Points */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Lightbulb className="h-5 w-5 mr-2" />
                      Key Points
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {studySession.keyPoints.map((point, index) => (
                        <li key={index} className="flex items-start">
                          <Badge variant="outline" className="mr-2 mt-0.5 text-xs">
                            {index + 1}
                          </Badge>
                          <span className="text-sm">{point}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>

                {/* Study Questions */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <MessageSquare className="h-5 w-5 mr-2" />
                      Study Questions
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {studySession.questions.map((question, index) => (
                        <div
                          key={index}
                          className="p-3 bg-accent/30 rounded-lg cursor-pointer hover:bg-accent/50 transition-colors"
                        >
                          <p className="text-sm font-medium">{question}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card>
                <CardContent className="p-8 text-center">
                  <Brain className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-lg font-medium mb-2">Ready to Study</p>
                  <p className="text-muted-foreground">
                    Select a transcript and let AI help you understand and learn from your meetings
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StudySpot;