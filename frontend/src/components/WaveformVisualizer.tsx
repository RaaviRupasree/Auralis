import React, { useEffect, useRef } from 'react';
import { SessionState } from '../types';

interface WaveformVisualizerProps {
  analyser: AnalyserNode | null;
  state: SessionState;
  isVadActive?: boolean;
}

export const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({
  analyser,
  state,
  isVadActive = false,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    const bufferLength = analyser ? analyser.frequencyBinCount : 64;
    const dataArray = new Uint8Array(bufferLength);

    const render = () => {
      animationId = requestAnimationFrame(render);

      const width = canvas.width;
      const height = canvas.height;

      ctx.clearRect(0, 0, width, height);

      // Background gradient
      const bgGrad = ctx.createLinearGradient(0, 0, width, height);
      bgGrad.addColorStop(0, 'rgba(10, 15, 30, 0.4)');
      bgGrad.addColorStop(1, 'rgba(5, 8, 16, 0.6)');
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);

      if (analyser && state !== 'idle' && state !== 'disconnected') {
        analyser.getByteFrequencyData(dataArray);
      } else {
        // Idle gentle wave animation
        for (let i = 0; i < bufferLength; i++) {
          dataArray[i] = Math.sin(Date.now() * 0.003 + i * 0.1) * 12 + 16;
        }
      }

      // Bar color selection based on state
      let barGrad = ctx.createLinearGradient(0, height, 0, 0);
      if (state === 'speaking') {
        barGrad.addColorStop(0, '#10b981');
        barGrad.addColorStop(1, '#6ee7b7');
      } else if (state === 'interrupted') {
        barGrad.addColorStop(0, '#f43f5e');
        barGrad.addColorStop(1, '#fda4af');
      } else if (state === 'generating' || state === 'processing') {
        barGrad.addColorStop(0, '#6366f1');
        barGrad.addColorStop(1, '#a855f7');
      } else if (isVadActive) {
        barGrad.addColorStop(0, '#06b6d4');
        barGrad.addColorStop(1, '#38bdf8');
      } else {
        barGrad.addColorStop(0, 'rgba(99, 102, 241, 0.4)');
        barGrad.addColorStop(1, 'rgba(6, 182, 212, 0.6)');
      }

      const numBars = 48;
      const barWidth = (width / numBars) * 0.7;
      const gap = (width / numBars) * 0.3;

      for (let i = 0; i < numBars; i++) {
        const step = Math.floor((i / numBars) * bufferLength * 0.7);
        const value = dataArray[step] || 8;
        const percent = Math.min(1, Math.max(0.08, value / 255));
        const barHeight = percent * (height * 0.85);

        const x = i * (barWidth + gap) + gap / 2;
        const y = (height - barHeight) / 2;

        ctx.fillStyle = barGrad;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, [4, 4, 4, 4]);
        ctx.fill();

        // Subtle glow reflection
        ctx.shadowColor = state === 'speaking' ? '#10b981' : '#06b6d4';
        ctx.shadowBlur = isVadActive || state === 'speaking' ? 12 : 4;
      }
      ctx.shadowBlur = 0;
    };

    render();

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [analyser, state, isVadActive]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '160px', borderRadius: '16px', overflow: 'hidden' }}>
      <canvas
        ref={canvasRef}
        width={700}
        height={160}
        style={{ width: '100%', height: '100%', display: 'block' }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: '12px',
          left: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '0.78rem',
          color: 'var(--text-muted)',
          background: 'rgba(0,0,0,0.5)',
          padding: '4px 10px',
          borderRadius: '999px',
          backdropFilter: 'blur(4px)',
        }}
      >
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background:
              state === 'speaking'
                ? '#10b981'
                : state === 'interrupted'
                ? '#f43f5e'
                : state === 'listening'
                ? '#06b6d4'
                : '#6366f1',
          }}
        />
        <span>
          {state === 'speaking'
            ? 'Jordan Speaking (AI TTS)'
            : state === 'listening'
            ? isVadActive
              ? 'Trainee Speech Detected...'
              : 'Listening for Trainee Voice'
            : state === 'interrupted'
            ? 'Interrupted'
            : state === 'generating'
            ? 'Synthesizing De-escalation...'
            : state === 'processing'
            ? 'Analyzing Acoustic Emotion...'
            : state.toUpperCase()}
        </span>
      </div>
    </div>
  );
};
