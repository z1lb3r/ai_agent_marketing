// frontend/src/components/Common/Header.tsx
import React from 'react';
import { useLocation } from 'react-router-dom';

export const Header: React.FC = () => {
  const location = useLocation();
  
  // Определение заголовка на основе текущего пути
  const getPageTitle = () => {
    const path = location.pathname;
    if (path.startsWith('/telegram')) {
      return 'Telegram Analytics';
    } else if (path.startsWith('/email')) {
      return 'Email Analytics';
    } else if (path.startsWith('/calls')) {
      return 'Calls Analytics';
    } else if (path.startsWith('/settings')) {
      return 'Settings';
    } else {
      return 'Dashboard';
    }
  };

  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <h1 className="text-xl font-semibold text-gray-800">
            {getPageTitle()}
          </h1>
          <div className="flex items-center">
            <span className="text-sm text-gray-500">
              Multi-Channel Analyzer
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};