import React, { useState, useEffect } from 'react';
import SplashScreen from '@/components/SplashScreen';
import Dashboard from '@/components/Dashboard';
import LiveMeeting from '@/components/LiveMeeting';
import ImportAudio from '@/components/ImportAudio';
import SavedTranscripts from '@/components/SavedTranscripts';
import RemindersNotes from '@/components/RemindersNotes';
import StudySpot from '@/components/StudySpot';
import DonateButton from '@/components/DonateButton';
import FloatingAIChat from '@/components/FloatingAIChat';
import VerbaTestSuite from '@/components/VerbaTestSuite';

const Index = () => {
  const [showSplash, setShowSplash] = useState(false); // Skip splash for immediate preview
  const [currentPage, setCurrentPage] = useState('test-suite'); // Start with test suite
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
      {/* Force display test suite for immediate preview */}
      <VerbaTestSuite />
    </>
  );
};

export default Index;
