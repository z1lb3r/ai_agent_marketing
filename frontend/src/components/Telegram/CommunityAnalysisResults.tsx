// frontend/src/components/Telegram/CommunityAnalysisResults.tsx

import React from 'react';
import { AlertCircle, TrendingDown, TrendingUp, Home, Shield, Users } from 'lucide-react';

interface CommunityAnalysisResultsProps {
  results: any;
  onHide: () => void;
}

export const CommunityAnalysisResults: React.FC<CommunityAnalysisResultsProps> = ({ 
  results, 
  onHide 
}) => {
  if (!results) return null;

  const getMoodIcon = (mood: string) => {
    switch (mood) {
      case 'довольны': return <TrendingUp className="h-6 w-6 text-green-500" />;
      case 'недовольны': return <TrendingDown className="h-6 w-6 text-red-500" />;
      default: return <Users className="h-6 w-6 text-gray-500" />;
    }
  };

  const getMoodColor = (mood: string) => {
    switch (mood) {
      case 'довольны': return 'text-green-600 bg-green-50';
      case 'недовольны': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getComplaintLevelColor = (level: string) => {
    switch (level) {
      case 'низкий': return 'text-green-600 bg-green-50';
      case 'высокий': return 'text-red-600 bg-red-50';
      default: return 'text-yellow-600 bg-yellow-50';
    }
  };

  const getServiceQualityColor = (score: number) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-900">Анализ Настроений Жителей</h2>
        <button 
          onClick={onHide}
          className="text-indigo-600 hover:text-indigo-800"
        >
          Скрыть Детали
        </button>
      </div>

      {/* Общие настроения */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4">Общие Настроения</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className={`p-4 rounded-lg ${getMoodColor(results.sentiment_summary?.overall_mood || 'нейтрально')}`}>
            <div className="flex items-center mb-2">
              {getMoodIcon(results.sentiment_summary?.overall_mood || 'нейтрально')}
              <span className="ml-2 font-medium">Общее Настроение</span>
            </div>
            <p className="text-2xl font-bold">
              {results.sentiment_summary?.overall_mood || 'Нейтрально'}
            </p>
          </div>
          
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center mb-2">
              <TrendingUp className="h-6 w-6 text-blue-500" />
              <span className="ml-2 font-medium text-blue-700">Удовлетворенность</span>
            </div>
            <p className="text-2xl font-bold text-blue-600">
              {results.sentiment_summary?.satisfaction_score || 0}%
            </p>
          </div>
          
          <div className={`p-4 rounded-lg ${getComplaintLevelColor(results.sentiment_summary?.complaint_level || 'средний')}`}>
            <div className="flex items-center mb-2">
              <AlertCircle className="h-6 w-6" />
              <span className="ml-2 font-medium">Уровень Жалоб</span>
            </div>
            <p className="text-2xl font-bold">
              {results.sentiment_summary?.complaint_level || 'Средний'}
            </p>
          </div>
        </div>
      </div>

      {/* Основные проблемы */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4">Основные Проблемы</h3>
        
        {results.main_issues && results.main_issues.length > 0 ? (
          <div className="space-y-3">
            {results.main_issues.map((issue: any, index: number) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div className="p-2 bg-red-100 rounded-full mr-3">
                    <Home className="h-4 w-4 text-red-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{issue.category}</p>
                    <p className="text-sm text-gray-600">{issue.issue}</p>
                  </div>
                </div>
                <span className="bg-red-100 text-red-800 px-2 py-1 rounded text-sm font-medium">
                  {issue.frequency} упоминаний
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">Основные проблемы не выявлены</p>
        )}
      </div>

      {/* Качество услуг */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4">Оценка Качества Услуг</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {results.service_quality && Object.entries(results.service_quality).map(([service, score]: [string, any]) => (
            <div key={service} className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm font-medium text-gray-700 capitalize">{service}</span>
                <span className={`text-sm font-bold ${getServiceQualityColor(score)}`}>
                  {score}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    score >= 70 ? 'bg-green-500' : 
                    score >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${score}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Предложения по улучшению */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium mb-4">Предложения по Улучшению</h3>
          
          {results.improvement_suggestions && results.improvement_suggestions.length > 0 ? (
            <div className="space-y-3">
              {results.improvement_suggestions.map((suggestion: string, index: number) => (
                <div key={index} className="flex items-start">
                  <div className="p-1 bg-blue-100 rounded-full mr-3 mt-0.5">
                    <TrendingUp className="h-4 w-4 text-blue-600" />
                  </div>
                  <p className="text-gray-700">{suggestion}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">Предложения не найдены</p>
          )}
        </div>

        {/* Срочные проблемы */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium mb-4">Срочные Проблемы</h3>
          
          {results.urgent_issues && results.urgent_issues.length > 0 ? (
            <div className="space-y-3">
              {results.urgent_issues.map((issue: string, index: number) => (
                <div key={index} className="flex items-start p-3 bg-red-50 rounded-lg">
                  <AlertCircle className="h-5 w-5 text-red-500 mr-3 mt-0.5 flex-shrink-0" />
                  <p className="text-red-800">{issue}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-4">
              <Shield className="h-12 w-12 text-green-300 mx-auto mb-2" />
              <p className="text-green-600 font-medium">Срочных проблем не выявлено</p>
            </div>
          )}
        </div>
      </div>

      {/* Ключевые темы */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium mb-4">Ключевые Темы Обсуждений</h3>
        
        {results.key_topics && results.key_topics.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {results.key_topics.map((topic: string, index: number) => (
              <span 
                key={index} 
                className="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm font-medium"
              >
                {topic}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">Ключевые темы не определены</p>
        )}
      </div>

      {/* Информация об анализе */}
      {results.prompt && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium mb-4">Критерии Анализа</h3>
          <div className="bg-gray-50 p-4 rounded-lg">
            <p className="text-gray-700">{results.prompt}</p>
          </div>
          <div className="mt-3 text-sm text-gray-500">
            Проанализировано сообщений: {results.messages_analyzed || 0} | 
            Дата анализа: {results.timestamp ? new Date(results.timestamp).toLocaleString('ru-RU') : 'Неизвестно'}
          </div>
        </div>
      )}
    </div>
  );
};