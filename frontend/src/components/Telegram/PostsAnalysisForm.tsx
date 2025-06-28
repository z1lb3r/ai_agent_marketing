// frontend/src/components/Telegram/PostsAnalysisForm.tsx

import React, { useState } from 'react';
import { api } from '../../services/api';
import { X, Plus, LinkIcon, MessageSquare, Users, AlertCircle } from 'lucide-react';

interface PostsAnalysisFormProps {
  groupId: string;
  onSuccess: (result: any) => void;
  onCancel?: () => void;
}

export const PostsAnalysisForm: React.FC<PostsAnalysisFormProps> = ({ 
  groupId, 
  onSuccess,
  onCancel 
}) => {
  const [prompt, setPrompt] = useState('');
  const [postLinks, setPostLinks] = useState<string[]>(['']);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Валидация
    if (!prompt.trim()) {
      setError('Пожалуйста, введите критерии для анализа');
      return;
    }

    const validLinks = postLinks.filter(link => link.trim());
    if (validLinks.length === 0) {
      setError('Пожалуйста, добавьте хотя бы одну ссылку на пост');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await api.post(`/telegram/groups/${groupId}/analyze-posts`, {
        prompt,
        post_links: validLinks
      });

      if (response.data.status === 'success') {
        onSuccess(response.data.result);
      }
    } catch (err: any) {
      console.error('Ошибка анализа комментариев к постам:', err);
      const errorMessage = err.response?.data?.detail || 'Не удалось выполнить анализ. Попробуйте снова.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const addPostLink = () => {
    setPostLinks([...postLinks, '']);
  };

  const removePostLink = (index: number) => {
    if (postLinks.length > 1) {
      setPostLinks(postLinks.filter((_, i) => i !== index));
    }
  };

  const updatePostLink = (index: number, value: string) => {
    const newLinks = [...postLinks];
    newLinks[index] = value;
    setPostLinks(newLinks);
  };

  // Готовые шаблоны промптов для анализа комментариев к постам
  const promptTemplates = [
    {
      title: "Общий анализ реакций",
      prompt: "Проанализируй реакции жителей на пост. Определи общие настроения, основные темы обсуждения, поддержку или критику. Выяви конструктивные предложения."
    },
    {
      title: "Анализ объявлений УК",
      prompt: "Проанализируй реакции на объявление управляющей компании. Оцени уровень понимания, поддержки, вопросов и недовольства жителей."
    },
    {
      title: "Реакции на изменения",
      prompt: "Проанализируй комментарии к посту об изменениях (тарифы, правила, ремонт). Определи уровень принятия изменений жителями."
    },
    {
      title: "Обратная связь по проектам",
      prompt: "Проанализируй мнения жителей о предлагаемых проектах благоустройства. Выяви популярные идеи и опасения."
    }
  ];

  const isValidTelegramLink = (link: string) => {
    const telegramLinkPattern = /^(https?:\/\/)?(t\.me\/)[^\/]+\/\d+$/;
    return telegramLinkPattern.test(link.trim());
  };

  return (
    <div className="bg-white shadow rounded-lg p-6 mb-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-lg font-medium">Анализ Комментариев к Постам</h3>
          <p className="text-sm text-gray-600 mt-1">
            Анализ реакций и обратной связи на конкретные посты
          </p>
        </div>
        <button
          onClick={onCancel}
          className="text-gray-400 hover:text-gray-600"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400 mr-2 mt-0.5" />
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* Ссылки на посты */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Ссылки на посты для анализа
          </label>
          
          <div className="space-y-3">
            {postLinks.map((link, index) => (
              <div key={index} className="flex space-x-2">
                <div className="flex-1">
                  <div className="relative">
                    <LinkIcon className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                    <input
                      type="url"
                      value={link}
                      onChange={(e) => updatePostLink(index, e.target.value)}
                      placeholder="https://t.me/channel_name/123 или https://t.me/c/1234567890/456"
                      className={`w-full pl-10 pr-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500 ${
                        link.trim() && !isValidTelegramLink(link) 
                          ? 'border-red-300 bg-red-50' 
                          : 'border-gray-300'
                      }`}
                    />
                  </div>
                  {link.trim() && !isValidTelegramLink(link) && (
                    <p className="text-xs text-red-600 mt-1">
                      Неверный формат ссылки на Telegram пост
                    </p>
                  )}
                </div>
                
                {postLinks.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removePostLink(index)}
                    className="px-3 py-2 text-red-600 hover:text-red-800 border border-red-300 rounded-md"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={addPostLink}
            className="mt-3 flex items-center text-sm text-purple-600 hover:text-purple-800"
          >
            <Plus className="h-4 w-4 mr-1" />
            Добавить еще пост
          </button>

          <div className="mt-2 text-xs text-gray-500">
            <p>Поддерживаемые форматы:</p>
            <ul className="list-disc list-inside ml-2 mt-1">
              <li>https://t.me/channel_name/123 (публичные каналы)</li>
              <li>https://t.me/c/1234567890/456 (приватные каналы/группы)</li>
            </ul>
          </div>
        </div>

        {/* Шаблоны промптов */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Готовые шаблоны анализа
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {promptTemplates.map((template, index) => (
              <button
                key={index}
                type="button"
                onClick={() => setPrompt(template.prompt)}
                className="p-3 text-left border border-gray-200 rounded-md hover:bg-purple-50 hover:border-purple-300 transition-colors"
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

        {/* Кастомный промпт */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Или введите свои критерии анализа
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Опишите что именно нужно анализировать в комментариях к постам..."
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-purple-500 focus:border-purple-500"
            rows={4}
          />
          <p className="text-xs text-gray-500 mt-2">
            Например: "Определи отношение жителей к предлагаемому ремонту лифтов, выяви основные опасения и предложения"
          </p>
        </div>

        {/* Информация о функции */}
        <div className="bg-purple-50 border border-purple-200 rounded-md p-4 mb-6">
          <div className="flex">
            <MessageSquare className="h-5 w-5 text-purple-600 mr-2 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-purple-900 mb-1">
                Как работает анализ комментариев к постам
              </h4>
              <ul className="text-xs text-purple-700 space-y-1">
                <li>• Система собирает все комментарии к указанным постам</li>
                <li>• ИИ анализирует настроения и основные темы обсуждения</li>
                <li>• Применяется фильтрация значимых проблем (7% правило)</li>
                <li>• Результат показывает конкретные комментарии по каждой теме</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Кнопки */}
        <div className="flex space-x-3">
          <button
            type="submit"
            disabled={isLoading || !prompt.trim() || postLinks.filter(link => link.trim()).length === 0}
            className={`flex-1 py-2 px-4 rounded-md ${
              isLoading || !prompt.trim() || postLinks.filter(link => link.trim()).length === 0
                ? 'bg-gray-400 cursor-not-allowed' 
                : 'bg-purple-600 hover:bg-purple-700 text-white'
            }`}
          >
            {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Анализ комментариев...
              </div>
            ) : (
              'Анализировать Комментарии'
            )}
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