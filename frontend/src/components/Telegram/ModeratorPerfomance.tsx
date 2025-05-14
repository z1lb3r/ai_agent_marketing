// frontend/src/components/Telegram/ModeratorPerformance.tsx
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ModeratorPerformanceProps {
  performanceData?: {
    effectiveness: number;
    helpfulness: number;
    clarity: number;
  };
  responseTimeData?: {
    avg: number;
    min: number;
    max: number;
  };
}

export const ModeratorPerformance: React.FC<ModeratorPerformanceProps> = ({ 
  performanceData, responseTimeData 
}) => {
  if (!performanceData) {
    return (
      <div className="bg-white rounded-lg shadow p-6 flex items-center justify-center">
        <p className="text-gray-500">Нет данных о эффективности модераторов</p>
      </div>
    );
  }

  const performanceMetrics = [
    { name: 'Эффективность', value: performanceData.effectiveness },
    { name: 'Полезность', value: performanceData.helpfulness },
    { name: 'Ясность', value: performanceData.clarity },
  ];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium mb-4">Эффективность модераторов</h3>
      
      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={performanceMetrics}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis domain={[0, 100]} />
            <Tooltip formatter={(value) => [`${value}%`, 'Оценка']} />
            <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
        
      {responseTimeData && (
        <div className="mt-4">
          <h4 className="font-medium text-gray-700 mb-2">Время ответа</h4>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-blue-50 p-3 rounded-lg text-center">
              <p className="text-sm text-gray-500">Минимальное</p>
              <p className="text-lg font-semibold text-blue-700">{responseTimeData.min} мин</p>
            </div>
            <div className="bg-blue-50 p-3 rounded-lg text-center">
              <p className="text-sm text-gray-500">Среднее</p>
              <p className="text-lg font-semibold text-blue-700">{responseTimeData.avg} мин</p>
            </div>
            <div className="bg-blue-50 p-3 rounded-lg text-center">
              <p className="text-sm text-gray-500">Максимальное</p>
              <p className="text-lg font-semibold text-blue-700">{responseTimeData.max} мин</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};