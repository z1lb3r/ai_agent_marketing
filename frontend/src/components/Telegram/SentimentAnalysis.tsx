// frontend/src/components/Telegram/SentimentAnalysis.tsx
import React from 'react';
import { BarChart2, TrendingUp, AlertCircle } from 'lucide-react';

interface SentimentAnalysisProps {
  groupId: string;
  analysisResults: any | null;
  isAnalyzing: boolean;
  onAnalyze: () => void;
}

export const SentimentAnalysis: React.FC<SentimentAnalysisProps> = ({ 
  groupId, 
  analysisResults, 
  isAnalyzing, 
  onAnalyze 
}) => {
  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <BarChart2 className="h-5 w-5 text-purple-600 mr-2" />
          <h3 className="text-lg font-medium">Sentiment Analysis</h3>
        </div>
        <button
          onClick={onAnalyze}
          disabled={isAnalyzing}
          className={`px-4 py-2 rounded-md ${
            isAnalyzing 
              ? 'bg-gray-300 cursor-not-allowed' 
              : 'bg-indigo-600 hover:bg-indigo-700 text-white'
          }`}
        >
          {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>
      
      {isAnalyzing ? (
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-24 bg-gray-200 rounded mb-4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      ) : analysisResults ? (
        <div>
          <div className="mb-6">
            <h4 className="font-medium text-gray-700 mb-2">Overall Sentiment</h4>
            <div className="bg-gray-100 h-6 rounded-full overflow-hidden">
              <div 
                className="h-full bg-green-500"
                style={{ width: `${analysisResults.sentiment_score || 0}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-sm mt-1">
              <span>Negative</span>
              <span>Neutral</span>
              <span>Positive</span>
            </div>
          </div>
          
          <div className="mb-6">
            <h4 className="font-medium text-gray-700 mb-2">Moderator Performance</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-sm text-gray-500">Response Time</p>
                <p className="text-xl font-semibold">{analysisResults.response_time || 'N/A'}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-sm text-gray-500">Resolved Issues</p>
                <p className="text-xl font-semibold">{analysisResults.resolved_issues || 'N/A'}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-sm text-gray-500">Satisfaction Score</p>
                <p className="text-xl font-semibold">{analysisResults.satisfaction_score || 'N/A'}</p>
              </div>
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-sm text-gray-500">Engagement Rate</p>
                <p className="text-xl font-semibold">{analysisResults.engagement_rate || 'N/A'}</p>
              </div>
            </div>
          </div>
          
          {analysisResults.key_topics && (
            <div>
              <h4 className="font-medium text-gray-700 mb-2">Key Topics</h4>
              <div className="flex flex-wrap gap-2">
                {analysisResults.key_topics.map((topic: string, index: number) => (
                  <span 
                    key={index} 
                    className="bg-indigo-100 text-indigo-800 px-2 py-1 rounded text-sm"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-8">
          <TrendingUp className="h-12 w-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 mb-2">No analysis data available</p>
          <p className="text-sm text-gray-400 mb-6 max-w-md mx-auto">
            Run the analysis to get insights about moderator performance, sentiment analysis, 
            and key discussion topics in this group.
          </p>
          <button
            onClick={onAnalyze}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md"
          >
            Start Analysis
          </button>
        </div>
      )}
    </div>
  );
};