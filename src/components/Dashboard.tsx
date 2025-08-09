import React from 'react';
import { Mic, Upload, FileText, Bell, BookOpen, Wifi, WifiOff } from 'lucide-react';
import DashboardCard from './DashboardCard';
import { ThemeToggle } from './ThemeToggle';
import DeviceFirstMessage from './DeviceFirstMessage';
import ProfileButton from './ProfileButton';

interface DashboardProps {
  onNavigate: (page: string) => void;
  isOnline: boolean;
}

const Dashboard: React.FC<DashboardProps> = ({ onNavigate, isOnline }) => {
  const cards = [
    {
      title: 'Live Meeting',
      description: 'Start recording and transcribing in real-time',
      icon: Mic,
      color: 'bg-gradient-to-br from-green-500 to-green-600',
      action: () => onNavigate('live-meeting')
    },
    {
      title: 'Import Audio',
      description: 'Upload audio files for transcription',
      icon: Upload,
      color: 'bg-gradient-to-br from-blue-500 to-blue-600',
      action: () => onNavigate('import-audio')
    },
    {
      title: 'StudySpot',
      description: 'AI-powered study assistant for your transcripts',
      icon: BookOpen,
      color: 'bg-gradient-to-br from-cyan-500 to-cyan-600',
      action: () => onNavigate('studyspot')
    },
    {
      title: 'Saved Transcripts',
      description: 'View and manage your transcriptions',
      icon: FileText,
      color: 'bg-gradient-to-br from-purple-500 to-purple-600',
      action: () => onNavigate('transcripts')
    },
    {
      title: 'Reminders & Notes',
      description: 'Manage your meeting notes and reminders',
      icon: Bell,
      color: 'bg-gradient-to-br from-orange-500 to-orange-600',
      action: () => onNavigate('reminders')
    }
  ];

  const handleCardKeyDown = (event: React.KeyboardEvent, action: () => void) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      action();
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold text-primary mb-2 font-sans lowercase">verba</h1>
            <p className="text-muted-foreground">AI-Powered Meeting Transcription</p>
          </div>
          
          <div className="flex items-center space-x-3">
            {/* Online/Offline Status */}
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-muted/50 border border-border/50">
              {isOnline ? (
                <Wifi className="w-4 h-4 text-green-500" />
              ) : (
                <WifiOff className="w-4 h-4 text-red-500" />
              )}
              <span className="text-xs font-medium text-muted-foreground">
                {isOnline ? 'Online' : 'Offline'}
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              <ProfileButton />
              <ThemeToggle />
            </div>
          </div>
        </div>


        {/* Main Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {cards.map((card) => (
            <DashboardCard
              key={card.title}
              title={card.title}
              description={card.description}
              icon={card.icon}
              color={card.color}
              onClick={card.action}
              onKeyDown={(event) => handleCardKeyDown(event, card.action)}
            />
          ))}
        </div>

        {/* Device First Message - moved to bottom */}
        <DeviceFirstMessage />
      </div>
    </div>
  );
};

export default Dashboard;