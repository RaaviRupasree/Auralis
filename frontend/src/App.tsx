import React, { useState, useEffect } from 'react';
import { Sidebar, NavTab } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { LandingPage } from './pages/LandingPage';
import { DashboardPage } from './pages/DashboardPage';
import { LiveSessionPage } from './pages/LiveSessionPage';
import { HistoryPage } from './pages/HistoryPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { SettingsPage } from './pages/SettingsPage';
import { SessionSummary, AnalyticsData, ModelStatus } from './types';
import { api } from './services/api';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard');
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [loadingModels, setLoadingModels] = useState(false);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [selectedHistorySessionId, setSelectedHistorySessionId] = useState<string | null>(null);

  useEffect(() => {
    fetchGlobalData();
  }, []);

  const fetchGlobalData = async () => {
    setLoadingModels(true);
    try {
      const [models, sessList, analyticsData] = await Promise.allSettled([
        api.getModelStatus(),
        api.getSessions(10),
        api.getAnalytics(),
      ]);

      if (models.status === 'fulfilled') setModelStatus(models.value);
      if (sessList.status === 'fulfilled') setSessions(sessList.value);
      if (analyticsData.status === 'fulfilled') setAnalytics(analyticsData.value);
    } catch (e) {
      console.error('Failed to load initial data', e);
    } finally {
      setLoadingModels(false);
    }
  };

  const handleStartVoiceSession = () => {
    setCurrentTab('session');
  };

  const handleSelectSessionFromDashboard = (sessionId: string) => {
    setSelectedHistorySessionId(sessionId);
    setCurrentTab('history');
  };

  return (
    <div className="layout-container">
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => {
          if (tab !== 'history') setSelectedHistorySessionId(null);
          setCurrentTab(tab);
        }}
        isSessionActive={currentTab === 'session'}
      />

      <div className="main-content">
        <Navbar
          modelStatus={modelStatus}
          loadingModels={loadingModels}
          onStartSession={handleStartVoiceSession}
          isSessionActive={currentTab === 'session'}
        />

        <main className="page-wrapper">
          {currentTab === 'landing' && (
            <LandingPage onStartTraining={handleStartVoiceSession} />
          )}

          {currentTab === 'dashboard' && (
            <DashboardPage
              sessions={sessions}
              analytics={analytics}
              modelStatus={modelStatus}
              onStartSession={handleStartVoiceSession}
              onSelectSession={handleSelectSessionFromDashboard}
            />
          )}

          {currentTab === 'session' && <LiveSessionPage />}

          {currentTab === 'history' && (
            <HistoryPage
              initialSessionId={selectedHistorySessionId}
              onClearInitialSession={() => setSelectedHistorySessionId(null)}
            />
          )}

          {currentTab === 'analytics' && <AnalyticsPage />}

          {currentTab === 'settings' && <SettingsPage />}
        </main>
      </div>
    </div>
  );
};

export default App;
