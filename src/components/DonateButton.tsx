import React from 'react';
import { Heart } from 'lucide-react';
import { Button } from '@/components/ui/button';

const DonateButton: React.FC = () => {
  const handleDonateClick = () => {
    // Implementation for donation functionality would go here
    console.log('Donate clicked');
  };

  return (
    <div className="fixed bottom-6 right-6 z-40">
      <Button
        onClick={handleDonateClick}
        className="rounded-full bg-gradient-to-r from-pink-500 to-red-500 hover:from-pink-600 hover:to-red-600 text-white shadow-lg"
        size="lg"
      >
        <Heart className="h-5 w-5 mr-2" />
        Donate
      </Button>
    </div>
  );
};

export default DonateButton;