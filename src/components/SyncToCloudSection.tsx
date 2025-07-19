import React, { useState } from 'react';
import { Cloud, CloudOff, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';

interface SyncToCloudSectionProps {
  isOnline: boolean;
}

const SyncToCloudSection: React.FC<SyncToCloudSectionProps> = ({ isOnline }) => {
  const cloudServices = [
    { name: 'Google Drive', icon: '📁' },
    { name: 'Dropbox', icon: '📦' },
    { name: 'OneDrive', icon: '☁️' },
    { name: 'iCloud Drive', icon: '🍎' },
    { name: 'Nextcloud', icon: '🔒' }
  ];

  const handleSyncToCloud = (service?: string) => {
    const serviceName = service || 'cloud';
    console.log(`Syncing to ${serviceName}...`);
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
                {cloudServices.map((service) => (
                  <DropdownMenuItem
                    key={service.name}
                    onClick={() => handleSyncToCloud(service.name)}
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <span className="text-lg">{service.icon}</span>
                    {service.name}
                  </DropdownMenuItem>
                ))}
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

export default SyncToCloudSection;