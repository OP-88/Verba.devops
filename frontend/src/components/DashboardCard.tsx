import React from 'react';

interface DashboardCardProps {
  title: string;
  description: string;
  icon: React.ComponentType<any>;
  color: string;
  onClick: () => void;
  onKeyDown: (event: React.KeyboardEvent) => void;
}

const DashboardCard: React.FC<DashboardCardProps> = ({ title, description, icon: Icon, color, onClick, onKeyDown }) => {
  return (
    <div
      className={`${color} rounded-xl p-6 text-white cursor-pointer transition-all duration-300 hover:scale-105 hover:shadow-xl focus:outline-none focus:ring-4 focus:ring-white/30`}
      onClick={onClick}
      onKeyDown={onKeyDown}
      tabIndex={0}
      role="button"
      aria-label={`${title}: ${description}`}
    >
      <div className="flex items-center justify-center w-12 h-12 bg-white/20 rounded-lg mb-4">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-white/80 text-sm">{description}</p>
    </div>
  );
};

export default DashboardCard;