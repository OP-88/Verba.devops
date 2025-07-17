import React from 'react';
import { User, Settings, LogOut, Bell, Shield, HelpCircle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ProfileModal: React.FC<ProfileModalProps> = ({ isOpen, onClose }) => {
  const handleAction = (action: string) => {
    console.log(`Profile action: ${action}`);
    // Here you would implement the actual functionality for each action
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Profile</DialogTitle>
          <DialogDescription>
            Manage your account settings and preferences
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* User Info */}
          <div className="flex items-center space-x-4 p-4 bg-accent/50 rounded-lg">
            <Avatar className="h-12 w-12">
              <AvatarImage src="/placeholder-avatar.jpg" alt="User Avatar" />
              <AvatarFallback>
                <User className="h-6 w-6" />
              </AvatarFallback>
            </Avatar>
            <div>
              <h3 className="font-medium">John Doe</h3>
              <p className="text-sm text-muted-foreground">john.doe@example.com</p>
            </div>
          </div>

          <Separator />

          {/* Actions */}
          <div className="space-y-2">
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={() => handleAction('settings')}
            >
              <Settings className="h-4 w-4 mr-3" />
              Account Settings
            </Button>
            
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={() => handleAction('notifications')}
            >
              <Bell className="h-4 w-4 mr-3" />
              Notifications
            </Button>
            
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={() => handleAction('privacy')}
            >
              <Shield className="h-4 w-4 mr-3" />
              Privacy & Security
            </Button>
            
            <Button
              variant="ghost"
              className="w-full justify-start"
              onClick={() => handleAction('help')}
            >
              <HelpCircle className="h-4 w-4 mr-3" />
              Help & Support
            </Button>

            <Separator />
            
            <Button
              variant="ghost"
              className="w-full justify-start text-destructive hover:text-destructive"
              onClick={() => handleAction('logout')}
            >
              <LogOut className="h-4 w-4 mr-3" />
              Sign Out
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ProfileModal;