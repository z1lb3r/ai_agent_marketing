// frontend/src/pages/TelegramPage.tsx - ОБНОВЛЕННАЯ ВЕРСИЯ

import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { MessageSquare, BarChart2, Users, Clock, AlertCircle, Activity, TrendingUp, Settings } from 'lucide-react';
import { useTelegramGroups, useTelegramGroup, useAnalyzeGroup } from '../hooks/useTelegramData';
import { GroupList } from '../components/Telegram/GroupList';
import { LineChart } from '../components/Charts/LineChart';
import { DashboardCard } from '../components/Dashboard/DashboardCard';
import { MessageList } from '../components/Telegram/MessageList';
import { ModeratorList } from '../components/Telegram/ModeratorList';
import { SentimentAnalysis } from '../components/Telegram/SentimentAnalysis';
import { CommunityAnalysisForm } from '../components/Telegram/CommunityAnalysisForm';
import { CommunityAnalysisResults } from '../components/Telegram/CommunityAnalysisResults';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';

// Типы анализа
type AnalysisType = 'moderators' | 'community';

export const TelegramPage: React.FC = () => {
  const { groupId } = useParams<{ groupId: string }>();
  const queryClient = useQueryClient();
  const { data: groups } = useTelegramGroups();
  const { data: group, isLoading: isLoadingGroup } = useTelegramGroup(groupId || '');
  const analyzeGroupMutation = useAnalyzeGroup();
  
  // Состояние для выбора типа анализа
  const [analysisType, setAnalysisType] = useState<AnalysisType>('moderators');
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [communityResults, setCommunityResults] = useState<any>(null);
  const [showAnalysisDetails, setShowAnalysisDetails] = useState<boolean>(false);
  const [showCommunityDetails, setShowCommunityDetails] = useState<boolean>(false);
  
  // Состояние для формы добавления группы
  const [showAddGroupForm, setShowAddGroupForm] = useState<boolean>(false);
  const [groupLink, setGroupLink] = useState<string>('');
  const [moderators, setModerators] = useState<string>('');
  const [addingGroup, setAddingGroup] = useState<boolean>(false);
  const [addGroupError, setAddGroupError] = useState<string>('');
  
  // Состояние для форм анализа
  const [showAnalysisForm, setShowAnalysisForm] = useState<boolean>(false);
  const [showCommunityForm, setShowCommunityForm] = useState<boolean>(false);
  const [prompt, setPrompt] = useState<string>('');
  const [selectedModerators, setSelectedModerators] = useState<string[]>([]);
  const [daysBack, setDaysBack] = useState<number>(7);

  // Обработчик для запуска анализа модераторов
  const handleModeratorAnalysis = async () => {
    if (!groupId) return;
    if (!prompt.trim()) {
      alert("Пожалуйста, введите критерии для анализа");
      return;
    }
    
    console.log("Запуск анализа модераторов для группы:", groupId);
    setAnalyzing(true);
    
    try {
      const response = await api.post(`/telegram/groups/${groupId}/analyze`, {
        prompt: prompt,
        moderators: selectedModerators,
        days_back: daysBack
      });
      
      console.log("Ответ API анализа модераторов:", response.data);
      
      setAnalysisResults(response.data.result);
      setShowAnalysisDetails(true);
      setShowAnalysisForm(false);
      
      queryClient.invalidateQueries({ queryKey: ['telegram-groups'] });
    } catch (error) {
      console.error('Ошибка анализа модераторов:', error);
      alert('Ошибка анализа модераторов. Попробуйте снова.');
    } finally {
      setAnalyzing(false);
    }
  };

  // Обработчик для запуска анализа сообщества
  const handleCommunityAnalysis = (result: any) => {
    setCommunityResults(result);
    setShowCommunityDetails(true);
    setShowCommunityForm(false);
  };
  
  // Обработчик для добавления новой группы
  const handleAddGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupLink.trim()) {
      setAddGroupError("Пожалуйста, введите ссылку или username группы");
      return;
    }
    
    setAddingGroup(true);
    setAddGroupError('');
    
    try {
      const moderatorsList = moderators
        .split(',')
        .map(m => m.trim())
        .filter(m => m.length > 0);
      
      const response = await api.get(`/telegram/groups_add`, {
        params: { 
          group_link: groupLink,
          moderators: moderatorsList.join(',')
        }
      });
      
      if (response.data.status === 'success' || response.data.status === 'already_exists') {
        setGroupLink('');
        setModerators('');
        setShowAddGroupForm(false);
        
        queryClient.invalidateQueries({ queryKey: ['telegram-groups'] });
      } else {
        setAddGroupError("Не удалось добавить группу. Попробуйте снова.");
      }
    } catch (error) {
      console.error('Ошибка добавления группы:', error);
      setAddGroupError("Ошибка добавления группы. Проверьте ссылку и попробуйте снова.");
    } finally {
      setAddingGroup(false);
    }
  };

  // Функция для сброса состояния при переключении типа анализа
  const handleAnalysisTypeChange = (type: AnalysisType) => {
    setAnalysisType(type);
    setShowAnalysisForm(false);
    setShowCommunityForm(false);
    setShowAnalysisDetails(false);
    setShowCommunityDetails(false);
    setPrompt('');
  };

  // Если groupId не указан, показываем список групп
  if (!groupId) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center mb-8">
            <h1 className="text-2xl font-semibold text-gray-900">
              Telegram Группы
            </h1>
            <button
              onClick={() => setShowAddGroupForm(!showAddGroupForm)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md"
            >
              {showAddGroupForm ? 'Отмена' : 'Добавить Группу'}
            </button>
          </div>
          
          {/* Форма добавления группы */}
          {showAddGroupForm && (
            <div className="bg-white shadow rounded-lg p-6 mb-8">
              <h3 className="text-lg font-medium mb-4">Добавить Telegram Группу</h3>
              
              {addGroupError && (
                <div className="bg-red-50 text-red-700 p-3 rounded mb-4">
                  {addGroupError}
                </div>
              )}
              
              <form onSubmit={handleAddGroup}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ссылка на группу или Username
                  </label>
                  <input
                    type="text"
                    value={groupLink}
                    onChange={(e) => setGroupLink(e.target.value)}
                    placeholder="t.me/groupname или @groupname"
                    className="w-full p-2 border border-gray-300 rounded"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Введите ссылку на Telegram группу или username
                  </p>
                </div>
                
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Модераторы
                  </label>
                  <input
                    type="text"
                    value={moderators}
                    onChange={(e) => setModerators(e.target.value)}
                    placeholder="@moderator1, @moderator2"
                    className="w-full p-2 border border-gray-300 rounded"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Введите username модераторов через запятую
                  </p>
                </div>
                
                <button
                  type="submit"
                  disabled={addingGroup}
                  className={`px-4 py-2 rounded ${
                    addingGroup 
                      ? 'bg-gray-400 cursor-not-allowed' 
                      : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                  }`}
                >
                  {addingGroup ? 'Добавление...' : 'Добавить Группу'}
                </button>
              </form>
            </div>
          )}
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <GroupList />
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium mb-4">Как использовать</h3>
              <p className="text-gray-600 mb-4">
                Этот модуль помогает анализировать Telegram группы для оценки работы модераторов 
                и анализа настроений сообщества.
              </p>
              <div className="space-y-3">
                <div className="flex items-start">
                  <div className="bg-indigo-100 p-2 rounded-full mr-3 mt-0.5">
                    <span className="text-indigo-700 font-bold">1</span>
                  </div>
                  <p className="text-gray-600">
                    Добавьте Telegram группу, указав ссылку или username
                  </p>
                </div>
                <div className="flex items-start">
                  <div className="bg-indigo-100 p-2 rounded-full mr-3 mt-0.5">
                    <span className="text-indigo-700 font-bold">2</span>
                  </div>
                  <p className="text-gray-600">
                    Выберите тип анализа и введите критерии оценки
                  </p>
                </div>
                <div className="flex items-start">
                  <div className="bg-indigo-100 p-2 rounded-full mr-3 mt-0.5">
                    <span className="text-indigo-700 font-bold">3</span>
                  </div>
                  <p className="text-gray-600">
                    Изучите результаты анализа и рекомендации
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
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Группа не найдена</h2>
            <p className="text-lg text-gray-600 mb-6">
              Telegram группа, которую вы ищете, не найдена. Возможно, она была удалена или у вас нет доступа.
            </p>
            <Link 
              to="/telegram" 
              className="inline-block px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md"
            >
              Вернуться к группам
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Получаем список модераторов из настроек группы
  const groupModerators = group.settings?.moderators || [];

  // Мок-данные для демонстрации
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
      avgResponse: '4.5 мин',
      resolved: 43,
      satisfaction: '92%',
      activeTime: '8.5 часов'
    }
  };

  // Определяем какие результаты показывать в метриках
  const currentResults = analysisType === 'moderators' ? analysisResults : communityResults;

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-2xl font-semibold text-gray-900">
            {group.name}
          </h1>
          
          <div className="flex items-center space-x-4">
            <Link 
              to="/telegram" 
              className="text-indigo-600 hover:text-indigo-800"
            >
              Ко всем группам
            </Link>
          </div>
        </div>

        {/* Переключатель типов анализа */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h3 className="text-lg font-medium mb-4">Тип Анализа</h3>
          
          <div className="flex space-x-4 mb-6">
            <button
              onClick={() => handleAnalysisTypeChange('moderators')}
              className={`flex items-center px-4 py-2 rounded-md ${
                analysisType === 'moderators'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              <Users className="h-5 w-5 mr-2" />
              Анализ Модераторов
            </button>
            
            <button
              onClick={() => handleAnalysisTypeChange('community')}
              className={`flex items-center px-4 py-2 rounded-md ${
                analysisType === 'community'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              <MessageSquare className="h-5 w-5 mr-2" />
              Анализ Настроений Жителей
            </button>
          </div>

          <div className="text-sm text-gray-600 mb-4">
            {analysisType === 'moderators' 
              ? 'Анализ эффективности работы модераторов группы'
              : 'Анализ настроений жителей и проблем ЖКХ'
            }
          </div>

          {/* Кнопки запуска анализа */}
          <div className="flex space-x-3">
            {analysisType === 'moderators' ? (
              <button 
                onClick={() => setShowAnalysisForm(!showAnalysisForm)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md"
                disabled={analyzing}
              >
                {showAnalysisForm ? 'Отмена' : 'Новый Анализ Модераторов'}
              </button>
            ) : (
              <button 
                onClick={() => setShowCommunityForm(!showCommunityForm)}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-md"
                disabled={analyzing}
              >
                {showCommunityForm ? 'Отмена' : 'Анализ Настроений Жителей'}
              </button>
            )}
          </div>
        </div>
        
        {/* Форма анализа модераторов */}
        {showAnalysisForm && analysisType === 'moderators' && (
          <div className="bg-white shadow rounded-lg p-6 mb-8">
            <h3 className="text-lg font-medium mb-4">Анализ Модераторов</h3>
            <form onSubmit={(e) => { e.preventDefault(); handleModeratorAnalysis(); }}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Критерии Анализа
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Опишите критерии для оценки работы модераторов..."
                  className="w-full p-3 border border-gray-300 rounded-md"
                  rows={4}
                  required
                ></textarea>
                <p className="text-xs text-gray-500 mt-1">
                  Определите, как должны вести себя модераторы и какие критерии использовать для оценки
                </p>
              </div>
              
              {groupModerators.length > 0 && (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Модераторы для Анализа
                  </label>
                  <div className="space-y-2">
                    {groupModerators.map((mod) => (
                      <label key={mod} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedModerators.includes(mod)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedModerators([...selectedModerators, mod]);
                            } else {
                              setSelectedModerators(selectedModerators.filter(m => m !== mod));
                            }
                          }}
                          className="mr-2"
                        />
                        {mod}
                      </label>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Дней для Анализа
                </label>
                <input
                  type="number"
                  value={daysBack}
                  onChange={(e) => setDaysBack(parseInt(e.target.value))}
                  min={1}
                  max={30}
                  className="w-full p-2 border border-gray-300 rounded-md"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Количество дней назад для анализа (1-30)
                </p>
              </div>
              
              <button
                type="submit"
                disabled={analyzing}
                className={`px-4 py-2 rounded-md ${
                  analyzing 
                    ? 'bg-gray-300 cursor-not-allowed' 
                    : 'bg-indigo-600 hover:bg-indigo-700 text-white'
                }`}
              >
                {analyzing ? 'Анализ...' : 'Запустить Анализ'}
              </button>
            </form>
          </div>
        )}

        {/* Форма анализа сообщества */}
        {showCommunityForm && analysisType === 'community' && (
          <CommunityAnalysisForm
            groupId={groupId}
            onSuccess={handleCommunityAnalysis}
            onCancel={() => setShowCommunityForm(false)}
          />
        )}
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
          <DashboardCard
            title="Участников"
            value={group.settings?.members_count || 0}
            icon={<Users className="h-6 w-6 text-blue-600" />}
          />
          <DashboardCard
            title={analysisType === 'moderators' ? "Ср. Время Ответа" : "Удовлетворенность"}
            value={analysisType === 'moderators' 
              ? (currentResults?.summary?.response_time_avg ? `${currentResults.summary.response_time_avg} мин` : mockData.moderatorStats.avgResponse)
              : (currentResults?.sentiment_summary?.satisfaction_score ? `${currentResults.sentiment_summary.satisfaction_score}%` : "Н/Д")
            }
            icon={<Clock className="h-6 w-6 text-yellow-600" />}
          />
          <DashboardCard
            title={analysisType === 'moderators' ? "Решено Вопросов" : "Уровень Жалоб"}
            value={analysisType === 'moderators'
              ? (currentResults?.summary?.resolved_issues || mockData.moderatorStats.resolved)
              : (currentResults?.sentiment_summary?.complaint_level || "Н/Д")
            }
            icon={<BarChart2 className="h-6 w-6 text-green-600" />}
          />
          <DashboardCard
            title={analysisType === 'moderators' ? "Удовлетворенность" : "Общее Настроение"}
            value={analysisType === 'moderators'
              ? (currentResults?.summary?.satisfaction_score ? `${currentResults.summary.satisfaction_score}%` : mockData.moderatorStats.satisfaction)
              : (currentResults?.sentiment_summary?.overall_mood || "Н/Д")
            }
            icon={<MessageSquare className="h-6 w-6 text-purple-600" />}
          />
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <LineChart 
            data={mockData.responseTime}
            dataKey="value"
            xAxisKey="date"
            title={analysisType === 'moderators' ? "Тренд Времени Ответа (минуты)" : "Динамика Настроений"}
            color="#3b82f6"
          />
          
          <SentimentAnalysis 
            groupId={groupId}
            analysisResults={analysisType === 'moderators' ? analysisResults : null}  // ← ИСПРАВЛЕНИЕ
            isAnalyzing={analyzing}
            onAnalyze={() => analysisType === 'moderators' ? setShowAnalysisForm(true) : setShowCommunityForm(true)}
          />
        </div>
        
        {/* Результаты анализа модераторов */}
        {analysisResults && showAnalysisDetails && analysisType === 'moderators' && (
          <div className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Результаты Анализа Модераторов</h2>
              <button 
                onClick={() => setShowAnalysisDetails(!showAnalysisDetails)}
                className="text-indigo-600 hover:text-indigo-800"
              >
                {showAnalysisDetails ? 'Скрыть Детали' : 'Показать Детали'}
              </button>
            </div>
            
            {/* Подробные результаты анализа модераторов (существующий код) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Сентимент */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium mb-4">Анализ Настроений</h3>
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="bg-green-50 p-4 rounded-lg text-center">
                    <p className="text-sm text-gray-500">Позитивные</p>
                    <p className="text-2xl font-semibold text-green-600">
                      {analysisResults.moderator_metrics?.sentiment?.positive || 0}%
                    </p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg text-center">
                    <p className="text-sm text-gray-500">Нейтральные</p>
                    <p className="text-2xl font-semibold text-gray-600">
                      {analysisResults.moderator_metrics?.sentiment?.neutral || 0}%
                    </p>
                  </div>
                  <div className="bg-red-50 p-4 rounded-lg text-center">
                    <p className="text-sm text-gray-500">Негативные</p>
                    <p className="text-2xl font-semibold text-red-600">
                      {analysisResults.moderator_metrics?.sentiment?.negative || 0}%
                    </p>
                  </div>
                </div>
              </div>

              {/* Модераторы */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-medium mb-4">Эффективность Модераторов</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between mb-1">
                      <p className="text-sm text-gray-600">Эффективность</p>
                      <p className="text-sm font-medium">{analysisResults.moderator_metrics?.performance?.effectiveness || 0}%</p>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-green-500 h-2 rounded-full" 
                        style={{ width: `${analysisResults.moderator_metrics?.performance?.effectiveness || 0}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Результаты анализа сообщества */}
        {communityResults && showCommunityDetails && analysisType === 'community' && (
          <CommunityAnalysisResults
            results={communityResults}
            onHide={() => setShowCommunityDetails(false)}
          />
        )}
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <MessageList groupId={groupId} />
          <ModeratorList groupId={groupId} />
        </div>
      </div>
    </div>
  );
};