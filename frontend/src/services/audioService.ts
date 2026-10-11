import { EmotionType, SessionState } from '../types';

export interface AudioServiceCallbacks {
  onStateChange: (state: SessionState) => void;
  onTranscription: (data: {
    turnIndex: number;
    transcript: string;
    sttMs: number;
    emotion: EmotionType;
    confidence: number;
    serMs: number;
  }) => void;
  onLLMResponse: (data: {
    turnIndex: number;
    response: string;
    llmTtftMs: number;
    llmTotalMs: number;
  }) => void;
  onAudioOutput: (data: {
    turnIndex: number;
    ttsTtfaMs: number;
    ttsTotalMs: number;
    totalLatencyMs: number;
  }) => void;
  onInterrupted: () => void;
  onError: (err: string) => void;
  onVADActive: (isSpeaking: boolean, db: number) => void;
}

export class AudioService {
  private audioContext: AudioContext | null = null;
  private mediaStream: MediaStream | null = null;
  private analyserNode: AnalyserNode | null = null;
  private processorNode: ScriptProcessorNode | null = null;
  private socket: WebSocket | null = null;
  private activeSources: AudioBufferSourceNode[] = [];
  private nextPlayTime = 0;
  private callbacks: AudioServiceCallbacks;
  private isInterrupted = false;

  constructor(callbacks: AudioServiceCallbacks) {
    this.callbacks = callbacks;
  }

  public getAnalyser(): AnalyserNode | null {
    return this.analyserNode;
  }

  public async startSession(sessionId: string): Promise<void> {
    try {
      this.callbacks.onStateChange('connecting');
      this.isInterrupted = false;

      // 1. Initialize Audio Context
      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.audioContext = new AudioCtx({ sampleRate: 16000 });
      if (this.audioContext.state === 'suspended') {
        await this.audioContext.resume();
      }

      // 2. Request real microphone permission
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // 3. Setup analyser node for live waveform visualization
      this.analyserNode = this.audioContext.createAnalyser();
      this.analyserNode.fftSize = 512;
      this.analyserNode.smoothingTimeConstant = 0.8;

      const micSource = this.audioContext.createMediaStreamSource(this.mediaStream);
      micSource.connect(this.analyserNode);

      // 4. Setup WebSocket connection
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/audio/${sessionId}`;
      this.socket = new WebSocket(wsUrl);
      this.socket.binaryType = 'arraybuffer';

      this.socket.onopen = () => {
        this.callbacks.onStateChange('listening');
        this.setupMicrophoneProcessor(micSource);
      };

      this.socket.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleServerEvent(data);
        } catch {
          // ignore non-json
        }
      };

      this.socket.onerror = () => {
        this.callbacks.onError('WebSocket connection error. Check backend server on port 8080.');
      };

      this.socket.onclose = () => {
        this.callbacks.onStateChange('disconnected');
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Microphone permission or connection failed';
      this.callbacks.onError(msg);
      this.callbacks.onStateChange('error');
      throw err;
    }
  }

  private setupMicrophoneProcessor(source: MediaStreamAudioSourceNode) {
    if (!this.audioContext) return;

    // Buffer size 2048 at 16kHz is ~128ms chunks
    this.processorNode = this.audioContext.createScriptProcessor(2048, 1, 1);

    this.processorNode.onaudioprocess = (e) => {
      if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;

      const inputData = e.inputBuffer.getChannelData(0);
      
      // Convert Float32 to 16-bit PCM for low-bandwidth streaming
      const pcm16 = new Int16Array(inputData.length);
      for (let i = 0; i < inputData.length; i++) {
        const s = Math.max(-1, Math.min(1, inputData[i]));
        pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }

      this.socket.send(pcm16.buffer);
    };

    // Route mic into processor and mute before destination to prevent speaker feedback loop
    const muteGain = this.audioContext.createGain();
    muteGain.gain.value = 0;
    source.connect(this.processorNode);
    this.processorNode.connect(muteGain);
    muteGain.connect(this.audioContext.destination);
  }

  private async handleServerEvent(event: {
    type: string;
    state?: SessionState;
    transcript?: string;
    stt_duration_ms?: number;
    detected_emotion?: EmotionType;
    emotion_confidence?: number;
    ser_duration_ms?: number;
    response_text?: string;
    llm_ttft_ms?: number;
    llm_total_ms?: number;
    audio_base64?: string;
    tts_ttfa_ms?: number;
    tts_total_ms?: number;
    total_latency_ms?: number;
    turn_index?: number;
    is_first?: boolean;
    is_speaking?: boolean;
    db?: number;
  }) {
    switch (event.type) {
      case 'state_change':
        if (event.state) this.callbacks.onStateChange(event.state);
        break;

      case 'vad_active':
        this.callbacks.onVADActive(Boolean(event.is_speaking), event.db ?? -100);
        break;

      case 'transcription':
        this.callbacks.onTranscription({
          turnIndex: event.turn_index ?? 1,
          transcript: event.transcript ?? '',
          sttMs: event.stt_duration_ms ?? 0,
          emotion: event.detected_emotion ?? 'neutral',
          confidence: event.emotion_confidence ?? 0.5,
          serMs: event.ser_duration_ms ?? 0,
        });
        break;

      case 'llm_response':
        this.callbacks.onLLMResponse({
          turnIndex: event.turn_index ?? 1,
          response: event.response_text ?? '',
          llmTtftMs: event.llm_ttft_ms ?? 0,
          llmTotalMs: event.llm_total_ms ?? 0,
        });
        break;

      case 'audio_chunk':
        if (event.audio_base64 && !this.isInterrupted) {
          if (event.is_first) {
            this.stopActivePlayback();
          }
          await this.playAudioBase64(event.audio_base64, false);
        }
        if (event.is_first && event.tts_ttfa_ms) {
          this.callbacks.onAudioOutput({
            turnIndex: event.turn_index ?? 1,
            ttsTtfaMs: event.tts_ttfa_ms,
            ttsTotalMs: event.total_latency_ms ?? 0,
            totalLatencyMs: event.total_latency_ms ?? 0,
          });
        }
        break;

      case 'audio_output':
        if (event.audio_base64 && this.activeSources.length === 0 && !this.isInterrupted) {
          await this.playAudioBase64(event.audio_base64, true);
        }
        this.callbacks.onAudioOutput({
          turnIndex: event.turn_index ?? 1,
          ttsTtfaMs: event.tts_ttfa_ms ?? 0,
          ttsTotalMs: event.tts_total_ms ?? 0,
          totalLatencyMs: event.total_latency_ms ?? 0,
        });
        break;

      case 'interrupted':
        this.isInterrupted = true;
        this.stopActivePlayback();
        this.callbacks.onInterrupted();
        break;

      case 'error':
        this.callbacks.onError('An error occurred during audio pipeline processing.');
        break;
    }
  }

  private async playAudioBase64(base64: string, stopExisting = false): Promise<void> {
    if (!this.audioContext || this.isInterrupted) return;

    try {
      const binaryString = atob(base64);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      const audioBuffer = await this.audioContext.decodeAudioData(bytes.buffer.slice(0));
      
      if (stopExisting) {
        this.stopActivePlayback();
      }

      const source = this.audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(this.audioContext.destination);

      const currentTime = this.audioContext.currentTime;
      const startTime = Math.max(currentTime, this.nextPlayTime);
      source.start(startTime);
      this.nextPlayTime = startTime + audioBuffer.duration;

      this.activeSources.push(source);

      source.onended = () => {
        const idx = this.activeSources.indexOf(source);
        if (idx !== -1) {
          this.activeSources.splice(idx, 1);
        }
      };
    } catch {
      // Chunk decode boundary handling
    }
  }

  public interrupt(): void {
    this.isInterrupted = true;
    this.stopActivePlayback();
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type: 'interrupt' }));
    }
    this.callbacks.onInterrupted();
  }

  public stopActivePlayback(): void {
    for (const source of this.activeSources) {
      try {
        source.stop();
        source.disconnect();
      } catch {
        // ignore already stopped sources
      }
    }
    this.activeSources = [];
    if (this.audioContext) {
      this.nextPlayTime = this.audioContext.currentTime;
    } else {
      this.nextPlayTime = 0;
    }
  }

  public stopSession(): void {
    this.isInterrupted = true;
    this.stopActivePlayback();

    if (this.processorNode) {
      this.processorNode.disconnect();
      this.processorNode = null;
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop());
      this.mediaStream = null;
    }

    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }

    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
      this.audioContext = null;
    }

    this.callbacks.onStateChange('idle');
  }
}
