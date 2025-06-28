// frontend/src/pages/SentimentAnalysisPage.tsx
import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowLeft, MessageSquare } from 'lucide-react';
import { useTelegramGroups } from '../hooks/useTelegramData';
import { CommunityAnalysisResults } from '../components/Telegram/CommunityAnalysisResults';
import { api } from '../services/api';

export const SentimentAnalysisPage: React.FC = () => {
  const { data: groups } = useTelegramGroups();
  const [searchParams] = useSearchParams();
  
  // Состояние формы
  const [selectedGroupId, setSelectedGroupId] = useState<string>('');
  const [prompt, setPrompt] = useState<string>('');
  const [daysBack, setDaysBack] = useState<number>(7);
  
  // Состояние анализа
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [showResults, setShowResults] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  // Предзаполнение группы из URL параметров
  useEffect(() => {
    const groupIdFromUrl = searchParams.get('groupId');
    if (groupIdFromUrl && groups?.some(g => g.id === groupIdFromUrl)) {
      setSelectedGroupId(groupIdFromUrl);
    }
  }, [searchParams, groups]);

  // Готовые шаблоны промптов для ЖКХ
  const promptTemplates = [
    {
      title: "Общий анализ ЖКХ",
      prompt: "Проанализируй общие настроения жителей по поводу ЖКХ услуг. Выяви основные проблемы и оцени удовлетворенность работой управляющей компании."
    },
    {
      title: "Проблемы двора",
      prompt: "Проанализируй жалобы жителей на состояние двора: парковка, детские площадки, освещение, уборка территории, зеленые насаждения."
    },
    {
      title: "Коммунальные услуги",
      prompt: "Проанализируй проблемы с коммунальными услугами: отопление, водоснабжение, электричество, интернет, мусоропровод."
    },
    {
      title: "Безопасность",
      prompt: "Проанализируй вопросы безопасности: работа домофона, видеонаблюдение, освещение, консьерж, посторонние лица."
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
      const response = await api.post(`/telegram/groups/${selectedGroupId}/analyze-community`, {
        prompt: prompt,
        days_back: daysBack
      });
      
      if (response.data.status === 'success') {
        setAnalysisResults(response.data.result);
        setShowResults(true);
      }
    } catch (err: any) {
      console.error('Ошибка анализа настроений:', err);
      const errorMessage = err.response?.data?.detail || 'Не удалось выполнить анализ. Попробуйте снова.';
      setError(errorMessage);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
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
          <div className="flex items-center justify-center w-16 h-16 bg-green-100 rounded-lg mb-4 mx-auto">
            <MessageSquare className="h-8 w-8 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Анализ Настроений Жителей
          </h1>
          <p className="text-lg text-gray-600">
            Анализ настроений и проблем жителей в ЖКХ группах
          </p>
        </div>

        {/* Результаты анализа */}
        {showResults && analysisResults && (
          <CommunityAnalysisResults 
            results={analysisResults}
            onHide={() => setShowResults(false)}
          />
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
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
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
                      className="p-3 text-left border border-gray-200 rounded-md hover:bg-green-50 hover:border-green-300 transition-colors"
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
                  placeholder="Опишите, что именно вы хотите проанализировать в сообщениях жителей..."
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
                  rows={4}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Опишите фокус анализа: проблемы ЖКХ, качество услуг, настроения жителей
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
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
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
                    : 'bg-green-600 hover:bg-green-700'
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