import React from 'react';
import { LatencyBreakdown } from '../types';
import { Zap, Clock, Cpu, MessageSquare, Volume2 } from 'lucide-react';

interface LatencyCardProps {
  metrics: LatencyBreakdown;
  compact?: boolean;
}

export const LatencyCard: React.FC<LatencyCardProps> = ({ metrics, compact = false }) => {
  const isSubTarget = metrics.total_latency_ms > 0 && metrics.total_latency_ms <= 800;

  if (compact) {
    return (
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '12px',
          padding: '6px 12px',
          borderRadius: '8px',
          background: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid var(--border-subtle)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.78rem',
        }}
      >
        <span style={{ color: 'var(--text-muted)' }}>EOU → Audio:</span>
        <span
          style={{
            fontWeight: 700,
            color: isSubTarget ? '#10b981' : metrics.total_latency_ms > 1500 ? '#f59e0b' : '#38bdf8',
          }}
        >
          {metrics.total_latency_ms.toFixed(0)} ms
        </span>
      </div>
    );
  }

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Zap size={18} color="#38bdf8" />
          <h4 style={{ fontSize: '1rem', fontWeight: 600 }}>Measured Telemetry & Latency</h4>
        </div>
        <div
          className="status-pill"
          style={{
            backgroundColor: isSubTarget ? 'rgba(16, 185, 129, 0.15)' : 'rgba(56, 189, 248, 0.15)',
            color: isSubTarget ? '#34d399' : '#38bdf8',
            borderColor: isSubTarget ? 'rgba(16, 185, 129, 0.3)' : 'rgba(56, 189, 248, 0.3)',
          }}
        >
          EOU → Audio: {metrics.total_latency_ms.toFixed(0)} ms
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '12px' }}>
        {/* STT */}
        <div
          style={{
            padding: '12px',
            borderRadius: '10px',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '4px' }}>
            <Cpu size={14} color="#818cf8" />
            <span>STT (Whisper)</span>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
            {metrics.stt_duration_ms.toFixed(0)} <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>ms</span>
          </div>
        </div>

        {/* SER */}
        <div
          style={{
            padding: '12px',
            borderRadius: '10px',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '4px' }}>
            <Clock size={14} color="#f59e0b" />
            <span>SER (Prosody)</span>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
            {metrics.ser_duration_ms.toFixed(0)} <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>ms</span>
          </div>
        </div>

        {/* LLM TTFT */}
        <div
          style={{
            padding: '12px',
            borderRadius: '10px',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '4px' }}>
            <MessageSquare size={14} color="#38bdf8" />
            <span>LLM TTFT</span>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
            {metrics.llm_ttft_ms.toFixed(0)} <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>ms</span>
          </div>
        </div>

        {/* TTS TTFA */}
        <div
          style={{
            padding: '12px',
            borderRadius: '10px',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '4px' }}>
            <Volume2 size={14} color="#10b981" />
            <span>TTS TTFA</span>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
            {metrics.tts_ttfa_ms.toFixed(0)} <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>ms</span>
          </div>
        </div>
      </div>
    </div>
  );
};
