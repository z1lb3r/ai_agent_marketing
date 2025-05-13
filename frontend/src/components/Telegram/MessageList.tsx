// frontend/src/components/Telegram/MessageList.tsx
import React from 'react';
import { useGroupMessages } from '../../hooks/useTelegramData';
import { MessageSquare } from 'lucide-react';

interface MessageListProps {
  groupId: string;
}

export const MessageList: React.FC<MessageListProps> = ({ groupId }) => {
  const { data: messages, isLoading, error } = useGroupMessages(groupId);

  if (isLoading) return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium mb-4">Recent Messages</h3>
      <div className="animate-pulse">
        <div className="h-10 bg-gray-200 rounded mb-4"></div>
        <div className="h-10 bg-gray-200 rounded mb-4"></div>
        <div className="h-10 bg-gray-200 rounded mb-4"></div>
      </div>
    </div>
  );

  if (error) return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium mb-4">Recent Messages</h3>
      <div className="text-red-500">Failed to load messages. Please try again.</div>
    </div>
  );
  
  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center mb-4">
        <MessageSquare className="h-5 w-5 text-blue-600 mr-2" />
        <h3 className="text-lg font-medium">Recent Messages</h3>
      </div>
      
      <div className="space-y-4 max-h-[500px] overflow-y-auto">
        {messages && messages.length > 0 ? (
          messages.map((message) => (
            <div key={message.id} className="border-b pb-3">
              <div className="flex justify-between">
                <span className="font-medium text-indigo-600">User #{message.sender_id}</span>
                <span className="text-sm text-gray-500">
                  {new Date(message.date).toLocaleString()}
                </span>
              </div>
              <p className="mt-1 text-gray-700">{message.text}</p>
              {message.reply_to_msg_id && (
                <div className="mt-1 pl-3 border-l-2 border-gray-300 text-sm text-gray-500">
                  Replying to message #{message.reply_to_msg_id}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="text-center py-6">
            <MessageSquare className="h-12 w-12 text-gray-300 mx-auto mb-2" />
            <p className="text-gray-500">No messages available</p>
          </div>
        )}
      </div>
    </div>
  );
};