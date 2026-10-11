import React, { useState, useEffect, useRef } from 'react';
import { SessionState, ConversationTurn, LatencyBreakdown } from '../types';
import { AudioService } from '../services/audioService';
import { api } from '../services/api';
import { WaveformVisualizer } from '../components/WaveformVisualizer';
import { EmotionBadge } from '../components/EmotionBadge';
import { LatencyCard } from '../components/LatencyCard';
import {
  Mic,
  Square,
  AlertCircle,
  Clock,
  Radio,
  User,
  Bot,
  VolumeX,
  RefreshCw,
  Zap,
} from 'lucide-react';

export const LiveSessionPage: React.FC = () => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionState, setSessionState] = useState<SessionState>('idle');
  const [isVadActive, setIsVadActive] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [sessionDuration, setSessionDuration] = useState(0);

  // Active dialogue turns
  const [turns, setTurns] = useState<ConversationTurn[]>([]);
  const [currentTurn, setCurrentTurn] = useState<Partial<ConversationTurn>>({});
  const [latestLatency, setLatestLatency] = useState<LatencyBreakdown>({
    stt_duration_ms: 0,
    ser_duration_ms: 0,
    llm_ttft_ms: 0,
    llm_total_ms: 0,
    tts_ttfa_ms: 0,
    tts_total_ms: 0,
    total_latency_ms: 0,
  });

  const audioServiceRef = useRef<AudioService | null>(null);
  const turnsEndRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll conversation history
  useEffect(() => {
    turnsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns, currentTurn]);

  // Session duration timer
  useEffect(() => {
    let interval: number;
    if (sessionState !== 'idle' && sessionState !== 'disconnected' && sessionState !== 'error') {
      interval = window.setInterval(() => {
        setSessionDuration((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [sessionState]);

  const handleStartSession = async () => {
    setErrorMessage(null);
    try {
      // 1. Create session in backend SQLite
      const sess = await api.createSession('crisis_negotiation');
      setSessionId(sess.session_id);
      setSessionDuration(0);
      setTurns([]);
      setCurrentTurn({});

      // 2. Instantiate AudioService
      const service = new AudioService({
        onStateChange: (state) => setSessionState(state),
        onVADActive: (speaking) => setIsVadActive(speaking),
        onTranscription: (data) => {
          setCurrentTurn((prev) => ({
            ...prev,
            turn_index: data.turnIndex,
            user_transcript: data.transcript,
            detected_emotion: data.emotion,
            emotion_confidence: data.confidence,
            metrics: {
              ...latestLatency,
              stt_duration_ms: data.sttMs,
              ser_duration_ms: data.serMs,
            },
          }));
          setLatestLatency((prev) => ({
            ...prev,
            stt_duration_ms: data.sttMs,
            ser_duration_ms: data.serMs,
          }));
        },
        onLLMResponse: (data) => {
          setCurrentTurn((prev) => ({
            ...prev,
            ai_response: data.response,
            metrics: {
              ...(prev.metrics || latestLatency),
              llm_ttft_ms: data.llmTtftMs,
              llm_total_ms: data.llmTotalMs,
            },
          }));
          setLatestLatency((prev) => ({
            ...prev,
            llm_ttft_ms: data.llmTtftMs,
            llm_total_ms: data.llmTotalMs,
          }));
        },
        onAudioOutput: (data) => {
          const finalMetrics: LatencyBreakdown = {
            ...latestLatency,
            tts_ttfa_ms: data.ttsTtfaMs,
            tts_total_ms: data.ttsTotalMs,
            total_latency_ms: data.totalLatencyMs,
          };
          setLatestLatency(finalMetrics);

          setCurrentTurn((prev) => {
            if (prev.user_transcript && prev.ai_response) {
              const completed: ConversationTurn = {
                turn_index: data.turnIndex,
                user_transcript: prev.user_transcript,
                detected_emotion: prev.detected_emotion || 'neutral',
                emotion_confidence: prev.emotion_confidence || 0.5,
                ai_response: prev.ai_response,
                metrics: finalMetrics,
                created_at: new Date().toISOString(),
              };
              setTurns((tList) => [...tList, completed]);
              return {};
            }
            return prev;
          });
        },
        onInterrupted: () => {
          setSessionState('interrupted');
          setCurrentTurn((prev) => ({
            ...prev,
            was_interrupted: true,
          }));
          setTimeout(() => {
            setSessionState('listening');
          }, 1200);
        },
        onError: (err) => {
          setErrorMessage(err);
        },
      });

      audioServiceRef.current = service;
      await service.startSession(sess.session_id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to initialize audio stream';
      setErrorMessage(msg);
      setSessionState('error');
    }
  };

  const handleEndSession = async () => {
    if (audioServiceRef.current) {
      audioServiceRef.current.stopSession();
      audioServiceRef.current = null;
    }
    if (sessionId) {
      try {
        await api.terminateSession(sessionId);
      } catch (e) {
        console.error('Error terminating session', e);
      }
    }
    setSessionState('idle');
  };

  const handleInterrupt = () => {
    if (audioServiceRef.current) {
      audioServiceRef.current.interrupt();
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Top Session Control Header */}
      <div
        className="glass-panel"
        style={{
          padding: '20px 28px',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background:
                sessionState === 'speaking'
                  ? 'rgba(16, 185, 129, 0.2)'
                  : sessionState === 'listening'
                  ? 'rgba(6, 182, 212, 0.2)'
                  : 'rgba(99, 102, 241, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Radio
              size={22}
              color={
                sessionState === 'speaking'
                  ? '#10b981'
                  : sessionState === 'listening'
                  ? '#06b6d4'
                  : '#818cf8'
              }
            />
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Crisis Negotiation Simulator</h2>
              <span
                className={`status-pill ${
                  sessionState === 'speaking' || sessionState === 'listening'
                    ? 'status-online'
                    : sessionState === 'interrupted' || sessionState === 'error'
                    ? 'status-danger'
                    : 'status-warning'
                }`}
              >
                {sessionState.toUpperCase()}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              <span>Subject: Jordan (Barricaded Individual)</span>
              <span>•</span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Clock size={12} />
                {formatDuration(sessionDuration)}
              </span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {sessionState === 'speaking' && (
            <button
              className="btn btn-secondary"
              onClick={handleInterrupt}
              title="Barge-in / Interrupt Jordan's active speech"
              style={{ color: '#fb7185', borderColor: 'rgba(244, 63, 94, 0.3)' }}
            >
              <VolumeX size={16} />
              <span>Barge-In (Interrupt)</span>
            </button>
          )}

          {sessionState === 'idle' || sessionState === 'disconnected' || sessionState === 'error' ? (
            <button className="btn btn-primary" onClick={handleStartSession}>
              <Mic size={18} />
              <span>Start Voice Session</span>
            </button>
          ) : (
            <button className="btn btn-danger" onClick={handleEndSession}>
              <Square size={16} />
              <span>End Session</span>
            </button>
          )}
        </div>
      </div>

      {/* Error recovery instructions banner if error state */}
      {errorMessage && (
        <div
          className="glass-panel"
          style={{
            padding: '16px 20px',
            backgroundColor: 'rgba(244, 63, 94, 0.1)',
            borderColor: 'rgba(244, 63, 94, 0.3)',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px',
          }}
        >
          <AlertCircle size={20} color="#fb7185" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div style={{ flex: 1, fontSize: '0.875rem' }}>
            <div style={{ fontWeight: 600, color: '#fb7185', marginBottom: '4px' }}>
              Connection or Audio Device Issue
            </div>
            <div style={{ color: 'var(--text-main)', marginBottom: '8px' }}>{errorMessage}</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', lineHeight: 1.5 }}>
              <strong>Recovery steps:</strong> 1) Grant browser microphone permission in the address bar lock icon.
              2) Ensure the FastAPI backend server is running on port 8000. 3) Click "Start Voice Session" again to reconnect.
            </div>
          </div>
          <button className="btn btn-secondary" onClick={handleStartSession} style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
            <RefreshCw size={14} />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Waveform & Audio Spectrum Visualizer */}
      <div className="glass-panel" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={16} color="#38bdf8" />
            <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>Real-Time Web Audio Stream</span>
          </div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
            {sessionState === 'listening' ? 'Microphone Active (16kHz PCM)' : 'Full-Duplex Pipeline'}
          </span>
        </div>
        <WaveformVisualizer
          analyser={audioServiceRef.current ? audioServiceRef.current.getAnalyser() : null}
          state={sessionState}
          isVadActive={isVadActive}
        />
      </div>

      {/* Live Acoustic Emotion & Latency Telemetry */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        {/* Emotion Card */}
        <div className="glass-panel" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Detected Acoustic Emotion
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Acoustic Prosody Analysis</span>
          </div>
          <EmotionBadge
            emotion={currentTurn.detected_emotion || turns[turns.length - 1]?.detected_emotion || 'neutral'}
            confidence={currentTurn.emotion_confidence || turns[turns.length - 1]?.emotion_confidence || 0.65}
            showDetails={true}
          />
        </div>

        {/* Real Latency Metrics */}
        <LatencyCard metrics={latestLatency} />
      </div>

      {/* Conversation Turns & Dialog Log */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '12px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Dialogue Stream & Transcripts</h3>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
            {turns.length + (currentTurn.user_transcript ? 1 : 0)} turns in session
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', minHeight: '200px', maxHeight: '420px', overflowY: 'auto', paddingRight: '8px' }}>
          {turns.length === 0 && !currentTurn.user_transcript && (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-dim)' }}>
              <Mic size={32} style={{ marginBottom: '8px', opacity: 0.5 }} />
              <p style={{ fontSize: '0.9rem' }}>
                {sessionState === 'listening'
                  ? 'Speak into your microphone. Say something de-escalating like: "Jordan, I hear you, let us talk this through calmly."'
                  : 'Click "Start Voice Session" to begin training.'}
              </p>
            </div>
          )}

          {/* Past Turns */}
          {turns.map((turn, idx) => (
            <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {/* Trainee Speech Bubble */}
              <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <User size={16} color="#38bdf8" />
                </div>
                <div style={{ flex: 1, background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-subtle)', borderRadius: '12px', padding: '12px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#38bdf8' }}>Trainee (Negotiator)</span>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <EmotionBadge emotion={turn.detected_emotion} confidence={turn.emotion_confidence} showDetails={false} />
                      <LatencyCard metrics={turn.metrics} compact={true} />
                    </div>
                  </div>
                  <p style={{ fontSize: '0.95rem', lineHeight: 1.5, color: 'var(--text-main)' }}>
                    "{turn.user_transcript}"
                  </p>
                </div>
              </div>

              {/* Jordan AI Response Bubble */}
              <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', paddingLeft: '24px' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <Bot size={16} color="#10b981" />
                </div>
                <div style={{ flex: 1, background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: '12px', padding: '12px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#34d399' }}>Jordan (Barricaded Subject)</span>
                    {turn.was_interrupted && (
                      <span className="status-pill status-danger" style={{ fontSize: '0.65rem' }}>
                        INTERRUPTED
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: '0.95rem', lineHeight: 1.5, color: 'var(--text-main)' }}>
                    "{turn.ai_response}"
                  </p>
                </div>
              </div>
            </div>
          ))}

          {/* Live In-Progress Turn */}
          {currentTurn.user_transcript && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  <User size={16} color="#38bdf8" />
                </div>
                <div style={{ flex: 1, background: 'rgba(56, 189, 248, 0.05)', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '12px', padding: '12px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#38bdf8' }}>Trainee (Transcribed)</span>
                    {currentTurn.detected_emotion && (
                      <EmotionBadge emotion={currentTurn.detected_emotion} confidence={currentTurn.emotion_confidence} showDetails={false} />
                    )}
                  </div>
                  <p style={{ fontSize: '0.95rem', lineHeight: 1.5, color: 'var(--text-main)' }}>
                    "{currentTurn.user_transcript}"
                  </p>
                </div>
              </div>

              {currentTurn.ai_response && (
                <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', paddingLeft: '24px' }}>
                  <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Bot size={16} color="#10b981" />
                  </div>
                  <div style={{ flex: 1, background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '12px', padding: '12px 16px' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#34d399', display: 'block', marginBottom: '6px' }}>
                      Jordan (Speaking...)
                    </span>
                    <p style={{ fontSize: '0.95rem', lineHeight: 1.5, color: 'var(--text-main)' }}>
                      "{currentTurn.ai_response}"
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          <div ref={turnsEndRef} />
        </div>
      </div>
    </div>
  );
};
