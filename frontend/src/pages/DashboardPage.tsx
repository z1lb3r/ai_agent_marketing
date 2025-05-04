// frontend/src/pages/DashboardPage.tsx
import React from 'react';
import { DashboardCard } from '../components/Dashboard/DashboardCard';
import { GroupList } from '../components/Telegram/GroupList';
import { MessageSquare, Users, TrendingUp, Clock } from 'lucide-react';
import { useTelegramGroups } from '../hooks/useTelegramData';

export const DashboardPage: React.FC = () => {
  const { data: groups } = useTelegramGroups();

  // В реальном приложении эти данные будут из API
  const stats = {
    totalGroups: groups?.length || 0,
    totalModerators: 12,
    avgResponseTime: 5.2,
    resolvedIssues: 156,
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-2xl font-semibold text-gray-900 mb-8">
          Dashboard
        </h1>
        
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <DashboardCard
            title="Total Groups"
            value={stats.totalGroups}
            icon={<MessageSquare className="h-6 w-6 text-blue-600" />}
          />
          <DashboardCard
            title="Active Moderators"
            value={stats.totalModerators}
            icon={<Users className="h-6 w-6 text-green-600" />}
          />
          <DashboardCard
            title="Avg Response Time"
            value={`${stats.avgResponseTime} min`}
            icon={<Clock className="h-6 w-6 text-yellow-600" />}
            trend={{ value: 12, isPositive: false }}
          />
          <DashboardCard
            title="Resolved Issues"
            value={stats.resolvedIssues}
            icon={<TrendingUp className="h-6 w-6 text-purple-600" />}
            trend={{ value: 8, isPositive: true }}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <GroupList />
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium mb-4">Recent Activity</h3>
            {/* TODO: Add recent activity component */}
          </div>
        </div>
      </div>
    </div>
  );
};