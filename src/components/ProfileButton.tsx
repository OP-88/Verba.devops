import React from 'react';
import { User } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ProfileButtonProps {
  isVisible: boolean;
}

const ProfileButton: React.FC<ProfileButtonProps> = ({ isVisible }) => {
  const handleProfileClick = () => {
    // Implementation for profile functionality would go here
    console.log('Profile clicked');
  };

  if (!isVisible) return null;

  return (
    <div className="fixed top-6 right-6 z-40">
      <Button
        onClick={handleProfileClick}
        variant="outline"
        size="icon"
        className="rounded-full w-12 h-12 bg-background/80 backdrop-blur-sm border-border/50 hover:bg-accent/50"
      >
        <User className="h-5 w-5" />
        <span className="sr-only">Profile</span>
      </Button>
    </div>
  );
};

export default ProfileButton;