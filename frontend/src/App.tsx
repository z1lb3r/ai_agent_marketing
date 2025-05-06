// frontend/src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DashboardPage } from './pages/DashboardPage';
import { TelegramPage } from './pages/TelegramPage';
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
                <Route path="/telegram" element={<TelegramPage />} />
                <Route path="/telegram/:groupId" element={<TelegramPage />} />
                {/* TODO: Add more routes */}
              </Routes>
            </main>
          </div>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App; 