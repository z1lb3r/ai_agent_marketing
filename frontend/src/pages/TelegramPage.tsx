// frontend/src/pages/TelegramPage.tsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { MessageSquare, BarChart2, Users, Clock } from 'lucide-react';
import { useTelegramGroups, useTelegramGroup, useAnalyzeGroup } from '../hooks/useTelegramData';
import { GroupList } from '../components/Telegram/GroupList';
import { LineChart } from '../components/Charts/LineChart';
import { DashboardCard } from '../components/Dashboard/DashboardCard';
import { MessageList } from '../components/Telegram/MessageList';
import { ModeratorList } from '../components/Telegram/ModeratorList';
import { SentimentAnalysis } from '../components/Telegram/SentimentAnalysis';

export const TelegramPage: React.FC = () => {
  console.log("TelegramPage component rendering");
  
  const { groupId } = useParams<{ groupId: string }>();
  const { data: groups } = useTelegramGroups();
  const { data: group, isLoading: isLoadingGroup } = useTelegramGroup(groupId || '');
  const analyzeGroupMutation = useAnalyzeGroup();
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);

  // Добавляем эффект для логирования при изменении данных
  useEffect(() => {
    console.log("TelegramPage - Current state:", { 
      groupId, 
      group, 
      isLoadingGroup,
      analyzing,
      analysisResults 
    });
  }, [groupId, group, isLoadingGroup, analyzing, analysisResults]);

  // Обработчик для запуска анализа
  const handleAnalyze = async () => {
    if (!groupId) return;
    
    console.log("Starting analysis for group:", groupId);
    setAnalyzing(true);
    
    try {
      const result = await analyzeGroupMutation.mutateAsync(groupId);
      console.log("Analysis API response:", result);
      
      // Сохраняем весь ответ API для отладки
      setAnalysisResults(result);
    } catch (error) {
      console.error('Error analyzing group:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  // Если groupId не указан, показываем список групп
  if (!groupId) {
    console.log("No groupId - showing groups list");
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
              <p className="text-gray-600 mb-4">
                This module helps you analyze Telegram groups to evaluate moderator performance, 
                sentiment trends, and community engagement.
              </p>
              <div className="space-y-3">
                <div className="flex items-start">
                  <div className="bg-indigo-100 p-2 rounded-full mr-3 mt-0.5">
                    <span className="text-indigo-700 font-bold">1</span>
                  </div>
                  <p className="text-gray-600">
                    Select a Telegram group from the list to view details
                  </p>
                </div>
                <div className="flex items-start">
                  <div className="bg-indigo-100 p-2 rounded-full mr-3 mt-0.5">
                    <span className="text-indigo-700 font-bold">2</span>
                  </div>
                  <p className="text-gray-600">
                    Run analysis to get insights on moderator performance
                  </p>
                </div>
                <div className="flex items-start">
                  <div className="bg-indigo-100 p-2 rounded-full mr-3 mt-0.5">
                    <span className="text-indigo-700 font-bold">3</span>
                  </div>
                  <p className="text-gray-600">
                    Review sentiment analysis and key discussion topics
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Если загружаем данные группы
  if (isLoadingGroup) {
    console.log("Loading group data...");
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="bg-white h-32 rounded-lg shadow"></div>
              ))}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-white h-80 rounded-lg shadow"></div>
              <div className="bg-white h-80 rounded-lg shadow"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Если группа не найдена
  if (!group) {
    console.log("Group not found");
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center bg-white shadow rounded-lg p-8">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Group Not Found</h2>
            <p className="text-lg text-gray-600 mb-6">
              The Telegram group you're looking for couldn't be found. It may have been removed or you don't have access.
            </p>
            <a 
              href="/telegram" 
              className="inline-block px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md"
            >
              Back to Groups
            </a>
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
      { date: '2025-04-06', value: 4.2 },
      { date: '2025-04-07', value: 3.8 },
    ],
    moderatorStats: {
      avgResponse: '4.5 min',
      resolved: 43,
      satisfaction: '92%',
      activeTime: '8.5 hours'
    }
  };

  // Безопасное получение значений из результатов анализа
  const getSafeValue = (path: string, defaultValue: any = null) => {
    try {
      const parts = path.split('.');
      let result = analysisResults;
      
      for (const part of parts) {
        if (result === undefined || result === null) return defaultValue;
        result = result[part];
      }
      
      return result === undefined || result === null ? defaultValue : result;
    } catch (error) {
      console.error(`Error accessing path ${path}:`, error);
      return defaultValue;
    }
  };

  console.log("Rendering group details view");
  
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-semibold text-gray-900">
            {group.name}
          </h1>
          
          <a 
            href="/telegram" 
            className="text-indigo-600 hover:text-indigo-800"
          >
            Back to all groups
          </a>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
          <DashboardCard
            title="Members"
            value={group.settings?.members_count || 0}
            icon={<Users className="h-6 w-6 text-blue-600" />}
          />
          <DashboardCard
            title="Avg Response Time"
            value={getSafeValue('result.summary.response_time_avg') ? `${getSafeValue('result.summary.response_time_avg')} min` : mockData.moderatorStats.avgResponse}
            icon={<Clock className="h-6 w-6 text-yellow-600" />}
          />
          <DashboardCard
            title="Resolved Issues"
            value={getSafeValue('result.summary.resolved_issues', mockData.moderatorStats.resolved)}
            icon={<BarChart2 className="h-6 w-6 text-green-600" />}
          />
          <DashboardCard
            title="Satisfaction"
            value={getSafeValue('result.summary.satisfaction_score') ? `${getSafeValue('result.summary.satisfaction_score')}%` : mockData.moderatorStats.satisfaction}
            icon={<MessageSquare className="h-6 w-6 text-purple-600" />}
          />
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <LineChart 
            data={mockData.responseTime}
            dataKey="value"
            xAxisKey="date"
            title="Response Time Trend (minutes)"
            color="#3b82f6"
          />
          
          <SentimentAnalysis 
            groupId={groupId}
            analysisResults={analysisResults}
            isAnalyzing={analyzing}
            onAnalyze={handleAnalyze}
          />
        </div>
        
        {/* Временно удалим блок с детальными результатами для отладки */}
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <MessageList groupId={groupId} />
          <ModeratorList groupId={groupId} />
        </div>
      </div>
    </div>
  );
};