// frontend/src/components/Telegram/AddGroupForm.tsx
import React, { useState } from 'react';
import { api } from '../../services/api';

interface AddGroupFormProps {
  onSuccess: () => void;
}

export const AddGroupForm: React.FC<AddGroupFormProps> = ({ onSuccess }) => {
  const [link, setLink] = useState('');
  const [moderators, setModerators] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // Преобразуем строку с модераторами в массив
      const moderatorsList = moderators
        .split(',')
        .map(m => m.trim())
        .filter(m => m.length > 0);

      const response = await api.post('/telegram/groups', {
        link,
        moderators: moderatorsList
      });

      if (response.data.status === 'created' || response.data.status === 'updated') {
        setLink('');
        setModerators('');
        onSuccess();
      }
    } catch (err) {
      console.error('Error adding group:', err);
      setError('Failed to add group. Please check the link and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium mb-4">Add Telegram Group</h3>
      
      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Group Link or Username
          </label>
          <input
            type="text"
            value={link}
            onChange={(e) => setLink(e.target.value)}
            placeholder="t.me/groupname or @groupname"
            className="w-full p-2 border border-gray-300 rounded"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Enter the Telegram group link or username
          </p>
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Moderators
          </label>
          <input
            type="text"
            value={moderators}
            onChange={(e) => setModerators(e.target.value)}
            placeholder="@moderator1, @moderator2"
            className="w-full p-2 border border-gray-300 rounded"
          />
          <p className="text-xs text-gray-500 mt-1">
            Enter moderator usernames separated by commas
          </p>
        </div>
        
        <button
          type="submit"
          disabled={isLoading}
          className={`px-4 py-2 rounded ${
            isLoading 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-indigo-600 hover:bg-indigo-700 text-white'
          }`}
        >
          {isLoading ? 'Adding...' : 'Add Group'}
        </button>
      </form>
    </div>
  );
};