// frontend/src/components/Telegram/KeyTopics.tsx
import React from 'react';
import { MessageSquare, Zap, AlertTriangle, ArrowUp } from 'lucide-react';

interface KeyTopicsProps {
  topics: string[];
}

export const KeyTopics: React.FC<KeyTopicsProps> = ({ topics }) => {
  if (!topics || topics.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6 flex items-center justify-center">
        <p className="text-gray-500">Нет данных о ключевых темах</p>
      </div>
    );
  }
  
  // Маппинг иконок для разных типов тем
  const getIconForTopic = (topic: string) => {
    if (topic.includes('support') || topic.includes('поддержка')) 
      return <MessageSquare className="h-5 w-5 text-blue-500" />;
    if (topic.includes('issue') || topic.includes('problem') || topic.includes('проблем')) 
      return <AlertTriangle className="h-5 w-5 text-red-500" />;
    if (topic.includes('update') || topic.includes('обновлен')) 
      return <ArrowUp className="h-5 w-5 text-green-500" />;
    
    return <Zap className="h-5 w-5 text-purple-500" />;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium mb-4">Ключевые темы обсуждения</h3>
      
      <ul className="space-y-3">
        {topics.map((topic, index) => (
          <li key={index} className="flex items-center p-3 bg-gray-50 rounded-lg">
            <div className="p-2 bg-white rounded-full shadow-sm mr-3">
              {getIconForTopic(topic)}
            </div>
            <span className="text-gray-700">{topic}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};