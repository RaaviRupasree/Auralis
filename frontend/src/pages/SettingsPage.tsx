import React, { useState, useEffect } from 'react';
import { AppConfig } from '../types';
import { api } from '../services/api';
import {
  Save,
  CheckCircle2,
  Volume2,
  Cpu,
  Sliders,
  Terminal,
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Form states
  const [llmProvider, setLlmProvider] = useState('ollama');
  const [ollamaBaseUrl, setOllamaBaseUrl] = useState('http://localhost:11434');
  const [ollamaModel, setOllamaModel] = useState('llama3.2');
  const [openaiKey, setOpenaiKey] = useState('');
  const [openaiModel, setOpenaiModel] = useState('gpt-4o-mini');
  const [ttsVoice, setTtsVoice] = useState('en-US-ChristopherNeural');
  const [vadThreshold, setVadThreshold] = useState(0.015);
  const [vadSilenceDuration, setVadSilenceDuration] = useState(600);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const cfg = await api.getConfig();
      setConfig(cfg);
      setLlmProvider(cfg.llm_provider);
      setOllamaBaseUrl(cfg.ollama_base_url);
      setOllamaModel(cfg.ollama_model);
      setOpenaiModel(cfg.openai_model);
      setTtsVoice(cfg.tts_voice);
      setVadThreshold(cfg.vad_energy_threshold);
      setVadSilenceDuration(cfg.vad_silence_duration_ms);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.updateConfig({
        llm_provider: llmProvider,
        ollama_base_url: ollamaBaseUrl,
        ollama_model: ollamaModel,
        openai_api_key: openaiKey || undefined,
        openai_model: openaiModel,
        tts_voice: ttsVoice,
        vad_energy_threshold: vadThreshold,
        vad_silence_duration_ms: vadSilenceDuration,
      });
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
      loadConfig();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', maxWidth: '850px' }}>
      <div>
        <h2 style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: '6px' }}>
          Engine & Model Configuration
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          Adjust conversational AI providers, speech parameters, and Voice Activity Detection sensitivity.
        </p>
      </div>

      {savedSuccess && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 18px',
            borderRadius: '10px',
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#34d399',
            fontSize: '0.9rem',
          }}
        >
          <CheckCircle2 size={18} />
          <span>Configuration saved and updated in active pipeline!</span>
        </div>
      )}

      <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* LLM Provider Configuration */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <Cpu size={18} color="#818cf8" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Conversational LLM Provider</h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-muted)', marginBottom: '8px' }}>
                Provider Architecture
              </label>
              <select
                value={llmProvider}
                onChange={(e) => setLlmProvider(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)',
                  fontSize: '0.9rem',
                  outline: 'none',
                }}
              >
                <option value="ollama">Ollama (Local Llama 3.2 / Mistral / DeepSeek)</option>
                <option value="openai">OpenAI Compatible (GPT-4o / Cloud Endpoint)</option>
                <option value="heuristic_fallback">Resilient Heuristic Fallback (Zero external dependency)</option>
              </select>
            </div>

            {llmProvider === 'ollama' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Ollama Endpoint URL
                  </label>
                  <input
                    type="text"
                    value={ollamaBaseUrl}
                    onChange={(e) => setOllamaBaseUrl(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px',
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.04)',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-main)',
                      fontSize: '0.85rem',
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Model Identifier
                  </label>
                  <input
                    type="text"
                    value={ollamaModel}
                    onChange={(e) => setOllamaModel(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px',
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.04)',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-main)',
                      fontSize: '0.85rem',
                    }}
                  />
                </div>
              </div>
            )}

            {llmProvider === 'openai' && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                    OpenAI API Key {config?.has_openai_key && `(Active: ${config.openai_key_preview})`}
                  </label>
                  <input
                    type="password"
                    placeholder="sk-..."
                    value={openaiKey}
                    onChange={(e) => setOpenaiKey(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px',
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.04)',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-main)',
                      fontSize: '0.85rem',
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.825rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Model
                  </label>
                  <input
                    type="text"
                    value={openaiModel}
                    onChange={(e) => setOpenaiModel(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '10px',
                      borderRadius: '8px',
                      background: 'rgba(255,255,255,0.04)',
                      border: '1px solid var(--border-subtle)',
                      color: 'var(--text-main)',
                      fontSize: '0.85rem',
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* TTS Voice Configuration */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <Volume2 size={18} color="#10b981" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Speech Synthesis (TTS) Engine</h3>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-muted)', marginBottom: '8px' }}>
              Jordan Voice Persona (Neural Edge-TTS)
            </label>
            <select
              value={ttsVoice}
              onChange={(e) => setTtsVoice(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 14px',
                borderRadius: '8px',
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-main)',
                fontSize: '0.9rem',
                outline: 'none',
              }}
            >
              <option value="en-US-ChristopherNeural">Christopher (Natural, Dynamic, Authentic American)</option>
              <option value="en-US-GuyNeural">Guy (Authoritative, Expressive)</option>
              <option value="en-US-EricNeural">Eric (Neutral, Deep)</option>
              <option value="en-US-JennyNeural">Jenny (Expressive, Natural Female Voice)</option>
            </select>
          </div>
        </div>

        {/* VAD Sensitivity Configuration */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
            <Sliders size={18} color="#06b6d4" />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Voice Activity Detection (VAD) Tuning</h3>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>Energy Threshold</label>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.825rem', color: '#06b6d4' }}>
                  {vadThreshold.toFixed(3)}
                </span>
              </div>
              <input
                type="range"
                min="0.005"
                max="0.06"
                step="0.002"
                value={vadThreshold}
                onChange={(e) => setVadThreshold(parseFloat(e.target.value))}
                style={{ width: '100%' }}
              />
              <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                Lower = more sensitive to soft voices. Higher = filters room background noise.
              </span>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <label style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>Silence Hang-time (EOU)</label>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.825rem', color: '#06b6d4' }}>
                  {vadSilenceDuration} ms
                </span>
              </div>
              <input
                type="range"
                min="350"
                max="1200"
                step="50"
                value={vadSilenceDuration}
                onChange={(e) => setVadSilenceDuration(parseInt(e.target.value))}
                style={{ width: '100%' }}
              />
              <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                Pause required before finalizing utterance. Prevents cutting off mid-sentence.
              </span>
            </div>
          </div>
        </div>

        {/* Save button */}
        <button
          type="submit"
          className="btn btn-primary"
          style={{ alignSelf: 'flex-start', padding: '12px 24px' }}
        >
          <Save size={18} />
          <span>Save Pipeline Configuration</span>
        </button>
      </form>

      {/* Local Setup Guidance Banner */}
      <div className="glass-panel" style={{ padding: '24px', background: 'rgba(255,255,255,0.01)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
          <Terminal size={18} color="#818cf8" />
          <h4 style={{ fontSize: '0.95rem', fontWeight: 600 }}>Ollama Local Deployment Guide</h4>
        </div>
        <p style={{ fontSize: '0.825rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
          To run local Llama 3.2 on this machine: Install Ollama from <code>ollama.com</code>, then run in your shell:{' '}
          <code style={{ background: 'rgba(0,0,0,0.4)', padding: '2px 6px', borderRadius: '4px', color: '#38bdf8' }}>
            ollama run llama3.2
          </code>
          . Auralis will automatically detect and bind to port 11434.
        </p>
      </div>
    </div>
  );
};
