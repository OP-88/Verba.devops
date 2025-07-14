import React from 'react';
import { Cloud, CloudOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

interface SyncToCloudSectionProps {
  isOnline: boolean;
}

const SyncToCloudSection: React.FC<SyncToCloudSectionProps> = ({ isOnline }) => {
  const handleSyncToCloud = () => {
    // Implementation for cloud sync would go here
    console.log('Syncing to cloud...');
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
          
          <Button 
            onClick={handleSyncToCloud}
            disabled={!isOnline}
            variant="outline"
            size="sm"
          >
            {isOnline ? 'Sync Now' : 'Offline'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default SyncToCloudSection;