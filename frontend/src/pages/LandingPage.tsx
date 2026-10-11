import React from 'react';
import {
  Mic,
  Activity,
  Cpu,
  Volume2,
  Shield,
  Zap,
  ArrowRight,
  Lock,
  Server,
  Layers,
} from 'lucide-react';

interface LandingPageProps {
  onStartTraining: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onStartTraining }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '48px', paddingBottom: '60px' }}>
      {/* Hero Section */}
      <section
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          gap: '24px',
          padding: '48px 0 24px',
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 14px',
            borderRadius: '999px',
            background: 'rgba(99, 102, 241, 0.1)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            color: '#818cf8',
            fontSize: '0.85rem',
            fontWeight: 600,
          }}
        >
          <Activity size={16} />
          <span>Real-Time Voice-to-Voice Emotion Engine</span>
        </div>

        <h1
          style={{
            fontSize: 'clamp(2.5rem, 5vw, 4rem)',
            fontWeight: 800,
            lineHeight: 1.1,
            maxWidth: '900px',
            background: 'linear-gradient(135deg, #ffffff 30%, #94a3b8 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Crisis Negotiation Training Powered by Acoustic Emotion Intelligence
        </h1>

        <p
          style={{
            fontSize: '1.15rem',
            color: 'var(--text-muted)',
            maxWidth: '720px',
            lineHeight: 1.6,
          }}
        >
          Auralis captures micro-prosodic voice cues, pitch jitter, and vocal strain in real time.
          Experience full-duplex de-escalation simulations with sub-second latency and emotion-adapted
          neural speech synthesis.
        </p>

        <div style={{ display: 'flex', gap: '16px', marginTop: '12px' }}>
          <button
            className="btn btn-primary"
            onClick={onStartTraining}
            style={{ fontSize: '1.05rem', padding: '14px 28px', borderRadius: '12px' }}
          >
            <Mic size={20} />
            <span>Launch Negotiation Session</span>
            <ArrowRight size={18} />
          </button>
        </div>
      </section>

      {/* Interactive Voice Processing Pipeline Diagram */}
      <section className="glass-panel" style={{ padding: '36px' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '8px' }}>
            Auralis Real-Time Voice Processing Pipeline
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Low-latency audio transport to cognitive de-escalation engine
          </p>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '16px',
            position: 'relative',
          }}
        >
          {[
            {
              step: '01',
              title: 'Mic & VAD Stream',
              desc: '16kHz float32 audio capture, pre-speech ring buffer & energy onset check.',
              icon: Mic,
              color: '#38bdf8',
            },
            {
              step: '02',
              title: 'Faster-Whisper STT',
              desc: 'High-speed quantized speech recognition transcribing raw speech.',
              icon: Cpu,
              color: '#818cf8',
            },
            {
              step: '03',
              title: 'Acoustic SER',
              desc: 'Direct waveform analysis: F0 pitch variance, RMS energy, spectral centroid.',
              icon: Activity,
              color: '#f59e0b',
            },
            {
              step: '04',
              title: 'Contextual LLM',
              desc: 'Crisis persona adjusts hostility/vulnerability based on trainee emotion.',
              icon: Layers,
              color: '#6366f1',
            },
            {
              step: '05',
              title: 'Neural TTS & Full-Duplex',
              desc: 'Expressive audio streaming back to trainee; instant cut-off on interruption.',
              icon: Volume2,
              color: '#10b981',
            },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.step}
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '14px',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  position: 'relative',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div
                    style={{
                      width: '36px',
                      height: '36px',
                      borderRadius: '8px',
                      background: `rgba(${item.color === '#38bdf8' ? '56, 189, 248' : item.color === '#818cf8' ? '129, 140, 248' : item.color === '#f59e0b' ? '245, 158, 11' : item.color === '#10b981' ? '16, 185, 129' : '99, 102, 241'}, 0.15)`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Icon size={18} color={item.color} />
                  </div>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.8rem',
                      color: 'var(--text-dim)',
                    }}
                  >
                    {item.step}
                  </span>
                </div>
                <div>
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '4px' }}>
                    {item.title}
                  </h3>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: 1.5 }}>
                    {item.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Feature Capabilities Grid */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        <div className="glass-panel" style={{ padding: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px' }}>
            <Activity size={22} color="#f59e0b" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 600 }}>Acoustic Emotion Estimation</h3>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.6 }}>
            Unlike models that merely read transcription text, Auralis models vocal prosody directly from raw audio:
            pitch jitter, vocal tension, spectral brightness, and amplitude spikes to detect calm, agitation, distress, or hostility.
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px' }}>
            <Zap size={22} color="#10b981" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 600 }}>Full-Duplex Interruption Handling</h3>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.6 }}>
            Natural conversation requires barge-in capability. When the trainee begins speaking during active AI speech,
            Auralis detects voice onset, immediately terminates audio synthesis, and transitions back to active listening.
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '14px' }}>
            <Shield size={22} color="#6366f1" />
            <h3 style={{ fontSize: '1.15rem', fontWeight: 600 }}>Crisis Negotiation Simulator</h3>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.6 }}>
            Trainees practice high-stakes de-escalation against Jordan, a barricaded individual whose demeanor adapts in real time
            based on the trainee's empathy, tone stability, and verbal reassurance.
          </p>
        </div>
      </section>

      {/* Privacy and System Requirements */}
      <section
        className="glass-panel"
        style={{
          padding: '24px 32px',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '24px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Lock size={24} color="#34d399" />
          <div>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Privacy by Design</h4>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
              Raw audio is processed transiently in-memory and discarded. Only session metadata and telemetry are stored in SQLite.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Server size={24} color="#818cf8" />
          <div>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>System Requirements</h4>
            <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>
              Modern browser with Web Audio API & microphone access. Backend supports CPU inference or GPU acceleration.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
