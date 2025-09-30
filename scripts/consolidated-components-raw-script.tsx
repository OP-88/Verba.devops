/*
===============================================
VERBA STUDY APP - CONSOLIDATED COMPONENTS
===============================================
All React components used in the Study Spot redesign
Copy and paste individual components as needed
*/

// ============= ProfileModal.tsx =============
import React, { useState } from 'react';
import { User, Upload, Camera } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ProfileModal: React.FC<ProfileModalProps> = ({ isOpen, onClose }) => {
  const [name, setName] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');

  const handleAvatarUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const url = URL.createObjectURL(file);
      setAvatarUrl(url);
    }
  };

  const handleSave = () => {
    console.log('Saving profile:', { name, avatarUrl });
    // Here you would implement the actual save functionality
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Profile Settings</DialogTitle>
          <DialogDescription>
            Update your name and profile picture
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-6">
          {/* Avatar Upload */}
          <div className="flex flex-col items-center space-y-4">
            <Avatar className="h-24 w-24">
              <AvatarImage src={avatarUrl} alt="User Avatar" />
              <AvatarFallback>
                <User className="h-12 w-12" />
              </AvatarFallback>
            </Avatar>
            
            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => document.getElementById('avatar-upload')?.click()}
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload Photo
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  // Here you would implement camera functionality
                  console.log('Take photo with camera');
                }}
              >
                <Camera className="h-4 w-4 mr-2" />
                Take Photo
              </Button>
            </div>
            
            <input
              id="avatar-upload"
              type="file"
              accept="image/*"
              onChange={handleAvatarUpload}
              className="hidden"
            />
          </div>

          {/* Name Input */}
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              placeholder="Enter your name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          {/* Save Button */}
          <Button onClick={handleSave} className="w-full">
            Save Profile
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// ============= DonateButton.tsx =============
import React from 'react';
import { Heart } from 'lucide-react';
import { Button } from '@/components/ui/button';

const DonateButton: React.FC = () => {
  const handleDonateClick = () => {
    // Open Buy Me a Coffee link in a new tab
    window.open('https://buymeacoffee.com/verba', '_blank');
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

// ============= SyncToCloudSection.tsx =============
import React, { useState } from 'react';
import { Cloud, CloudOff, ChevronDown, HardDrive, Box, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';

interface SyncToCloudSectionProps {
  isOnline: boolean;
}

const SyncToCloudSection: React.FC<SyncToCloudSectionProps> = ({ isOnline }) => {
  const cloudServices = [
    { name: 'Google Drive', Icon: HardDrive },
    { name: 'Dropbox', Icon: Box },
    { name: 'OneDrive', Icon: Cloud },
    { name: 'Nextcloud', Icon: Shield }
  ];

  const handleSyncToCloud = (service?: string) => {
    const serviceName = service || 'cloud';
    console.log(`Syncing to ${serviceName}...`);
    
    // Implement actual sync functionality based on service
    switch (service) {
      case 'Google Drive':
        // Integrate with Google Drive API
        window.open('https://drive.google.com', '_blank');
        break;
      case 'Dropbox':
        // Integrate with Dropbox API
        window.open('https://dropbox.com', '_blank');
        break;
      case 'OneDrive':
        // Integrate with OneDrive API
        window.open('https://onedrive.live.com', '_blank');
        break;
      case 'Nextcloud':
        // Show Nextcloud server input modal
        const server = prompt('Enter your Nextcloud server URL:');
        if (server) {
          console.log(`Connecting to Nextcloud server: ${server}`);
        }
        break;
      default:
        console.log('Generic cloud sync');
    }
  };

  return (
    <Card className="mb-8 border-border/50">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {isOnline ? (
              <Cloud className="w-6 h-6 text-primary" />
            ) : (
              <CloudOff className="w-6 h-6 text-muted-foreground" />
            )}
            <div>
              <h3 className="font-semibold">Cloud Sync</h3>
              <p className="text-sm text-muted-foreground">
                {isOnline 
                  ? 'Your data is automatically synced to the cloud' 
                  : 'Connect to internet to sync your data'
                }
              </p>
            </div>
          </div>
          
          {isOnline ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="flex items-center gap-2">
                  Sync Now
                  <ChevronDown className="h-3 w-3" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                {cloudServices.map((service) => {
                  const IconComponent = service.Icon;
                  return (
                    <DropdownMenuItem
                      key={service.name}
                      onClick={() => handleSyncToCloud(service.name)}
                      className="flex items-center gap-2 cursor-pointer"
                    >
                      <IconComponent className="h-4 w-4" />
                      {service.name}
                    </DropdownMenuItem>
                  );
                })}
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button variant="outline" size="sm" disabled>
              Offline
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// ============= PreviouslyImportedFiles.tsx =============
import React, { useState } from 'react';
import { File, Play, Trash2, Download, Edit, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface ImportedFile {
  id: string;
  name: string;
  size: string;
  duration: string;
  uploadDate: string;
  status: 'completed' | 'processing' | 'failed';
  transcriptId?: string;
}

const PreviouslyImportedFiles: React.FC = () => {
  const [files] = useState<ImportedFile[]>([
    {
      id: '1',
      name: 'meeting-recording-01.mp3',
      size: '15.2 MB',
      duration: '45:30',
      uploadDate: '2024-01-15',
      status: 'completed',
      transcriptId: 'transcript-1'
    },
    {
      id: '2',
      name: 'lecture-physics-chapter5.wav',
      size: '28.7 MB',
      duration: '1:20:15',
      uploadDate: '2024-01-14',
      status: 'completed',
      transcriptId: 'transcript-2'
    },
    {
      id: '3',
      name: 'interview-candidate-a.m4a',
      size: '12.1 MB',
      duration: '35:45',
      uploadDate: '2024-01-12',
      status: 'processing'
    }
  ]);

  const handlePlay = (fileId: string) => {
    console.log(`Playing file: ${fileId}`);
    // Implement audio playback functionality
  };

  const handleDelete = (fileId: string) => {
    console.log(`Deleting file: ${fileId}`);
    // Implement delete functionality
  };

  const handleDownload = (fileId: string) => {
    console.log(`Downloading file: ${fileId}`);
    // Implement download functionality
  };

  const handleEditTranscript = (transcriptId: string) => {
    console.log(`Editing transcript: ${transcriptId}`);
    // Navigate to transcript editor
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'processing': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  if (files.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <File className="h-12 w-12 mx-auto mb-4 opacity-50" />
        <p>No previously imported files</p>
        <p className="text-sm">Your uploaded audio files will appear here</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {files.map((file) => (
        <div key={file.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors">
          <div className="flex items-center space-x-4 flex-1">
            <File className="h-8 w-8 text-primary" />
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{file.name}</p>
              <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                <span>{file.size}</span>
                <span className="flex items-center">
                  <Clock className="h-3 w-3 mr-1" />
                  {file.duration}
                </span>
                <span>{file.uploadDate}</span>
              </div>
            </div>
            <Badge className={getStatusColor(file.status)}>
              {file.status}
            </Badge>
          </div>
          
          <div className="flex items-center space-x-2 ml-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handlePlay(file.id)}
              title="Play audio"
            >
              <Play className="h-4 w-4" />
            </Button>
            
            {file.transcriptId && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => handleEditTranscript(file.transcriptId!)}
                title="Edit transcript"
              >
                <Edit className="h-4 w-4" />
              </Button>
            )}
            
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleDownload(file.id)}
              title="Download file"
            >
              <Download className="h-4 w-4" />
            </Button>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleDelete(file.id)}
              title="Delete file"
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
};

// ============= ExpandableAIChat.tsx =============
import React, { useState } from 'react';
import { MessageCircle, X, Maximize2, Minimize2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import AIChatArea from './AIChatArea';
import AIChatSidebar from './AIChatSidebar';

const ExpandableAIChat: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [showChatSidebar, setShowChatSidebar] = useState(false);

  const handleSelectChat = (chatId: string) => {
    console.log('Selected chat:', chatId);
    setShowChatSidebar(false);
  };

  if (!isOpen) {
    return (
      <div className="fixed bottom-8 right-8 z-50">
        <Button
          onClick={() => setIsOpen(true)}
          size="lg"
          className="rounded-full pl-4 pr-6 h-12 bg-primary hover:bg-primary/90 shadow-lg hover:shadow-xl transition-all duration-300 flex items-center gap-2"
        >
          <MessageCircle className="h-5 w-5" />
          <span className="text-sm font-medium">AI Assistant</span>
        </Button>
      </div>
    );
  }

  return (
    <>
      {/* Backdrop */}
      {isExpanded && (
        <div className="fixed inset-0 bg-black/10 z-40" onClick={() => setIsExpanded(false)} />
      )}
      
      {/* Chat Container */}
      <div className={`fixed z-50 transition-all duration-300 ${
        isExpanded 
          ? 'inset-8 lg:inset-16' 
          : 'bottom-8 right-8 w-96 h-[500px]'
      }`}>
        <Card className="h-full flex flex-col shadow-2xl border-border/20 bg-background/95 backdrop-blur-sm">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-border/10">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse" />
              <h3 className="font-medium text-foreground">AI Assistant</h3>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(!isExpanded)}
                className="h-8 w-8 p-0 hover:bg-accent/50"
              >
                {isExpanded ? (
                  <Minimize2 className="h-4 w-4" />
                ) : (
                  <Maximize2 className="h-4 w-4" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsOpen(false)}
                className="h-8 w-8 p-0 hover:bg-accent/50"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
          
          {/* Chat Area */}
          <div className="flex-1 overflow-hidden">
            <AIChatArea onShowSidebar={() => setShowChatSidebar(true)} />
          </div>
        </Card>
      </div>

      {/* AI Chat Sidebar */}
      <AIChatSidebar 
        isOpen={showChatSidebar}
        onClose={() => setShowChatSidebar(false)}
        onSelectChat={handleSelectChat}
      />
    </>
  );
};

// ============= StudyProfileButton.tsx =============
import React, { useState } from 'react';
import { Settings, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const StudyProfileButton: React.FC = () => {
  const [isOnline] = useState(true);

  const handleAction = (action: string) => {
    console.log(`Profile action: ${action}`);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-10 w-10 rounded-full p-0">
          <Avatar className="h-10 w-10 border-2 border-border/20">
            <AvatarImage src="/placeholder-avatar.jpg" alt="Profile" />
            <AvatarFallback className="bg-muted">JD</AvatarFallback>
          </Avatar>
          {/* Status indicator */}
          <div className={`absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-background ${
            isOnline ? 'bg-green-500' : 'bg-gray-400'
          }`} />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-48">
        <DropdownMenuItem onClick={() => handleAction('settings')}>
          <Settings className="h-4 w-4 mr-2" />
          Settings
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem 
          onClick={() => handleAction('logout')}
          className="text-destructive focus:text-destructive"
        >
          <LogOut className="h-4 w-4 mr-2" />
          Sign Out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

/*
===============================================
USAGE INSTRUCTIONS:
===============================================

1. Copy the component you need from above
2. Create a new .tsx file for each component
3. Import the required dependencies at the top
4. Export the component as default

Example file structure:
- src/components/ProfileModal.tsx
- src/components/DonateButton.tsx
- src/components/SyncToCloudSection.tsx
- src/components/PreviouslyImportedFiles.tsx
- src/components/ExpandableAIChat.tsx
- src/components/StudyProfileButton.tsx

All components use:
- React functional components with TypeScript
- Lucide React icons
- Shadcn/ui components
- Tailwind CSS classes
- Console logging for button actions (replace with actual functionality)

Customize as needed for your specific implementation!
*/