import {
  SessionSummary,
  SessionDetail,
  AnalyticsData,
  ModelStatus,
  AppConfig
} from '../types';

const API_BASE = '/api';

export const api = {
  async getHealth(): Promise<{ status: string; service: string; version: string }> {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('Failed to fetch health status');
    return res.json();
  },

  async getModelStatus(): Promise<ModelStatus> {
    const res = await fetch(`${API_BASE}/health/models`);
    if (!res.ok) throw new Error('Failed to fetch model status');
    return res.json();
  },

  async getSessions(limit = 20): Promise<SessionSummary[]> {
    const res = await fetch(`${API_BASE}/sessions?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch sessions');
    return res.json();
  },

  async createSession(scenario = 'crisis_negotiation'): Promise<SessionSummary> {
    const res = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario }),
    });
    if (!res.ok) throw new Error('Failed to create session');
    return res.json();
  },

  async getSessionDetail(sessionId: string): Promise<SessionDetail> {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
    if (!res.ok) throw new Error('Failed to fetch session details');
    return res.json();
  },

  async terminateSession(sessionId: string): Promise<{ status: string }> {
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/terminate`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to terminate session');
    return res.json();
  },

  async getAnalytics(): Promise<AnalyticsData> {
    const res = await fetch(`${API_BASE}/analytics`);
    if (!res.ok) throw new Error('Failed to fetch analytics');
    return res.json();
  },

  async getConfig(): Promise<AppConfig> {
    const res = await fetch(`${API_BASE}/config`);
    if (!res.ok) throw new Error('Failed to fetch configuration');
    return res.json();
  },

  async updateConfig(config: Partial<AppConfig>): Promise<{ status: string; config: AppConfig }> {
    const res = await fetch(`${API_BASE}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error('Failed to update configuration');
    return res.json();
  },

  async sendWebRTCOffer(sdp: string, sessionId: string): Promise<{ sdp: string; type: string }> {
    const res = await fetch(`${API_BASE}/webrtc/offer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sdp, type: 'offer', session_id: sessionId }),
    });
    if (!res.ok) throw new Error('Failed to exchange WebRTC offer');
    return res.json();
  },

  async disconnectWebRTC(sessionId: string): Promise<void> {
    await fetch(`${API_BASE}/webrtc/disconnect?session_id=${sessionId}`, {
      method: 'POST',
    });
  },
};
