// frontend/src/pages/TelegramPage.tsx
import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { MessageSquare, BarChart2, Users, Clock, AlertCircle, Activity } from 'lucide-react';
import { useTelegramGroups, useTelegramGroup, useAnalyzeGroup } from '../hooks/useTelegramData';
import { GroupList } from '../components/Telegram/GroupList';
import { LineChart } from '../components/Charts/LineChart';
import { DashboardCard } from '../components/Dashboard/DashboardCard';
import { MessageList } from '../components/Telegram/MessageList';
import { ModeratorList } from '../components/Telegram/ModeratorList';
import { SentimentAnalysis } from '../components/Telegram/SentimentAnalysis';

export const TelegramPage: React.FC = () => {
  const { groupId } = useParams<{ groupId: string }>();
  const { data: groups } = useTelegramGroups();
  const { data: group, isLoading: isLoadingGroup } = useTelegramGroup(groupId || '');
  const analyzeGroupMutation = useAnalyzeGroup();
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [showAnalysisDetails, setShowAnalysisDetails] = useState<boolean>(false);

  // Обработчик для запуска анализа
  const handleAnalyze = async () => {
    if (!groupId) return;
    
    console.log("Starting analysis for group:", groupId);
    setAnalyzing(true);
    
    try {
      const result = await analyzeGroupMutation.mutateAsync(groupId);
      console.log("Analysis API response:", result);
      
      // Сохраняем результат без модификации
      setAnalysisResults(result);
      
      // Показываем детали после успешного анализа
      setShowAnalysisDetails(true);
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

  // Добавляем кнопку отладки, которая будет видна только в режиме разработки
  const DebugButton = () => (
    <button 
      onClick={() => console.log('Current analysisResults:', analysisResults)} 
      className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm mt-2"
    >
      Debug: Log Results Data
    </button>
  );

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
            value={analysisResults?.result?.summary?.response_time_avg ? `${analysisResults.result.summary.response_time_avg} min` : mockData.moderatorStats.avgResponse}
            icon={<Clock className="h-6 w-6 text-yellow-600" />}
          />
          <DashboardCard
            title="Resolved Issues"
            value={analysisResults?.result?.summary?.resolved_issues || mockData.moderatorStats.resolved}
            icon={<BarChart2 className="h-6 w-6 text-green-600" />}
          />
          <DashboardCard
            title="Satisfaction"
            value={analysisResults?.result?.summary?.satisfaction_score ? `${analysisResults.result.summary.satisfaction_score}%` : mockData.moderatorStats.satisfaction}
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
            analysisResults={analysisResults?.result}
            isAnalyzing={analyzing}
            onAnalyze={handleAnalyze}
          />
          
          {/* Кнопка отладки - будет видна всегда для упрощения отладки */}
          <DebugButton />
        </div>
        
        {/* Детализированные результаты анализа */}
        {analysisResults?.result && showAnalysisDetails && (
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Analysis Results</h2>
              <button 
                onClick={() => setShowAnalysisDetails(!showAnalysisDetails)}
                className="text-indigo-600 hover:text-indigo-800"
              >
                {showAnalysisDetails ? 'Hide Details' : 'Show Details'}
              </button>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Сентимент */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium mb-4">Sentiment Analysis</h3>
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="bg-green-50 p-4 rounded-lg text-center">
                    <p className="text-sm text-gray-500">Positive</p>
                    <p className="text-2xl font-semibold text-green-600">
                      {analysisResults.result.moderator_metrics?.sentiment?.positive || 0}%
                    </p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <p className="text-sm text-gray-500">Neutral</p>
                    <p className="text-2xl font-semibold text-gray-600">
                      {analysisResults.result.moderator_metrics?.sentiment?.neutral || 0}%
                    </p>
                  </div>
                  <div className="bg-red-50 p-4 rounded-lg text-center">
                    <p className="text-sm text-gray-500">Negative</p>
                    <p className="text-2xl font-semibold text-red-600">
                      {analysisResults.result.moderator_metrics?.sentiment?.negative || 0}%
                    </p>
                  </div>
                </div>
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-700 font-medium mb-2">Overall Sentiment Score</p>
                  <div className="w-full bg-gray-200 rounded-full h-4">
                    <div
                      className="bg-blue-600 h-4 rounded-full"
                      style={{ width: `${analysisResults.result.summary?.sentiment_score || 0}%` }}
                    ></div>
                  </div>
                  <p className="text-right text-sm text-gray-600 mt-1">
                    {analysisResults.result.summary?.sentiment_score || 0}%
                  </p>
                </div>
              </div>

              {/* Модераторы */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium mb-4">Moderator Performance</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-1">
                      <p className="text-sm text-gray-600">Effectiveness</p>
                      <p className="text-sm font-medium">{analysisResults.result.moderator_metrics?.performance?.effectiveness || 0}%</p>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full" 
                        style={{ width: `${analysisResults.result.moderator_metrics?.performance?.effectiveness || 0}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <p className="text-sm text-gray-600">Helpfulness</p>
                      <p className="text-sm font-medium">{analysisResults.result.moderator_metrics?.performance?.helpfulness || 0}%</p>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-500 h-2 rounded-full" 
                        style={{ width: `${analysisResults.result.moderator_metrics?.performance?.helpfulness || 0}%` }}
                      ></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between mb-1">
                      <p className="text-sm text-gray-600">Clarity</p>
                      <p className="text-sm font-medium">{analysisResults.result.moderator_metrics?.performance?.clarity || 0}%</p>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-purple-500 h-2 rounded-full" 
                        style={{ width: `${analysisResults.result.moderator_metrics?.performance?.clarity || 0}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-6">
                  <h4 className="font-medium text-sm text-gray-700 mb-3">Response Time Metrics</h4>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-gray-50 p-3 rounded-lg text-center">
                      <p className="text-xs text-gray-500">Min</p>
                      <p className="text-lg font-semibold text-gray-700">
                        {analysisResults.result.moderator_metrics?.response_time?.min || 0} min
                      </p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-lg text-center">
                      <p className="text-xs text-gray-500">Avg</p>
                      <p className="text-lg font-semibold text-gray-700">
                        {analysisResults.result.moderator_metrics?.response_time?.avg || 0} min
                      </p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-lg text-center">
                      <p className="text-xs text-gray-500">Max</p>
                      <p className="text-lg font-semibold text-gray-700">
                        {analysisResults.result.moderator_metrics?.response_time?.max || 0} min
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Ключевые темы */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium mb-4">Key Discussion Topics</h3>
                {analysisResults.result.key_topics && analysisResults.result.key_topics.length > 0 ? (
                  <ul className="space-y-3">
                    {analysisResults.result.key_topics.map((topic: string, index: number) => (
                      <li key={index} className="flex items-center p-3 bg-gray-50 rounded-lg">
                        <div className="p-2 bg-indigo-100 rounded-full mr-3">
                          <Activity className="h-4 w-4 text-indigo-600" />
                        </div>
                        <span className="text-gray-700 capitalize">{topic}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-gray-500 text-center py-8">No key topics identified</p>
                )}
              </div>
              
              {/* Рекомендации */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium mb-4">Improvement Recommendations</h3>
                {analysisResults.result.recommendations && analysisResults.result.recommendations.length > 0 ? (
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <ul className="space-y-3">
                      {analysisResults.result.recommendations.map((recommendation: string, index: number) => (
                        <li key={index} className="flex">
                          <AlertCircle className="h-5 w-5 text-yellow-500 flex-shrink-0 mr-3" />
                          <p className="text-gray-700">{recommendation}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No recommendations available</p>
                )}
              </div>
            </div>
          </div>
        )}
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <MessageList groupId={groupId} />
          <ModeratorList groupId={groupId} />
        </div>
      </div>
    </div>
  );
};