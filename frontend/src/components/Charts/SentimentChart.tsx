// frontend/src/components/Charts/SentimentChart.tsx
import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface SentimentChartProps {
  sentimentData?: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

export const SentimentChart: React.FC<SentimentChartProps> = ({ sentimentData }) => {
  if (!sentimentData) {
    return (
      <div className="bg-white rounded-lg shadow p-6 flex items-center justify-center">
        <p className="text-gray-500">Нет данных для отображения</p>
      </div>
    );
  }

  const data = [
    { name: 'Позитивные', value: sentimentData.positive, color: '#10B981' },
    { name: 'Нейтральные', value: sentimentData.neutral, color: '#6B7280' },
    { name: 'Негативные', value: sentimentData.negative, color: '#EF4444' },
  ];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium mb-4">Анализ сентимента сообщений</h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
              label={({name, percent}) => `${name} ${(percent * 100).toFixed(0)}%`}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip formatter={(value) => `${value}%`} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};