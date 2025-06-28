// frontend/src/pages/PostsAnalysisPage.tsx
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, LinkIcon } from 'lucide-react';
import { PostsAnalysisForm } from '../components/Telegram/PostsAnalysisForm';
import { CommunityAnalysisResults } from '../components/Telegram/CommunityAnalysisResults';

export const PostsAnalysisPage: React.FC = () => {
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [showResults, setShowResults] = useState<boolean>(false);

  const handleAnalysisSuccess = (result: any) => {
    setAnalysisResults(result);
    setShowResults(true);
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
          <div className="flex items-center justify-center w-16 h-16 bg-purple-100 rounded-lg mb-4 mx-auto">
            <LinkIcon className="h-8 w-8 text-purple-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Анализ Комментариев к Постам
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Анализ реакций и обратной связи на конкретные посты, объявления и сообщения в Telegram
          </p>
        </div>

        {/* Информационный блок */}
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-6 mb-8">
          <h3 className="text-lg font-semibold text-purple-900 mb-3">
            Особенности анализа постов
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-purple-800">
            <div>
              <h4 className="font-medium mb-2">✅ Преимущества</h4>
              <ul className="space-y-1">
                <li>• Анализ реакций на конкретные объявления</li>
                <li>• Посты могут быть из разных групп</li>
                <li>• Детальная обратная связь от жителей</li>
                <li>• Оценка эффективности коммуникации</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-2">⚠️ Требования</h4>
              <ul className="space-y-1">
                <li>• Доступ к комментариям поста</li>
                <li>• Валидные ссылки на Telegram посты</li>
                <li>• Посты должны иметь включенные комментарии</li>
                <li>• Бот должен иметь доступ к каналу/группе</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Результаты анализа */}
        {showResults && analysisResults && (
          <CommunityAnalysisResults 
            results={analysisResults}
            onHide={() => setShowResults(false)}
            isPostsAnalysis={true}
          />
        )}

        {/* Форма анализа */}
        <PostsAnalysisForm
          groupId="" // Для анализа постов groupId не нужен
          onSuccess={handleAnalysisSuccess}
          // onCancel не нужен на отдельной странице
        />

        {/* Дополнительная информация */}
        <div className="mt-8 bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Как использовать анализ постов
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-gray-700">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">1. Подготовьте ссылки</h4>
              <p>Скопируйте ссылки на посты, комментарии к которым хотите проанализировать. Поддерживаются публичные и приватные каналы.</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">2. Выберите шаблон</h4>
              <p>Используйте готовые шаблоны анализа или создайте собственные критерии в зависимости от целей исследования.</p>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">3. Получите результаты</h4>
              <p>Изучите детальный анализ реакций, настроений и ключевых тем обсуждения в комментариях к постам.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};