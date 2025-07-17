import React, { useState, useEffect } from 'react';
import SplashScreen from '@/components/SplashScreen';
import Dashboard from '@/components/Dashboard';
import LiveMeeting from '@/components/LiveMeeting';
import ImportAudio from '@/components/ImportAudio';
import SavedTranscripts from '@/components/SavedTranscripts';
import RemindersNotes from '@/components/RemindersNotes';
import StudySpot from '@/components/StudySpot';
import DonateButton from '@/components/DonateButton';

const Index = () => {
  const [showSplash, setShowSplash] = useState(true);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnlineStatus = () => setIsOnline(navigator.onLine);

    window.addEventListener('online', handleOnlineStatus);
    window.addEventListener('offline', handleOnlineStatus);

    return () => {
      window.removeEventListener('online', handleOnlineStatus);
      window.removeEventListener('offline', handleOnlineStatus);
    };
  }, []);

  const handleSplashFinish = () => {
    setShowSplash(false);
  };

  const handleNavigate = (page: string) => {
    setCurrentPage(page);
  };

  const handleBack = () => {
    setCurrentPage('dashboard');
  };

  if (showSplash) {
    return <SplashScreen onFinish={handleSplashFinish} />;
  }

  return (
    <>
      <DonateButton />

      {(() => {
        switch (currentPage) {
          case 'live-meeting':
            return <LiveMeeting onBack={handleBack} isOnline={isOnline} />;
          case 'import-audio':
            return <ImportAudio onBack={handleBack} isOnline={isOnline} />;
          case 'transcripts':
            return <SavedTranscripts onBack={handleBack} />;
          case 'reminders':
            return <RemindersNotes onBack={handleBack} />;
          case 'studyspot':
            return <StudySpot onBack={handleBack} />;
          default:
            return <Dashboard onNavigate={handleNavigate} isOnline={isOnline} />;
        }
      })()}
    </>
  );
};

export default Index;
