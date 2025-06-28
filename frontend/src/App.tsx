// frontend/src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DashboardPage } from './pages/DashboardPage';
import { TelegramMainPage } from './pages/TelegramMainPage';
import { ModeratorsAnalysisPage } from './pages/ModeratorsAnalysisPage';
import { SentimentAnalysisPage } from './pages/SentimentAnalysisPage';
import { PostsAnalysisPage } from './pages/PostsAnalysisPage';
import { TelegramGroupsPage } from './pages/TelegramGroupsPage';
import { TelegramGroupPage } from './pages/TelegramGroupPage';
import { Sidebar } from './components/Common/Sidebar';
import { Header } from './components/Common/Header';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="flex h-screen bg-gray-100">
          <Sidebar />
          <div className="flex-1 flex flex-col overflow-hidden">
            <Header />
            <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-100">
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                
                {/* Telegram роуты */}
                <Route path="/telegram" element={<TelegramMainPage />} />
                <Route path="/telegram/analyze/moderators" element={<ModeratorsAnalysisPage />} />
                <Route path="/telegram/analyze/sentiment" element={<SentimentAnalysisPage />} />
                <Route path="/telegram/analyze/posts" element={<PostsAnalysisPage />} />
                <Route path="/telegram/groups" element={<TelegramGroupsPage />} />
                <Route path="/telegram/groups/:groupId" element={<TelegramGroupPage />} />
                
                {/* TODO: Add Email and Calls routes */}
              </Routes>
            </main>
          </div>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;