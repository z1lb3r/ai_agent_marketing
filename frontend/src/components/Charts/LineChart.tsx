// frontend/src/components/Charts/LineChart.tsx
import React from 'react';
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface LineChartProps {
  data: any[];
  dataKey: string;
  xAxisKey: string;
  title?: string;
  color?: string;
}

export const LineChart: React.FC<LineChartProps> = ({
  data,
  dataKey,
  xAxisKey,
  title,
  color = '#3b82f6',
}) => {
  return (
    <div className="bg-white p-4 rounded-lg shadow">
      {title && <h3 className="text-lg font-medium mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={300}>
        <RechartsLineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={xAxisKey} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            activeDot={{ r: 8 }}
          />
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
};