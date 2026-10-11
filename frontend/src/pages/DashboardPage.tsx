import React from 'react';
import { SessionSummary, AnalyticsData, ModelStatus } from '../types';
import { ModelStatusBadge } from '../components/ModelStatusBadge';
import {
  Mic,
  Activity,
  Zap,
  MessageSquare,
  Clock,
  ArrowRight,
  Shield,
  Layers,
} from 'lucide-react';

interface DashboardPageProps {
  sessions: SessionSummary[];
  analytics: AnalyticsData | null;
  modelStatus: ModelStatus | null;
  onStartSession: () => void;
  onSelectSession: (sessionId: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  sessions,
  analytics,
  modelStatus,
  onStartSession,
  onSelectSession,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Top Banner / Welcome */}
      <div
        className="glass-panel glass-panel-glow"
        style={{
          padding: '32px',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '24px',
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 27, 75, 0.6) 100%)',
        }}
      >
        <div style={{ maxWidth: '600px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <span className="status-pill status-online">System Ready</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Crisis Simulator Active</span>
          </div>
          <h1 style={{ fontSize: '1.85rem', fontWeight: 700, marginBottom: '8px' }}>
            Crisis Negotiation Command Center
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: 1.5 }}>
            Ready to test voice de-escalation skills. Start a real-time session to begin acoustic emotion tracking
            and continuous dialogue with Jordan.
          </p>
        </div>

        <button
          className="btn btn-primary"
          onClick={onStartSession}
          style={{ fontSize: '1rem', padding: '14px 24px', borderRadius: '12px' }}
        >
          <Mic size={18} />
          <span>Start Voice Session</span>
        </button>
      </div>

      {/* Model Health Grid */}
      <div className="glass-panel" style={{ padding: '20px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-muted)' }}>
            Active AI & Signal Infrastructure
          </h3>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>Zero-latency local orchestration</span>
        </div>
        <ModelStatusBadge status={modelStatus} />
      </div>

      {/* Primary KPI Metrics Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Total Sessions</span>
            <Layers size={18} color="#818cf8" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
            {analytics?.total_sessions ?? sessions.length}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Crisis negotiation trials
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Conversation Turns</span>
            <MessageSquare size={18} color="#38bdf8" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
            {analytics?.total_turns ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Trainee speech utterances
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Avg EOU-to-Audio Latency</span>
            <Zap size={18} color="#10b981" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#34d399' }}>
            {analytics && analytics.avg_latency_ms > 0 ? `${analytics.avg_latency_ms.toFixed(0)} ms` : '--'}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Measured speech-to-speech response
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Barge-In Interruptions</span>
            <Activity size={18} color="#f43f5e" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
            {analytics?.interruption_count ?? 0}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Handled full-duplex interruptions
          </div>
        </div>
      </div>

      {/* Recent Session Activity List */}
      <div className="glass-panel" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Recent Negotiation Sessions</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Historical simulation trials and measured performance
            </p>
          </div>
        </div>

        {sessions.length === 0 ? (
          <div
            style={{
              padding: '48px 24px',
              textAlign: 'center',
              color: 'var(--text-muted)',
              background: 'rgba(255,255,255,0.01)',
              borderRadius: '12px',
              border: '1px dashed var(--border-subtle)',
            }}
          >
            <Shield size={36} color="var(--text-dim)" style={{ marginBottom: '12px' }} />
            <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
              No Recorded Sessions Yet
            </h4>
            <p style={{ fontSize: '0.85rem', maxWidth: '400px', margin: '0 auto 16px' }}>
              Launch your first live negotiation session to begin recording real speech transcriptions, acoustic
              emotions, and latency telemetry.
            </p>
            <button className="btn btn-primary" onClick={onStartSession}>
              <Mic size={16} />
              <span>Launch First Session</span>
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {sessions.map((sess) => (
              <div
                key={sess.session_id}
                onClick={() => onSelectSession(sess.session_id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '16px 20px',
                  borderRadius: '12px',
                  background: 'rgba(255,255,255,0.02)',
                  border: '1px solid var(--border-subtle)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.04)';
                  e.currentTarget.style.borderColor = 'rgba(99,102,241,0.3)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.02)';
                  e.currentTarget.style.borderColor = 'var(--border-subtle)';
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div
                    style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: '10px',
                      background: 'rgba(99, 102, 241, 0.12)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Mic size={18} color="#818cf8" />
                  </div>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '2px' }}>
                      {sess.scenario.replace('_', ' ').toUpperCase()}
                    </div>
                    <div style={{ display: 'flex', gap: '12px', fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Clock size={12} />
                        {new Date(sess.start_time).toLocaleString()}
                      </span>
                      <span>•</span>
                      <span>{sess.total_turns} turns</span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                  {sess.avg_latency_ms > 0 && (
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', fontWeight: 700, color: '#38bdf8' }}>
                        {sess.avg_latency_ms.toFixed(0)} ms
                      </div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Avg Latency</div>
                    </div>
                  )}

                  <span
                    className={`status-pill ${
                      sess.status === 'active' ? 'status-online' : 'status-warning'
                    }`}
                  >
                    {sess.status}
                  </span>

                  <ArrowRight size={18} color="var(--text-dim)" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
