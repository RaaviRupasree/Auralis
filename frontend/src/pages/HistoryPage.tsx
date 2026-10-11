import React, { useState, useEffect } from 'react';
import { SessionSummary, SessionDetail } from '../types';
import { api } from '../services/api';
import { EmotionBadge } from '../components/EmotionBadge';
import { LatencyCard } from '../components/LatencyCard';
import {
  History,
  Calendar,
  Clock,
  ArrowLeft,
  User,
  Bot,
  Zap,
} from 'lucide-react';

interface HistoryPageProps {
  initialSessionId?: string | null;
  onClearInitialSession?: () => void;
}

export const HistoryPage: React.FC<HistoryPageProps> = ({
  initialSessionId,
  onClearInitialSession,
}) => {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(initialSessionId || null);
  const [sessionDetail, setSessionDetail] = useState<SessionDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    if (selectedSessionId) {
      loadSessionDetail(selectedSessionId);
    }
  }, [selectedSessionId]);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const data = await api.getSessions(50);
      setSessions(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadSessionDetail = async (id: string) => {
    try {
      const detail = await api.getSessionDetail(id);
      setSessionDetail(detail);
    } catch (e) {
      console.error(e);
    }
  };

  if (selectedSessionId && sessionDetail) {
    const { session, turns } = sessionDetail;
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1000px', margin: '0 auto' }}>
        <button
          className="btn btn-secondary"
          onClick={() => {
            setSelectedSessionId(null);
            setSessionDetail(null);
            if (onClearInitialSession) onClearInitialSession();
          }}
          style={{ alignSelf: 'flex-start', padding: '6px 14px', fontSize: '0.85rem' }}
        >
          <ArrowLeft size={16} />
          <span>Back to Sessions List</span>
        </button>

        {/* Header detail */}
        <div className="glass-panel" style={{ padding: '24px 28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 700 }}>
              Session: {session.scenario.replace('_', ' ').toUpperCase()}
            </h2>
            <span className={`status-pill ${session.status === 'completed' ? 'status-online' : 'status-warning'}`}>
              {session.status}
            </span>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Calendar size={14} />
              Started: {new Date(session.start_time).toLocaleString()}
            </span>
            <span>•</span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Clock size={14} />
              Total Turns: {session.total_turns}
            </span>
            {session.avg_latency_ms > 0 && (
              <>
                <span>•</span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#38bdf8' }}>
                  <Zap size={14} />
                  Avg Latency: {session.avg_latency_ms.toFixed(0)} ms
                </span>
              </>
            )}
          </div>
        </div>

        {/* Turn Timeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Dialogue Records</h3>

          {turns.length === 0 ? (
            <div className="glass-panel" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-dim)' }}>
              No dialog turns recorded in this session.
            </div>
          ) : (
            turns.map((t) => (
              <div key={t.turn_id || t.turn_index} className="glass-panel" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-dim)' }}>
                    TURN #{t.turn_index}
                  </span>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <EmotionBadge emotion={t.detected_emotion} confidence={t.emotion_confidence} showDetails={false} />
                    <LatencyCard metrics={t.metrics} compact={true} />
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {/* Trainee */}
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                    <div style={{ width: '28px', height: '28px', borderRadius: '6px', background: 'rgba(56, 189, 248, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <User size={14} color="#38bdf8" />
                    </div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: '#38bdf8', fontWeight: 600, marginBottom: '2px' }}>
                        Trainee
                      </div>
                      <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
                        "{t.user_transcript}"
                      </p>
                    </div>
                  </div>

                  {/* Jordan */}
                  <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-start', paddingLeft: '16px' }}>
                    <div style={{ width: '28px', height: '28px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <Bot size={14} color="#10b981" />
                    </div>
                    <div>
                      <div style={{ fontSize: '0.75rem', color: '#34d399', fontWeight: 600, marginBottom: '2px' }}>
                        Jordan
                      </div>
                      <p style={{ fontSize: '0.9rem', color: 'var(--text-main)', lineHeight: 1.5 }}>
                        "{t.ai_response}"
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: '6px' }}>
          Conversation & Session Archive
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Stored simulation transcripts, acoustic emotion observations, and measured latency metrics.
        </p>
      </div>

      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
          Loading session archive...
        </div>
      ) : sessions.length === 0 ? (
        <div className="glass-panel" style={{ padding: '48px', textAlign: 'center', color: 'var(--text-dim)' }}>
          <History size={40} style={{ marginBottom: '12px', opacity: 0.5 }} />
          <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
            No Sessions Recorded
          </h4>
          <p style={{ fontSize: '0.85rem' }}>
            Completed sessions will be preserved in SQLite with turn-by-turn transcripts and emotion scores.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {sessions.map((s) => (
            <div
              key={s.session_id}
              onClick={() => setSelectedSessionId(s.session_id)}
              className="glass-panel"
              style={{
                padding: '16px 24px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '4px' }}>
                  {s.scenario.replace('_', ' ').toUpperCase()}
                </div>
                <div style={{ display: 'flex', gap: '14px', fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                  <span>{new Date(s.start_time).toLocaleString()}</span>
                  <span>•</span>
                  <span>{s.total_turns} turns recorded</span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                {s.avg_latency_ms > 0 && (
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.9rem', color: '#38bdf8', fontWeight: 700 }}>
                      {s.avg_latency_ms.toFixed(0)} ms
                    </span>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>avg latency</div>
                  </div>
                )}
                <span className={`status-pill ${s.status === 'completed' ? 'status-online' : 'status-warning'}`}>
                  {s.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
