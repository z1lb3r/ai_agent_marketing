// frontend/src/components/Telegram/AnalysisForm.tsx
import React, { useState } from 'react';
import { api } from '../../services/api';

interface AnalysisFormProps {
  groupId: string;
  moderators?: string[];
  onSuccess: (result: any) => void;
}

export const AnalysisForm: React.FC<AnalysisFormProps> = ({ 
  groupId, 
  moderators = [],
  onSuccess 
}) => {
  const [prompt, setPrompt] = useState('');
  const [selectedModerators, setSelectedModerators] = useState<string[]>(moderators);
  const [daysBack, setDaysBack] = useState(7);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) {
      setError('Please enter a prompt for analysis');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await api.post(`/telegram/groups/${groupId}/analyze`, {
        prompt,
        moderators: selectedModerators,
        days_back: daysBack
      });

      if (response.data.status === 'success') {
        onSuccess(response.data.result);
      }
    } catch (err) {
      console.error('Error running analysis:', err);
      setError('Failed to run analysis. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6 mb-6">
      <h3 className="text-lg font-medium mb-4">Run Analysis</h3>
      
      {error && (
        <div className="bg-red-50 text-red-700 p-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Analysis Prompt
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe how moderators should behave..."
            className="w-full p-2 border border-gray-300 rounded"
            rows={4}
            required
          ></textarea>
          <p className="text-xs text-gray-500 mt-1">
            Describe the criteria for evaluating moderator performance
          </p>
        </div>
        
        {moderators.length > 0 && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Moderators to Analyze
            </label>
            <div className="space-y-2">
              {moderators.map((mod) => (
                <label key={mod} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedModerators.includes(mod)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedModerators([...selectedModerators, mod]);
                      } else {
                        setSelectedModerators(selectedModerators.filter(m => m !== mod));
                      }
                    }}
                    className="mr-2"
                  />
                  {mod}
                </label>
              ))}
            </div>
          </div>
        )}
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Days to Analyze
          </label>
          <input
            type="number"
            value={daysBack}
            onChange={(e) => setDaysBack(parseInt(e.target.value))}
            min={1}
            max={30}
            className="w-full p-2 border border-gray-300 rounded"
          />
          <p className="text-xs text-gray-500 mt-1">
            Number of days to look back for analysis (1-30)
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
          {isLoading ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </form>
    </div>
  );
};