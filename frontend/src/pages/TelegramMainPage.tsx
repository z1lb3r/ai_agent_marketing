// frontend/src/pages/TelegramMainPage.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { Users, MessageSquare, LinkIcon, Settings } from 'lucide-react';

export const TelegramMainPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Анализ Telegram
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Выберите тип анализа для получения детальной информации о коммуникациях в Telegram
          </p>
        </div>

        {/* Основные типы анализа */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          {/* Анализ модераторов */}
          <Link
            to="/telegram/analyze/moderators"
            className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow duration-300 border border-gray-200 hover:border-indigo-300"
          >
            <div className="flex items-center justify-center w-16 h-16 bg-indigo-100 rounded-lg mb-4 mx-auto">
              <Users className="h-8 w-8 text-indigo-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 text-center mb-3">
              Анализ Модераторов
            </h3>
            <p className="text-gray-600 text-center mb-4">
              Оценка эффективности работы модераторов: время ответа, качество общения, решение проблем
            </p>
            <div className="text-center">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                Требует выбор группы
              </span>
            </div>
          </Link>

          {/* Анализ настроений */}
          <Link
            to="/telegram/analyze/sentiment"
            className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow duration-300 border border-gray-200 hover:border-green-300"
          >
            <div className="flex items-center justify-center w-16 h-16 bg-green-100 rounded-lg mb-4 mx-auto">
              <MessageSquare className="h-8 w-8 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 text-center mb-3">
              Настроения Жителей
            </h3>
            <p className="text-gray-600 text-center mb-4">
              Анализ настроений жителей ЖКХ: проблемы, жалобы, уровень удовлетворенности, предложения
            </p>
            <div className="text-center">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                Требует выбор группы
              </span>
            </div>
          </Link>

          {/* Анализ комментариев к постам */}
          <Link
            to="/telegram/analyze/posts"
            className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow duration-300 border border-gray-200 hover:border-purple-300"
          >
            <div className="flex items-center justify-center w-16 h-16 bg-purple-100 rounded-lg mb-4 mx-auto">
              <LinkIcon className="h-8 w-8 text-purple-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 text-center mb-3">
              Комментарии к Постам
            </h3>
            <p className="text-gray-600 text-center mb-4">
              Анализ реакций и обратной связи на конкретные посты, объявления и сообщения
            </p>
            <div className="text-center">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                Без привязки к группе
              </span>
            </div>
          </Link>
        </div>

        {/* Управление группами */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="flex items-center justify-center w-12 h-12 bg-gray-100 rounded-lg mr-4">
                <Settings className="h-6 w-6 text-gray-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Управление Группами
                </h3>
                <p className="text-gray-600">
                  Добавление, настройка и обзор подключенных Telegram групп
                </p>
              </div>
            </div>
            <Link
              to="/telegram/groups"
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-md transition-colors"
            >
              Управление группами
            </Link>
          </div>
        </div>

        {/* Дополнительная информация */}
        <div className="mt-12 text-center">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h4 className="text-lg font-semibold text-blue-900 mb-3">
              Как начать работу
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-blue-800">
              <div>
                <div className="font-medium mb-2">1. Настройте группы</div>
                <div>Добавьте Telegram группы, которые хотите анализировать</div>
              </div>
              <div>
                <div className="font-medium mb-2">2. Выберите анализ</div>
                <div>Определите тип анализа в зависимости от ваших целей</div>
              </div>
              <div>
                <div className="font-medium mb-2">3. Получите результаты</div>
                <div>Изучите детальные отчеты и рекомендации</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};