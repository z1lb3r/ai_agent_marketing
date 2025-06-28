// frontend/src/pages/TelegramGroupPage.tsx
import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Users, MessageSquare, LinkIcon, Clock, BarChart2, Settings } from 'lucide-react';
import { useTelegramGroup } from '../hooks/useTelegramData';
import { DashboardCard } from '../components/Dashboard/DashboardCard';

export const TelegramGroupPage: React.FC = () => {
  const { groupId } = useParams<{ groupId: string }>();
  const { data: group, isLoading: isLoadingGroup } = useTelegramGroup(groupId || '');

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
            <div className="bg-white h-80 rounded-lg shadow mb-8"></div>
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
              Telegram группа, которую вы ищете, не найдена.
              Возможно, она была удалена или у вас нет доступа.
            </p>
            <Link 
              to="/telegram/groups" 
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

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Хлебные крошки */}
        <div className="flex items-center mb-8">
          <Link
            to="/telegram/groups"
            className="flex items-center text-indigo-600 hover:text-indigo-800"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Назад к группам
          </Link>
        </div>

        {/* Заголовок */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              {group.name}
            </h1>
            <p className="text-lg text-gray-600 mt-1">
              Обзор группы и быстрый доступ к анализу
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            <Link 
              to="/telegram/groups" 
              className="text-indigo-600 hover:text-indigo-800"
            >
              Все группы
            </Link>
          </div>
        </div>
        
        {/* Метрики группы */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
          <DashboardCard
            title="Участников"
            value={group.settings?.members_count || 0}
            icon={<Users className="h-6 w-6 text-blue-600" />}
          />
          <DashboardCard
            title="Модераторов"
            value={groupModerators.length}
            icon={<Settings className="h-6 w-6 text-green-600" />}
          />
          <DashboardCard
            title="Дата добавления"
            value={new Date(group.created_at).toLocaleDateString()}
            icon={<Clock className="h-6 w-6 text-yellow-600" />}
          />
          <DashboardCard
            title="Статус"
            value="Активна"
            icon={<BarChart2 className="h-6 w-6 text-purple-600" />}
          />
        </div>

        {/* Быстрые действия */}
        <div className="bg-white shadow rounded-lg p-6 mb-8">
          <h3 className="text-lg font-medium mb-6">Анализ группы</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Анализ модераторов */}
            <Link
              to={`/telegram/analyze/moderators?groupId=${group.id}`}
              className="block p-6 border border-gray-200 rounded-lg hover:border-indigo-300 hover:shadow-md transition-all duration-200"
            >
              <div className="flex items-center justify-center w-12 h-12 bg-indigo-100 rounded-lg mb-4 mx-auto">
                <Users className="h-6 w-6 text-indigo-600" />
              </div>
              <h4 className="text-lg font-medium text-gray-900 text-center mb-2">
                Анализ Модераторов
              </h4>
              <p className="text-gray-600 text-center text-sm">
                Оценка эффективности работы модераторов этой группы
              </p>
            </Link>

            {/* Анализ настроений */}
            <Link
              to={`/telegram/analyze/sentiment?groupId=${group.id}`}
              className="block p-6 border border-gray-200 rounded-lg hover:border-green-300 hover:shadow-md transition-all duration-200"
            >
              <div className="flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mb-4 mx-auto">
                <MessageSquare className="h-6 w-6 text-green-600" />
              </div>
              <h4 className="text-lg font-medium text-gray-900 text-center mb-2">
                Настроения Жителей
              </h4>
              <p className="text-gray-600 text-center text-sm">
                Анализ настроений и проблем жителей в этой группе
              </p>
            </Link>

            {/* Анализ постов */}
            <Link
              to="/telegram/analyze/posts"
              className="block p-6 border border-gray-200 rounded-lg hover:border-purple-300 hover:shadow-md transition-all duration-200"
            >
              <div className="flex items-center justify-center w-12 h-12 bg-purple-100 rounded-lg mb-4 mx-auto">
                <LinkIcon className="h-6 w-6 text-purple-600" />
              </div>
              <h4 className="text-lg font-medium text-gray-900 text-center mb-2">
                Комментарии к Постам
              </h4>
              <p className="text-gray-600 text-center text-sm">
                Анализ реакций на посты из любых групп
              </p>
            </Link>
          </div>
        </div>

        {/* Информация о группе */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Модераторы */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium mb-4">Модераторы группы</h3>
            {groupModerators.length > 0 ? (
              <div className="space-y-2">
                {groupModerators.map((moderator: string, index: number) => (
                  <div key={index} className="flex items-center p-3 bg-gray-50 rounded-md">
                    <div className="flex items-center justify-center w-8 h-8 bg-indigo-100 rounded-full mr-3">
                      <Users className="h-4 w-4 text-indigo-600" />
                    </div>
                    <span className="text-gray-900">{moderator}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">Модераторы не указаны</p>
            )}
          </div>

          {/* Настройки */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium mb-4">Настройки группы</h3>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-gray-600">ID группы</span>
                <span className="text-gray-900 font-mono text-sm">{group.group_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Участников</span>
                <span className="text-gray-900">{group.settings?.members_count || 'Не определено'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Дата создания</span>
                <span className="text-gray-900">{new Date(group.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Последнее обновление</span>
                <span className="text-gray-900">{new Date(group.updated_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};