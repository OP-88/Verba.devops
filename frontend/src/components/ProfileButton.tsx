import React, { useState } from 'react';
import { User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import ProfileModal from './ProfileModal';

const ProfileButton: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleProfileClick = () => {
    setIsModalOpen(true);
  };

  return (
    <>
      <Button
        onClick={handleProfileClick}
        variant="outline"
        size="icon"
        className="rounded-full w-10 h-10"
      >
        <User className="h-4 w-4" />
        <span className="sr-only">Profile</span>
      </Button>
      
      <ProfileModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
      />
    </>
  );
};

export default ProfileButton;