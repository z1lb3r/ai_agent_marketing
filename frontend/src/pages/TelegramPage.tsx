// frontend/src/pages/TelegramPage.tsx
import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { MessageSquare, BarChart2, Users, Clock } from 'lucide-react';
import { useTelegramGroups, useTelegramGroup, useAnalyzeGroup } from '../hooks/useTelegramData';
import { GroupList } from '../components/Telegram/GroupList';
import { LineChart } from '../components/Charts/LineChart';
import { DashboardCard } from '../components/Dashboard/DashboardCard';

export const TelegramPage: React.FC = () => {
  const { groupId } = useParams<{ groupId: string }>();
  const { data: groups, isLoading: isLoadingGroups } = useTelegramGroups();
  const { data: group, isLoading: isLoadingGroup } = useTelegramGroup(groupId || '');
  const analyzeGroupMutation = useAnalyzeGroup();
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);

  // Обработчик для запуска анализа
  const handleAnalyze = async () => {
    if (!groupId) return;
    
    setAnalyzing(true);
    try {
      const result = await analyzeGroupMutation.mutateAsync(groupId);
      setAnalysisResults(result.result);
    } catch (error) {
      console.error('Error analyzing group:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  // Если groupId не указан, показываем список групп
  if (!groupId) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-2xl font-semibold text-gray-900 mb-8">
            Telegram Analysis
          </h1>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <GroupList />
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium mb-4">How to Use</h3>
              <p className="text-gray-600 mb-2">
                1. Select a Telegram group from the list to view details.
              </p>
              <p className="text-gray-600 mb-2">
                2. Run analysis to get insights on moderator performance.
              </p>
              <p className="text-gray-600 mb-2">
                3. Review sentiment analysis and key discussion topics.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Если загружаем данные группы
  if (isLoadingGroup) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-lg text-gray-600">Loading group data...</p>
          </div>
        </div>
      </div>
    );
  }

  // Если группа не найдена
  if (!group) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-lg text-red-600">Group not found</p>
          </div>
        </div>
      </div>
    );
  }

  // Мок-данные для демонстрации (в реальном приложении будут из API)
  const mockData = {
    responseTime: [
      { date: '2025-04-01', value: 4.8 },
      { date: '2025-04-02', value: 5.2 },
      { date: '2025-04-03', value: 3.9 },
      { date: '2025-04-04', value: 4.5 },
      { date: '2025-04-05', value: 5.1 },
    ],
    moderatorStats: {
      avgResponse: '4.5 min',
      resolved: 43,
      satisfaction: '92%',
      activeTime: '8.5 hours'
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-semibold text-gray-900">
            {group.name}
          </h1>
          
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className={`px-4 py-2 rounded-md ${
              analyzing 
                ? 'bg-gray-300 cursor-not-allowed' 
                : 'bg-indigo-600 hover:bg-indigo-700 text-white'
            }`}
          >
            {analyzing ? 'Analyzing...' : 'Analyze Group'}
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
          <DashboardCard
            title="Members"
            value={group.settings?.members_count || 0}
            icon={<Users className="h-6 w-6 text-blue-600" />}
          />
          <DashboardCard
            title="Avg Response Time"
            value={mockData.moderatorStats.avgResponse}
            icon={<Clock className="h-6 w-6 text-yellow-600" />}
          />
          <DashboardCard
            title="Resolved Issues"
            value={mockData.moderatorStats.resolved}
            icon={<BarChart2 className="h-6 w-6 text-green-600" />}
          />
          <DashboardCard
            title="Satisfaction"
            value={mockData.moderatorStats.satisfaction}
            icon={<MessageSquare className="h-6 w-6 text-purple-600" />}
          />
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <LineChart 
            data={mockData.responseTime}
            dataKey="value"
            xAxisKey="date"
            title="Response Time Trend (minutes)"
            color="#3b82f6"
          />
          
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium mb-4">Moderator Analysis</h3>
            {analyzing ? (
              <p className="text-gray-600">Analyzing data...</p>
            ) : analysisResults ? (
              <div>
                <p className="text-gray-600 mb-3">{analysisResults}</p>
              </div>
            ) : (
              <p className="text-gray-600">
                Click the "Analyze Group" button to get detailed insights about moderator 
                performance, sentiment analysis, and key discussion topics.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};