// frontend/src/components/Telegram/CommunityAnalysisResults.tsx
import React, { useState } from 'react';
import { X, TrendingDown, TrendingUp, AlertCircle, Home, MessageSquare } from 'lucide-react';

interface CommunityAnalysisResultsProps {
  results: any;
  onHide: () => void;
}

interface RelatedMessage {
  text: string;
  date: string;
  author?: string;
}

interface Issue {
  category: string;
  issue: string;
  frequency: number;
  related_messages?: RelatedMessage[];
}

export const CommunityAnalysisResults: React.FC<CommunityAnalysisResultsProps> = ({ 
  results, 
  onHide 
}) => {
  // Состояние для поп-апа с сообщениями
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);
  const [showMessagesModal, setShowMessagesModal] = useState(false);

  const getComplaintLevelColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'низкий':
        return 'bg-green-50 text-green-700';
      case 'средний':
        return 'bg-yellow-50 text-yellow-700';
      case 'высокий':
        return 'bg-red-50 text-red-700';
      default:
        return 'bg-gray-50 text-gray-700';
    }
  };

  const getServiceQualityColor = (score: number) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 40) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Функция для показа сообщений проблемы
  const handleIssueClick = (issue: Issue) => {
    if (issue.related_messages && issue.related_messages.length > 0) {
      setSelectedIssue(issue);
      setShowMessagesModal(true);
    }
  };

  // Функция для форматирования даты
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  // ИСПРАВЛЕНО: Показываем ТОЛЬКО отфильтрованные main_issues
  const allIssues: Issue[] = [
    ...(results.main_issues || [])
    // urgent_issues и key_topics убраны - они не проходят фильтрацию 7%
  ];

  return (
    <>
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-gray-900">Анализ Настроений Жителей</h2>
              <p className="text-sm text-gray-600 mt-1">
                Проанализировано {results.messages_analyzed || 0} сообщений за последние {results.days_analyzed || 'N'} дней
              </p>
            </div>
            <button
              onClick={onHide}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          <div className="p-6 space-y-8">
            {/* Общие настроения */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium mb-4">Общие Настроения</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-red-50 p-4 rounded-lg">
                  <div className="flex items-center mb-2">
                    <TrendingDown className="h-6 w-6 text-red-500" />
                    <span className="ml-2 font-medium text-red-700">Общее Настроение</span>
                  </div>
                  <p className="text-2xl font-bold text-red-600">
                    {results.sentiment_summary?.overall_mood || 'недовольны'}
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

            {/* ОСНОВНЫЕ ПРОБЛЕМЫ - ТОЛЬКО ОТФИЛЬТРОВАННЫЕ */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium mb-4">
                Основные Проблемы
                <span className="text-sm text-gray-500 ml-2">(кликните чтобы посмотреть сообщения)</span>
              </h3>
              
              {allIssues && allIssues.length > 0 ? (
                <div className="space-y-3">
                  {allIssues.map((issue: Issue, index: number) => (
                    <div 
                      key={index} 
                      className={`flex items-center justify-between p-3 bg-gray-50 rounded-lg transition-colors ${
                        issue.related_messages && issue.related_messages.length > 0 
                          ? 'hover:bg-gray-100 cursor-pointer' 
                          : ''
                      }`}
                      onClick={() => handleIssueClick(issue)}
                      title={issue.related_messages && issue.related_messages.length > 0 ? 'Нажмите чтобы посмотреть сообщения' : ''}
                    >
                      <div className="flex items-center">
                        <div className="p-2 bg-red-100 rounded-full mr-3">
                          <Home className="h-4 w-4 text-red-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{issue.category}</p>
                          <p className="text-sm text-gray-600">{issue.issue}</p>
                          {issue.related_messages && issue.related_messages.length > 0 && (
                            <p className="text-xs text-blue-600 mt-1">
                              📱 {issue.related_messages.length} сообщений
                            </p>
                          )}
                        </div>
                      </div>
                      <span className="bg-red-100 text-red-800 px-2 py-1 rounded text-sm font-medium">
                        {issue.frequency || 1} упоминаний
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">Проблемы не выявлены</p>
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
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Рекомендации по улучшению */}
            {results.improvement_suggestions && results.improvement_suggestions.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium mb-4">Рекомендации по улучшению</h3>
                
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                  <ul className="space-y-3">
                    {results.improvement_suggestions.map((suggestion: string, index: number) => (
                      <li key={index} className="flex">
                        <div className="flex-shrink-0 mr-3">
                          <MessageSquare className="h-5 w-5 text-blue-600" />
                        </div>
                        <p className="text-gray-700">{suggestion}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Ключевые темы отдельно (не как проблемы) */}
            {results.key_topics && results.key_topics.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium mb-4">Ключевые темы обсуждения</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {results.key_topics.map((topic: string, index: number) => (
                    <div key={index} className="flex items-center p-3 bg-blue-50 rounded-lg">
                      <div className="p-2 bg-blue-100 rounded-full mr-3">
                        <MessageSquare className="h-4 w-4 text-blue-600" />
                      </div>
                      <span className="text-blue-800 font-medium">{topic}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Модальное окно с сообщениями */}
      {showMessagesModal && selectedIssue && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-60 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[80vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-gray-900">Сообщения по проблеме</h3>
                <p className="text-sm text-gray-600">{selectedIssue.issue}</p>
              </div>
              <button
                onClick={() => setShowMessagesModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="p-6">
              <div className="space-y-4">
                {selectedIssue.related_messages?.map((message: RelatedMessage, index: number) => (
                  <div key={index} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-sm font-medium text-gray-600">
                        {message.author || 'Аноним'}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatDate(message.date)}
                      </span>
                    </div>
                    <p className="text-gray-800">{message.text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};