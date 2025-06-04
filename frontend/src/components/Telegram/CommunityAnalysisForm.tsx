import React, { useState } from 'react';
import { api } from '../../services/api';

interface CommunityAnalysisFormProps {
  groupId: string;
  onSuccess: (result: any) => void;
  onCancel: () => void;
}

export const CommunityAnalysisForm: React.FC<CommunityAnalysisFormProps> = ({ 
  groupId, 
  onSuccess,
  onCancel 
}) => {
  const [prompt, setPrompt] = useState('');
  const [daysBack, setDaysBack] = useState(7);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) {
      setError('Пожалуйста, введите критерии для анализа');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await api.post(`/telegram/groups/${groupId}/analyze-community`, {
        prompt,
        days_back: daysBack
      });

      if (response.data.status === 'success') {
        onSuccess(response.data.result);
      }
    } catch (err) {
      console.error('Ошибка анализа сообщества:', err);
      setError('Не удалось выполнить анализ. Попробуйте снова.');
    } finally {
      setIsLoading(false);
    }
  };

  // Готовые шаблоны промптов для ЖКХ
  const promptTemplates = [
    {
      title: "Общий анализ ЖКХ",
      prompt: "Проанализируй настроения жителей в отношении работы ЖКХ. Определи основные проблемы: уборка, отопление, водоснабжение, лифты, двор. Оцени удовлетворенность работой управляющей компании."
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

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium">Анализ Настроений Жителей</h3>
        <button
          onClick={onCancel}
          className="text-gray-500 hover:text-gray-700"
        >
          ✕
        </button>
      </div>
      
      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Быстрые шаблоны */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Быстрые шаблоны:
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {promptTemplates.map((template, index) => (
            <button
              key={index}
              type="button"
              onClick={() => setPrompt(template.prompt)}
              className="text-left p-2 border border-gray-300 rounded hover:bg-gray-50 text-sm"
            >
              <div className="font-medium text-indigo-600">{template.title}</div>
            </button>
          ))}
        </div>
      </div>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Критерии Анализа
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Опишите, что именно вы хотите проанализировать в сообщениях жителей..."
            className="w-full p-2 border border-gray-300 rounded"
            rows={4}
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Опишите фокус анализа: проблемы ЖКХ, качество услуг, настроения жителей
          </p>
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Период Анализа (дней)
          </label>
          <input
            type="number"
            value={daysBack}
            onChange={(e) => setDaysBack(parseInt(e.target.value))}
            min={1}
            max={30}
            className="w-full p-2 border border-gray-300 rounded"
          />
          <p className="text-xs text-gray-500 mt-1">
            Количество дней назад для анализа (1-30)
          </p>
        </div>
        
        <div className="flex space-x-3">
          <button
            type="submit"
            disabled={isLoading}
            className={`flex-1 px-4 py-2 rounded ${
              isLoading 
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-indigo-600 hover:bg-indigo-700 text-white'
            }`}
          >
            {isLoading ? 'Анализ...' : 'Анализировать Настроения'}
          </button>
          
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
          >
            Отмена
          </button>
        </div>
      </form>
    </div>
  );
};