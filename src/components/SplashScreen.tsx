import React, { useEffect, useState } from 'react';

interface SplashScreenProps {
  onFinish: () => void;
}

const SplashScreen: React.FC<SplashScreenProps> = ({ onFinish }) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      // Wait for fade out animation to complete before calling onFinish
      setTimeout(onFinish, 500);
    }, 3000);

    return () => clearTimeout(timer);
  }, [onFinish]);

  return (
    <div className={`fixed inset-0 h-screen w-screen bg-slate-900 z-50 flex items-center justify-center transition-opacity duration-500 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
      <div className="text-center">
        <div className="animate-bounce mb-6">
          <h1 className="text-6xl md:text-8xl font-semibold tracking-wide font-sans lowercase animate-pulse"
              style={{
                color: '#3b82f6',  // Lighter blue shade
                fontFamily: '"Poppins", "Sora", system-ui, -apple-system, sans-serif',
                textShadow: '0 0 20px rgba(59, 130, 246, 0.4), 0 4px 8px rgba(0, 0, 0, 0.3)',
                filter: 'drop-shadow(0 0 15px rgba(59, 130, 246, 0.3))'
              }}>
            verba
          </h1>
        </div>
        <p className="text-lg md:text-xl text-gray-300 mt-4">
          AI-Powered Meeting Transcription
        </p>
      </div>
    </div>
  );
};

export default SplashScreen;