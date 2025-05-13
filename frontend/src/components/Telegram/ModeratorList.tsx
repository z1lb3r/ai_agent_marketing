// frontend/src/components/Telegram/ModeratorList.tsx
import React from 'react';
import { useGroupModerators } from '../../hooks/useTelegramData';
import { Users } from 'lucide-react';

interface ModeratorListProps {
  groupId: string;
}

export const ModeratorList: React.FC<ModeratorListProps> = ({ groupId }) => {
  const { data: moderators, isLoading, error } = useGroupModerators(groupId);

  if (isLoading) return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium mb-4">Group Moderators</h3>
      <div className="animate-pulse">
        <div className="h-10 bg-gray-200 rounded mb-4"></div>
        <div className="h-10 bg-gray-200 rounded mb-4"></div>
      </div>
    </div>
  );

  if (error) return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium mb-4">Group Moderators</h3>
      <div className="text-red-500">Failed to load moderators. Please try again.</div>
    </div>
  );
  
  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center mb-4">
        <Users className="h-5 w-5 text-indigo-600 mr-2" />
        <h3 className="text-lg font-medium">Group Moderators</h3>
      </div>
      
      <div className="space-y-3">
        {moderators && moderators.length > 0 ? (
          moderators.map((moderator) => (
            <div key={moderator.id} className="flex items-center p-2 hover:bg-gray-50 rounded">
              <div className="bg-indigo-100 p-2 rounded-full w-10 h-10 flex items-center justify-center mr-3">
                <span className="text-indigo-700 font-medium">
                  {moderator.first_name?.charAt(0) || moderator.username?.charAt(0) || '?'}
                </span>
              </div>
              <div>
                <p className="font-medium">
                  {moderator.first_name} {moderator.last_name}
                </p>
                {moderator.username && (
                  <p className="text-sm text-gray-500">@{moderator.username}</p>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-6">
            <Users className="h-12 w-12 text-gray-300 mx-auto mb-2" />
            <p className="text-gray-500">No moderators available</p>
          </div>
        )}
      </div>
    </div>
  );
};