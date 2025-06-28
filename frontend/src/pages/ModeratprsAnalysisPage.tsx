// frontend/src/pages/ModeratorsAnalysisPage.tsx
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Users, Settings } from 'lucide-react';
import { useTelegramGroups } from '../hooks/useTelegramData';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';

export const ModeratorsAnalysisPage: React.FC = () => {
  const { data: groups } = useTelegramGroups();
  const queryClient = useQueryClient();
  
  // Состояние формы
  const [selectedGroupId, setSelectedGroupId] = useState<string>('');
  const [prompt, setPrompt] = useState<string>('');
  const [selectedModerators, setSelectedModerators] = useState<string[]>([]);
  const [daysBack, setDaysBack] = useState<number>(7);
  
  // Состояние анализа
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [showResults, setShowResults] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  // Получаем выбранную группу
  const selectedGroup = groups?.find(g => g.id === selectedGroupId);
  const groupModerators = selectedGroup?.settings?.moderators || [];

  // Готовые шаблоны промптов
  const promptTemplates = [
    {
      title: "Общая эффективность",
      prompt: "Оцени общую эффективность модераторов: время ответа, качество решений, профессионализм общения с жителями."
    },
    {
      title: "Скорость реагирования",
      prompt: "Проанализируй скорость реагирования модераторов на вопросы и проблемы жителей. Выяви задержки и их причины."
    },
    {
      title: "Качество решений",
      prompt: "Оцени качество решений модераторов: полнота ответов, корректность информации, помощь в решении проблем."
    },
    {
      title: "Стиль общения",
      prompt: "Проанализируй стиль общения модераторов с жителями: вежливость, понятность объяснений, эмпатия."
    }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedGroupId) {
      setError('Пожалуйста, выберите группу для анализа');
      return;
    }
    
    if (!prompt.trim()) {
      setError('Пожалуйста, введите критерии для анализа');
      return;
    }
    
    setAnalyzing(true);
    setError('');
    
    try {
      const response = await api.post(`/telegram/groups/${selectedGroupId}/analyze`, {
        prompt: prompt,
        moderators: selectedModerators,
        days_back: daysBack
      });
      
      setAnalysisResults(response.data.result);
      setShowResults(true);
      queryClient.invalidateQueries({ queryKey: ['telegram-groups'] });
    } catch (err: any) {
      console.error('Ошибка анализа модераторов:', err);
      const errorMessage = err.response?.data?.detail || 'Не удалось выполнить анализ. Попробуйте снова.';
      setError(errorMessage);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Хлебные крошки */}
        <div className="flex items-center mb-8">
          <Link
            to="/telegram"
            className="flex items-center text-indigo-600 hover:text-indigo-800"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Назад к выбору анализа
          </Link>
        </div>

        {/* Заголовок */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center w-16 h-16 bg-indigo-100 rounded-lg mb-4 mx-auto">
            <Users className="h-8 w-8 text-indigo-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Анализ Модераторов
          </h1>
          <p className="text-lg text-gray-600">
            Оценка эффективности работы модераторов в Telegram группах
          </p>
        </div>

        {/* Результаты анализа */}
        {showResults && analysisResults && (
          <div className="bg-white shadow rounded-lg p-6 mb-8">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium">Результаты Анализа Модераторов</h3>
              <button
                onClick={() => setShowResults(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">Общая Оценка</h4>
                <p className="text-gray-700">{analysisResults.summary?.overall_assessment || 'Нет данных'}</p>
              </div>
              
              {analysisResults.moderator_performance && (
                <div>
                  <h4 className="font-medium mb-2">Производительность Модераторов</h4>
                  <div className="space-y-2">
                    {analysisResults.moderator_performance.map((mod: any, index: number) => (
                      <div key={index} className="flex justify-between">
                        <span>{mod.name}</span>
                        <span className="font-medium">{mod.score}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {analysisResults.recommendations && (
                <div>
                  <h4 className="font-medium mb-2">Рекомендации</h4>
                  <ul className="space-y-1">
                    {analysisResults.recommendations.map((rec: string, index: number) => (
                      <li key={index} className="text-gray-700">• {rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Форма анализа */}
        <div className="bg-white shadow rounded-lg p-6">
          <form onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* Выбор группы */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Выберите группу для анализа
              </label>
              <select
                value={selectedGroupId}
                onChange={(e) => setSelectedGroupId(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                required
              >
                <option value="">-- Выберите группу --</option>
                {groups?.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name}
                  </option>
                ))}
              </select>
              {!groups?.length && (
                <p className="text-sm text-gray-500 mt-2">
                  Нет доступных групп.{' '}
                  <Link to="/telegram/groups" className="text-indigo-600 hover:text-indigo-800">
                    Добавить группу
                  </Link>
                </p>
              )}
            </div>

            {/* Шаблоны промптов */}
            {selectedGroupId && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Готовые шаблоны анализа
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {promptTemplates.map((template, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => setPrompt(template.prompt)}
                      className="p-3 text-left border border-gray-200 rounded-md hover:bg-indigo-50 hover:border-indigo-300 transition-colors"
                    >
                      <div className="font-medium text-sm text-gray-900 mb-1">
                        {template.title}
                      </div>
                      <div className="text-xs text-gray-600 line-clamp-2">
                        {template.prompt}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Критерии анализа */}
            {selectedGroupId && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Критерии анализа
                </label>
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="Опишите критерии для анализа эффективности модераторов..."
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  rows={4}
                  required
                />
              </div>
            )}

            {/* Выбор модераторов */}
            {selectedGroupId && groupModerators.length > 0 && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Модераторы для анализа
                </label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {groupModerators.map((moderator: string, index: number) => (
                    <label key={index} className="flex items-center p-3 border border-gray-200 rounded-md hover:bg-gray-50">
                      <input
                        type="checkbox"
                        checked={selectedModerators.includes(moderator)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedModerators([...selectedModerators, moderator]);
                          } else {
                            setSelectedModerators(selectedModerators.filter(m => m !== moderator));
                          }
                        }}
                        className="mr-3 h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                      />
                      <span className="text-sm text-gray-700">{moderator}</span>
                    </label>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Оставьте пустым для анализа всех модераторов
                </p>
              </div>
            )}

            {/* Период анализа */}
            {selectedGroupId && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Период анализа (дней назад)
                </label>
                <input
                  type="number"
                  value={daysBack}
                  onChange={(e) => setDaysBack(parseInt(e.target.value))}
                  min={1}
                  max={30}
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Количество дней назад для анализа (1-30)
                </p>
              </div>
            )}

            {/* Кнопка отправки */}
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={analyzing || !selectedGroupId}
                className={`px-6 py-3 rounded-md text-white font-medium ${
                  analyzing || !selectedGroupId
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-indigo-600 hover:bg-indigo-700'
                }`}
              >
                {analyzing ? 'Анализ...' : 'Запустить Анализ'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};