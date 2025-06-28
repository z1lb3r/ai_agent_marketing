// frontend/src/pages/TelegramGroupsPage.tsx
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Settings, Plus } from 'lucide-react';
import { useTelegramGroups } from '../hooks/useTelegramData';
import { GroupList } from '../components/Telegram/GroupList';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';

export const TelegramGroupsPage: React.FC = () => {
  const { data: groups } = useTelegramGroups();
  const queryClient = useQueryClient();
  
  // Состояние для формы добавления группы
  const [showAddGroupForm, setShowAddGroupForm] = useState<boolean>(false);
  const [groupLink, setGroupLink] = useState<string>('');
  const [moderators, setModerators] = useState<string>('');
  const [addingGroup, setAddingGroup] = useState<boolean>(false);
  const [addGroupError, setAddGroupError] = useState<string>('');

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

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Хлебные крошки */}
        <div className="flex items-center mb-8">
          <Link
            to="/telegram"
            className="flex items-center text-indigo-600 hover:text-indigo-800"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Назад к Telegram
          </Link>
        </div>

        {/* Заголовок */}
        <div className="flex justify-between items-center mb-8">
          <div className="flex items-center">
            <div className="flex items-center justify-center w-12 h-12 bg-gray-100 rounded-lg mr-4">
              <Settings className="h-6 w-6 text-gray-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Управление Группами
              </h1>
              <p className="text-lg text-gray-600 mt-1">
                Добавление, настройка и обзор подключенных Telegram групп
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowAddGroupForm(!showAddGroupForm)}
            className="flex items-center px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md transition-colors"
          >
            <Plus className="h-4 w-4 mr-2" />
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Ссылка на группу или Username
                  </label>
                  <input
                    type="text"
                    value={groupLink}
                    onChange={(e) => setGroupLink(e.target.value)}
                    placeholder="t.me/groupname или @groupname"
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                    required
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Введите ссылку на Telegram группу или username
                  </p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Модераторы
                  </label>
                  <input
                    type="text"
                    value={moderators}
                    onChange={(e) => setModerators(e.target.value)}
                    placeholder="@moderator1, @moderator2"
                    className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Введите username модераторов через запятую
                  </p>
                </div>
              </div>
              
              <div className="mt-6 flex justify-end">
                <button
                  type="submit"
                  disabled={addingGroup}
                  className={`px-6 py-3 rounded-md text-white font-medium ${
                    addingGroup 
                      ? 'bg-gray-400 cursor-not-allowed' 
                      : 'bg-indigo-600 hover:bg-indigo-700'
                  }`}
                >
                  {addingGroup ? 'Добавление...' : 'Добавить Группу'}
                </button>
              </div>
            </form>
          </div>
        )}
        
        {/* Список групп */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <GroupList groups={groups || []} />
          </div>
          
          {/* Информационная панель */}
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium mb-4">Как управлять группами</h3>
            <p className="text-gray-600 mb-6">
              Добавляйте и настраивайте Telegram группы для последующего анализа модераторов и настроений сообщества.
            </p>
            
            <div className="space-y-4">
              <div className="flex items-start">
                <div className="bg-indigo-100 p-2 rounded-full mr-3 mt-0.5">
                  <span className="text-indigo-700 font-bold text-sm">1</span>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">Добавьте группу</h4>
                  <p className="text-gray-600 text-sm">
                    Укажите ссылку на группу и список модераторов для корректного анализа
                  </p>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="bg-indigo-100 p-2 rounded-full mr-3 mt-0.5">
                  <span className="text-indigo-700 font-bold text-sm">2</span>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">Настройте доступ</h4>
                  <p className="text-gray-600 text-sm">
                    Убедитесь, что бот имеет доступ к группе для чтения сообщений
                  </p>
                </div>
              </div>
              
              <div className="flex items-start">
                <div className="bg-indigo-100 p-2 rounded-full mr-3 mt-0.5">
                  <span className="text-indigo-700 font-bold text-sm">3</span>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">Запускайте анализ</h4>
                  <p className="text-gray-600 text-sm">
                    Выберите тип анализа и получайте детальные отчеты о коммуникациях
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="font-medium text-gray-900 mb-3">Статистика</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-indigo-600">{groups?.length || 0}</div>
                  <div className="text-sm text-gray-500">Всего групп</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {groups?.filter(g => g.settings?.members_count > 0).length || 0}
                  </div>
                  <div className="text-sm text-gray-500">Активных</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};