// frontend/src/components/Telegram/RecommendationsList.tsx
import React from 'react';
import { LightBulb } from 'lucide-react';

interface RecommendationsListProps {
  recommendations: string[];
}

export const RecommendationsList: React.FC<RecommendationsListProps> = ({ recommendations }) => {
  if (!recommendations || recommendations.length === 0) {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-8">
      <h3 className="text-lg font-medium mb-4">Рекомендации по улучшению</h3>
      
      <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
        <ul className="space-y-4">
          {recommendations.map((recommendation, index) => (
            <li key={index} className="flex">
              <div className="flex-shrink-0 mr-3">
                <LightBulb className="h-5 w-5 text-blue-600" />
              </div>
              <p className="text-gray-700">{recommendation}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};