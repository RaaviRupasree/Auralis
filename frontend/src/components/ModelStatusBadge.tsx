import React from 'react';
import { ModelStatus } from '../types';
import { CheckCircle2, AlertCircle } from 'lucide-react';

interface ModelStatusBadgeProps {
  status: ModelStatus | null;
  loading?: boolean;
}

export const ModelStatusBadge: React.FC<ModelStatusBadgeProps> = ({ status, loading }) => {
  if (loading || !status) {
    return (
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
        <span className="spinner" style={{ width: '12px', height: '12px', border: '2px solid var(--primary)', borderTopColor: 'transparent', borderRadius: '50%' }} />
        <span>Polling system models...</span>
      </div>
    );
  }

  const items = [
    { name: `STT (${status.whisper_model})`, ok: status.whisper_ready },
    { name: `SER (${status.ser_model})`, ok: status.ser_ready },
    { name: `LLM (${status.llm_provider})`, ok: status.llm_connected },
    { name: `TTS (${status.tts_engine})`, ok: status.tts_ready },
  ];

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
      {items.map((it) => (
        <div
          key={it.name}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 10px',
            borderRadius: '8px',
            background: it.ok ? 'rgba(16, 185, 129, 0.08)' : 'rgba(245, 158, 11, 0.08)',
            border: `1px solid ${it.ok ? 'rgba(16, 185, 129, 0.25)' : 'rgba(245, 158, 11, 0.25)'}`,
            fontSize: '0.78rem',
            color: it.ok ? '#34d399' : '#fbbf24',
          }}
        >
          {it.ok ? <CheckCircle2 size={12} /> : <AlertCircle size={12} />}
          <span>{it.name}</span>
        </div>
      ))}
    </div>
  );
};
