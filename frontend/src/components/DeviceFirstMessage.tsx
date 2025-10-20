import React from 'react';
import { Smartphone } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

const DeviceFirstMessage: React.FC = () => {
  return (
    <Card className="mb-8 bg-primary/5 border-primary/20">
      <CardContent className="p-6">
        <div className="flex items-center space-x-3">
          <Smartphone className="w-6 h-6 text-primary" />
          <div>
            <h3 className="font-semibold text-primary">Device-First Experience</h3>
            <p className="text-sm text-muted-foreground">
              All your data is stored locally on your device for privacy and works offline. 
              Cloud sync is optional and available when you're online.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default DeviceFirstMessage;