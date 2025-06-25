// frontend/src/components/Telegram/CommunityAnalysisResults.tsx - ОБНОВЛЕННАЯ ВЕРСИЯ

import React, { useState } from 'react';
import { X, TrendingDown, TrendingUp, AlertCircle, Home, MessageSquare, LinkIcon, ExternalLink } from 'lucide-react';

interface CommunityAnalysisResultsProps {
  results: any;
  onHide: () => void;
  isPostsAnalysis?: boolean; // НОВЫЙ ПРОП ДЛЯ ОПРЕДЕЛЕНИЯ ТИПА АНАЛИЗА
}

interface RelatedMessage {
  text: string;
  date: string;
  author?: string;
  post_link?: string; // НОВОЕ ПОЛЕ ДЛЯ ССЫЛКИ НА ПОСТ
}

interface Issue {
  category: string;
  issue: string;
  frequency: number;
  related_messages?: RelatedMessage[];
}

export const CommunityAnalysisResults: React.FC<CommunityAnalysisResultsProps> = ({ 
  results, 
  onHide,
  isPostsAnalysis = false // ПО УМОЛЧАНИЮ FALSE
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

  // ОБНОВЛЕНО: Показываем ТОЛЬКО отфильтрованные main_issues
  const allIssues: Issue[] = [
    ...(results.main_issues || [])
  ];

  // НОВАЯ ФУНКЦИЯ: Получение уникальных постов из результатов
  const getAnalyzedPosts = () => {
    if (!isPostsAnalysis || !results.post_links) return [];
    return results.post_links;
  };

  return (
    <div className="mb-8">
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            {/* ОБНОВЛЕННЫЙ ЗАГОЛОВОК В ЗАВИСИМОСТИ ОТ ТИПА АНАЛИЗА */}
            <h3 className="text-lg font-medium">
              {isPostsAnalysis ? 'Результаты Анализа Комментариев к Постам' : 'Результаты Анализа Настроений Сообщества'}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              {isPostsAnalysis 
                ? `Проанализировано ${results.comments_analyzed || 0} комментариев к ${results.posts_analyzed || 0} постам`
                : `Проанализировано ${results.messages_analyzed || 0} сообщений за ${results.days_analyzed || 7} дней`
              }
            </p>
          </div>
          <button
            onClick={onHide}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* НОВЫЙ БЛОК: Информация о проанализированных постах */}
        {isPostsAnalysis && getAnalyzedPosts().length > 0 && (
          <div className="mb-6 p-4 bg-purple-50 border border-purple-200 rounded-lg">
            <h4 className="font-medium text-purple-900 mb-2 flex items-center">
              <LinkIcon className="h-4 w-4 mr-2" />
              Проанализированные посты
            </h4>
            <div className="space-y-2">
              {getAnalyzedPosts().map((link: string, index: number) => (
                <div key={index} className="flex items-center space-x-2">
                  <a 
                    href={link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-purple-600 hover:text-purple-800 text-sm flex items-center"
                  >
                    <ExternalLink className="h-3 w-3 mr-1" />
                    {link}
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Общая сводка настроений */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-800">
              {results.sentiment_summary?.overall_mood || 'Н/Д'}
            </div>
            <div className="text-sm text-gray-600 mt-1">Общее настроение</div>
          </div>
          
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {results.sentiment_summary?.satisfaction_score || 0}%
            </div>
            <div className="text-sm text-gray-600 mt-1">
              {isPostsAnalysis ? 'Поддержка' : 'Удовлетворенность'}
            </div>
          </div>
          
          <div className="text-center p-4 rounded-lg">
            <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
              getComplaintLevelColor(results.sentiment_summary?.complaint_level || '')
            }`}>
              {results.sentiment_summary?.complaint_level || 'Неопределен'}
            </div>
            <div className="text-sm text-gray-600 mt-2">
              {isPostsAnalysis ? 'Уровень критики' : 'Уровень жалоб'}
            </div>
          </div>
        </div>

        {/* НОВЫЙ БЛОК: Реакции на посты (только для анализа постов) */}
        {isPostsAnalysis && results.post_reactions && (
          <div className="mb-6">
            <h4 className="font-medium text-gray-900 mb-3">Распределение реакций</h4>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-xl font-bold text-green-600">
                  {results.post_reactions.положительные || 0}
                </div>
                <div className="text-xs text-green-700">Позитивные</div>
              </div>
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-xl font-bold text-gray-600">
                  {results.post_reactions.нейтральные || 0}
                </div>
                <div className="text-xs text-gray-700">Нейтральные</div>
              </div>
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-xl font-bold text-red-600">
                  {results.post_reactions.негативные || 0}
                </div>
                <div className="text-xs text-red-700">Негативные</div>
              </div>
            </div>
          </div>
        )}

        {/* Оценки качества услуг (только для анализа сообщества) */}
        {!isPostsAnalysis && results.service_quality && (
          <div className="mb-6">
            <h4 className="font-medium text-gray-900 mb-3">Оценки качества услуг</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(results.service_quality).map(([service, score]: [string, any]) => (
                <div key={service} className="text-center">
                  <div className={`text-2xl font-bold ${getServiceQualityColor(score)}`}>
                    {score}%
                  </div>
                  <div className="text-sm text-gray-600 mt-1 capitalize">
                    {service.replace(/_/g, ' ')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Основные проблемы */}
        {allIssues.length > 0 && (
          <div className="mb-6">
            <h4 className="font-medium text-gray-900 mb-4">
              {isPostsAnalysis ? 'Основные темы обсуждения' : 'Основные проблемы'}
            </h4>
            <div className="space-y-3">
              {allIssues.map((issue, index) => (
                <div
                  key={index}
                  onClick={() => handleIssueClick(issue)}
                  className={`p-4 border rounded-lg transition-all ${
                    issue.related_messages && issue.related_messages.length > 0
                      ? 'border-gray-200 hover:border-blue-300 cursor-pointer hover:shadow-md'
                      : 'border-gray-200'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span className="inline-block w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
                        <span className="font-medium text-gray-900">{issue.category}</span>
                        <span className="ml-2 text-sm text-gray-500">
                          ({issue.frequency} {issue.frequency === 1 ? 'упоминание' : 'упоминаний'})
                        </span>
                      </div>
                      <p className="text-gray-700">{issue.issue}</p>
                      {issue.related_messages && issue.related_messages.length > 0 && (
                        <p className="text-sm text-blue-600 mt-2">
                          📄 Нажмите, чтобы посмотреть {issue.related_messages.length} связанных {
                            isPostsAnalysis ? 'комментариев' : 'сообщений'
                          }
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Ключевые темы обсуждения */}
        {results.key_topics && results.key_topics.length > 0 && (
          <div className="mb-6">
            <h4 className="font-medium text-gray-900 mb-3">
              {isPostsAnalysis ? 'Популярные темы' : 'Ключевые темы обсуждения'}
            </h4>
            <div className="flex flex-wrap gap-2">
              {results.key_topics.map((topic: string, index: number) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-indigo-100 text-indigo-800 text-sm rounded-full"
                >
                  {topic}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Рекомендации */}
        {results.improvement_suggestions && results.improvement_suggestions.length > 0 && (
          <div className="mb-6">
            <h4 className="font-medium text-gray-900 mb-3">Рекомендации по улучшению</h4>
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
              <ul className="space-y-2">
                {results.improvement_suggestions.map((suggestion: string, index: number) => (
                  <li key={index} className="flex items-start">
                    <div className="flex-shrink-0 mr-2 mt-1">
                      <div className="w-1.5 h-1.5 bg-blue-600 rounded-full"></div>
                    </div>
                    <p className="text-gray-700 text-sm">{suggestion}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Срочные вопросы */}
        {results.urgent_issues && results.urgent_issues.length > 0 && (
          <div className="mb-6">
            <h4 className="font-medium text-gray-900 mb-3 flex items-center">
              <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
              {isPostsAnalysis ? 'Требуют внимания' : 'Срочные вопросы'}
            </h4>
            <div className="space-y-3">
              {results.urgent_issues.map((urgentIssue: any, index: number) => (
                <div key={index} className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="font-medium text-red-800 mb-2">
                    {typeof urgentIssue === 'string' ? urgentIssue : urgentIssue.issue}
                  </p>
                  {urgentIssue.related_messages && urgentIssue.related_messages.length > 0 && (
                    <button
                      onClick={() => {
                        setSelectedIssue({
                          category: 'Срочное',
                          issue: typeof urgentIssue === 'string' ? urgentIssue : urgentIssue.issue,
                          frequency: urgentIssue.related_messages.length,
                          related_messages: urgentIssue.related_messages
                        });
                        setShowMessagesModal(true);
                      }}
                      className="text-sm text-red-600 hover:text-red-800 underline"
                    >
                      Посмотреть связанные {isPostsAnalysis ? 'комментарии' : 'сообщения'} ({urgentIssue.related_messages.length})
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Мета информация */}
        <div className="border-t pt-4 text-sm text-gray-500">
          <p>Анализ выполнен: {results.timestamp ? formatDate(results.timestamp) : 'Неизвестно'}</p>
          <p>
            {isPostsAnalysis 
              ? `Критерии: ${results.prompt || 'Не указаны'}`
              : `Критерии: ${results.prompt || 'Стандартный анализ настроений'}`
            }
          </p>
        </div>
      </div>

      {/* Модальное окно с сообщениями */}
      {showMessagesModal && selectedIssue && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-hidden">
            <div className="p-6 border-b">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-medium">
                    {isPostsAnalysis ? 'Комментарии по теме' : 'Сообщения по проблеме'}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {selectedIssue.category}: {selectedIssue.issue}
                  </p>
                </div>
                <button
                  onClick={() => setShowMessagesModal(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              <div className="space-y-4">
                {selectedIssue.related_messages?.map((message, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <div className="text-sm text-gray-600">
                        {message.author && <span className="font-medium">От: {message.author}</span>}
                        {message.author && <span className="mx-2">•</span>}
                        <span>{formatDate(message.date)}</span>
                        {/* НОВОЕ: Ссылка на пост для анализа постов */}
                        {isPostsAnalysis && message.post_link && (
                          <>
                            <span className="mx-2">•</span>
                            <a 
                              href={message.post_link} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800"
                            >
                              Пост
                            </a>
                          </>
                        )}
                      </div>
                    </div>
                    <p className="text-gray-800">{message.text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};