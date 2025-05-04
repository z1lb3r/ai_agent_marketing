// frontend/src/components/Common/Sidebar.tsx
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BarChart2, MessageSquare, Mail, Phone, Settings } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: BarChart2 },
    { name: 'Telegram', href: '/telegram', icon: MessageSquare },
    { name: 'Email', href: '/email', icon: Mail },
    { name: 'Calls', href: '/calls', icon: Phone },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <div className="hidden md:flex md:flex-shrink-0">
      <div className="flex flex-col w-64">
        <div className="flex flex-col h-0 flex-1 bg-gray-800">
          <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
            <div className="flex items-center flex-shrink-0 px-4">
              <span className="text-white text-xl font-semibold">
                Multi-Channel Analyzer
              </span>
            </div>
            <nav className="mt-5 flex-1 px-2 space-y-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`${
                      isActive
                        ? 'bg-gray-900 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                    } group flex items-center px-2 py-2 text-sm font-medium rounded-md`}
                  >
                    <item.icon
                      className={`${
                        isActive ? 'text-gray-300' : 'text-gray-400 group-hover:text-gray-300'
                      } mr-3 flex-shrink-0 h-6 w-6`}
                    />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>
      </div>
    </div>
  );
};