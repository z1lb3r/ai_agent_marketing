// frontend/src/components/Telegram/GroupList.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import { MessageSquare, Users, BarChart } from 'lucide-react';
import { useTelegramGroups } from '../../hooks/useTelegramData';

export const GroupList: React.FC = () => {
  const { data: groups, isLoading, error } = useTelegramGroups();

  if (isLoading) return <div>Loading groups...</div>;
  if (error) return <div>Error loading groups</div>;

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
        <h3 className="text-lg font-medium leading-6 text-gray-900">
          Telegram Groups
        </h3>
      </div>
      <ul className="divide-y divide-gray-200">
        {groups?.map((group) => (
          <li key={group.id}>
            <Link
              to={`/telegram/${group.id}`}
              className="block hover:bg-gray-50"
            >
              <div className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <MessageSquare className="h-5 w-5 text-gray-400 mr-3" />
                    <p className="text-sm font-medium text-indigo-600 truncate">
                      {group.name}
                    </p>
                  </div>
                  <div className="ml-2 flex items-center">
                    <Users className="h-4 w-4 text-gray-400 mr-1" />
                    <span className="text-sm text-gray-500">
                      {group.settings?.members_count || 0}
                    </span>
                  </div>
                </div>
                <div className="mt-2 sm:flex sm:justify-between">
                  <div className="sm:flex">
                    <p className="flex items-center text-sm text-gray-500">
                      <BarChart className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" />
                      Last analyzed: {new Date(group.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
};