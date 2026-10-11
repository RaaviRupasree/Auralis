import React, { useState, useEffect } from 'react';
import { AnalyticsData } from '../types';
import { api } from '../services/api';
import {
  BarChart2,
  Zap,
  Cpu,
  Clock,
  MessageSquare,
  PieChart,
} from 'lucide-react';

export const AnalyticsPage: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const res = await api.getAnalytics();
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading real-time performance analytics...
      </div>
    );
  }

  const hasData = data && data.total_turns > 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: '6px' }}>
          Performance & Emotion Analytics
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Real system telemetry measured across active negotiation conversation turns.
        </p>
      </div>

      {!hasData ? (
        <div className="glass-panel" style={{ padding: '60px 24px', textAlign: 'center', color: 'var(--text-dim)' }}>
          <BarChart2 size={48} style={{ marginBottom: '16px', opacity: 0.4 }} />
          <h3 style={{ fontSize: '1.15rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '6px' }}>
            No Recorded Telemetry Yet
          </h3>
          <p style={{ fontSize: '0.875rem', maxWidth: '420px', margin: '0 auto' }}>
            Run a live voice session to capture real end-of-utterance to audio playback latency, Whisper STT speed,
            and acoustic emotion distributions.
          </p>
        </div>
      ) : (
        <>
          {/* Latency Breakdown Metric Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Avg EOU → Audio</span>
                <Zap size={18} color="#10b981" />
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#34d399' }}>
                {data.avg_latency_ms.toFixed(0)} <span style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>ms</span>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Total speech-to-speech delay</span>
            </div>

            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Avg Faster-Whisper</span>
                <Cpu size={18} color="#818cf8" />
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
                {data.avg_stt_ms.toFixed(0)} <span style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>ms</span>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Speech recognition duration</span>
            </div>

            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Avg Acoustic SER</span>
                <Clock size={18} color="#f59e0b" />
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
                {data.avg_ser_ms.toFixed(0)} <span style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>ms</span>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Waveform emotion inference</span>
            </div>

            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Avg LLM TTFT</span>
                <MessageSquare size={18} color="#38bdf8" />
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
                {data.avg_llm_ttft_ms.toFixed(0)} <span style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>ms</span>
              </div>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Time to first generated token</span>
            </div>
          </div>

          {/* Emotion Distribution Breakdown */}
          <div className="glass-panel" style={{ padding: '28px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
              <PieChart size={20} color="#818cf8" />
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Acoustic Emotion Classification Distribution</h3>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              {Object.entries(data.emotion_distribution).map(([emotion, count]) => {
                const total = data.total_turns || 1;
                const pct = Math.round((count / total) * 100);

                const getBarColor = (em: string) => {
                  switch (em) {
                    case 'calm': return '#10b981';
                    case 'anxious': return '#f59e0b';
                    case 'agitated': return '#f97316';
                    case 'distressed': return '#ec4899';
                    case 'angry': return '#f43f5e';
                    default: return '#38bdf8';
                  }
                };

                const color = getBarColor(emotion);

                return (
                  <div key={emotion} style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                      <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{emotion}</span>
                      <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                        {count} turns ({pct}%)
                      </span>
                    </div>
                    <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${pct}%`,
                          height: '100%',
                          background: color,
                          borderRadius: '4px',
                          transition: 'width 0.5s ease',
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
