import React from 'react';
import { ModelStatus } from '../types';
import { ModelStatusBadge } from './ModelStatusBadge';
import { Mic, Radio } from 'lucide-react';

interface NavbarProps {
  modelStatus: ModelStatus | null;
  loadingModels?: boolean;
  onStartSession: () => void;
  isSessionActive: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  modelStatus,
  loadingModels,
  onStartSession,
  isSessionActive,
}) => {
  return (
    <header
      style={{
        height: '64px',
        borderBottom: '1px solid var(--border-subtle)',
        backgroundColor: 'rgba(10, 14, 26, 0.75)',
        backdropFilter: 'blur(12px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 32px',
        position: 'sticky',
        top: 0,
        zIndex: 40,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Radio size={16} color="#10b981" />
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)' }}>
            System Pipeline
          </span>
        </div>
        <ModelStatusBadge status={modelStatus} loading={loadingModels} />
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <button
          className={isSessionActive ? 'btn btn-danger' : 'btn btn-primary'}
          onClick={onStartSession}
          style={{ fontSize: '0.85rem', padding: '8px 16px' }}
        >
          <Mic size={16} />
          <span>{isSessionActive ? 'In Voice Session' : 'Start Voice Session'}</span>
        </button>
      </div>
    </header>
  );
};
