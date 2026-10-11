import React from 'react';
import { EmotionType } from '../types';
import { ShieldCheck, AlertTriangle, Flame, HeartCrack, Smile } from 'lucide-react';

interface EmotionBadgeProps {
  emotion?: EmotionType;
  confidence?: number;
  showDetails?: boolean;
}

export const EmotionBadge: React.FC<EmotionBadgeProps> = ({
  emotion = 'neutral',
  confidence = 0.5,
  showDetails = true,
}) => {
  const getMeta = (em: EmotionType) => {
    switch (em) {
      case 'calm':
        return {
          label: 'Calm / De-escalated',
          color: '#10b981',
          bg: 'rgba(16, 185, 129, 0.12)',
          border: 'rgba(16, 185, 129, 0.3)',
          icon: ShieldCheck,
          desc: 'Low jitter, steady pitch baseline, controlled vocal dynamics.',
        };
      case 'anger':
        return {
          label: 'Anger / Agitated',
          color: '#f43f5e',
          bg: 'rgba(244, 63, 94, 0.12)',
          border: 'rgba(244, 63, 94, 0.3)',
          icon: Flame,
          desc: 'High RMS energy, abrupt onsets, elevated fundamental frequency.',
        };
      case 'fear_panic':
        return {
          label: 'Fear / Panic',
          color: '#f59e0b',
          bg: 'rgba(245, 158, 11, 0.12)',
          border: 'rgba(245, 158, 11, 0.3)',
          icon: AlertTriangle,
          desc: 'Elevated pitch, rapid jitter variance, high spectral tension.',
        };
      case 'sadness':
        return {
          label: 'Sadness / Subdued',
          color: '#818cf8',
          bg: 'rgba(129, 140, 248, 0.12)',
          border: 'rgba(129, 140, 248, 0.3)',
          icon: HeartCrack,
          desc: 'Depressed F0 mean, low acoustic energy, flat pitch trajectory.',
        };
      case 'neutral':
      default:
        return {
          label: 'Neutral Baseline',
          color: '#38bdf8',
          bg: 'rgba(56, 189, 248, 0.12)',
          border: 'rgba(56, 189, 248, 0.3)',
          icon: Smile,
          desc: 'Balanced acoustic spectrum, stable fundamental frequency.',
        };
    }
  };

  const meta = getMeta(emotion);
  const IconComponent = meta.icon;
  const pct = Math.round(confidence * 100);

  return (
    <div
      style={{
        display: 'inline-flex',
        flexDirection: 'column',
        gap: '4px',
        padding: '8px 14px',
        borderRadius: '12px',
        backgroundColor: meta.bg,
        border: `1px solid ${meta.border}`,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <IconComponent size={16} color={meta.color} />
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: meta.color }}>
            {meta.label}
          </span>
        </div>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.78rem',
            color: meta.color,
            fontWeight: 700,
          }}
        >
          {pct}%
        </span>
      </div>

      {showDetails && (
        <>
          <div
            style={{
              width: '100%',
              height: '4px',
              backgroundColor: 'rgba(255,255,255,0.08)',
              borderRadius: '2px',
              overflow: 'hidden',
              marginTop: '2px',
            }}
          >
            <div
              style={{
                width: `${pct}%`,
                height: '100%',
                backgroundColor: meta.color,
                borderRadius: '2px',
                transition: 'width 0.4s ease',
              }}
            />
          </div>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '2px' }}>
            {meta.desc}
          </span>
        </>
      )}
    </div>
  );
};
