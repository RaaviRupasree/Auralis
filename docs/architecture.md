# Auralis Architecture & System Design

## 1. Executive Overview

**Auralis** is a Real-Time Voice-to-Voice Emotion Engine tailored for crisis-negotiation training simulations. Unlike traditional conversational AI architectures that serially chain Speech-to-Text (STT), text Large Language Models (LLM), and Text-to-Speech (TTS) while stripping acoustic prosody, Auralis models **acoustic emotion directly from the raw audio waveform** concurrently with speech recognition.

The system features full-duplex conversational capabilities with dynamic barge-in interruption detection, sub-second latency targets, and emotion-adapted neural speech synthesis.

---

## 2. End-to-End Audio Pipeline

```
                     ┌───────────────────────────────┐
                     │ Trainee Microphone (Browser)  │
                     └───────────────┬───────────────┘
                                     │ 16kHz PCM Frames
                                     ▼
                     ┌───────────────────────────────┐
                     │ Web Audio API / WebSocket /   │
                     │ aiortc WebRTC Gateway         │
                     └───────────────┬───────────────┘
                                     │
                     ┌───────────────▼───────────────┐
                     │   Voice Activity Detection    │
                     │  (Silero / Energy & Ring Buf) │
                     └───────┬───────────────┬───────┘
            Speech Onset     │               │ End-of-Utterance (EOU)
                   (Barge-in)│               │
        ┌────────────────────▼─────┐  ┌──────▼─────────────────────┐
        │ Active Interruption Hub  │  │ Concurrency Dispatcher     │
        │ - Abort Active Synthesis │  │ - Faster-Whisper STT       │
        │ - Flush Audio Queues     │  │ - Acoustic SER Engine      │
        │ - Switch State to Listen │  └──────┬──────────────┬──────┘
        └──────────────────────────┘         │              │
                                  Transcript │              │ Emotion & Confidence
                                             ▼              ▼
                                  ┌────────────────────────────────┐
                                  │   Contextual LLM Engine        │
                                  │   (Crisis Negotiation Persona) │
                                  │   - Ollama (Llama 3.2 local)   │
                                  │   - OpenAI / Cloud compatible  │
                                  │   - Resilient heuristic rules  │
                                  └──────────────┬─────────────────┘
                                                 │ Response Text + Emotion
                                                 ▼
                                  ┌────────────────────────────────┐
                                  │ Emotion-Aware Neural TTS       │
                                  │ (Edge-TTS / Streaming Chunks)  │
                                  └──────────────┬─────────────────┘
                                                 │ Audio Bytes + Telemetry
                                                 ▼
                                  ┌────────────────────────────────┐
                                  │ Web Audio API Playback Queue   │
                                  │ & Live Waveform Visualizer     │
                                  └────────────────────────────────┘
```

---

## 3. Core Architectural Modules

### Module 1: Voice Activity Detection (VAD)
- **Role:** Segment continuous speech into coherent conversational utterances without clipping word onsets.
- **Implementation:** Pre-speech ring buffering (250ms), dual-frame onset confirmation (60ms), and configurable silence hang-time (350ms–1200ms, default 600ms).

### Module 2: Real-Time Speech Recognition (STT)
- **Engine:** Faster-Whisper (CTranslate2 inference engine).
- **Quantization:** `int8` CPU quantization with beam size 1 for sub-300ms transcription latency.
- **Sample Rate:** Standardized 16,000 Hz 1D float32 audio input.

### Module 3: Acoustic Speech Emotion Recognition (SER)
- **Engine:** Native acoustic prosody and spectral analyzer.
- **Extracted Acoustic Features:**
  - Fundamental frequency ($F_0$) autocorrelation, mean, and pitch jitter variance ($\sigma_{F_0}$).
  - RMS energy dynamics and rate of energy onset.
  - Zero Crossing Rate (ZCR).
  - Spectral Centroid (brightness) via Fast Fourier Transform (FFT).
- **Categories:** `calm`, `anxious`, `agitated`, `distressed`, `angry`, `neutral`.
- **Output:** Bounded confidence score (45%–92%) and execution telemetry.

### Module 4: Crisis Negotiation Conversational Engine
- **Persona:** Jordan, a barricaded subject in an intense crisis standoff scenario.
- **Emotion Coupling:**
  - If the trainee negotiator's acoustic emotion is `calm` or `neutral` with empathetic wording: Jordan's hostility decreases, expressing cautious de-escalation.
  - If the trainee sounds `agitated` or `angry`: Jordan's hostility escalates defensively.
  - If the trainee sounds `anxious` or `distressed`: Jordan questions their authority.
- **Provider Support:** Local Ollama (`llama3.2`), OpenAI API format, or built-in heuristic simulation rules.

### Module 5: Emotion-Aware Neural TTS & Streaming
- **Engine:** Microsoft Edge Neural TTS asynchronously streamed.
- **Voice Adaptation:** Dynamic pitch and rate inflection based on conversational tension (e.g., `-3%` rate for calm de-escalation, `+6%` rate with elevated pitch for agitated tension).
- **Audio Output:** Encoded 16-bit PCM and MP3 streaming chunks.

### Module 6: Full-Duplex Interruption & Barge-In
- **Interruption Flow:** If the trainee begins speaking while AI audio is playing or synthesizing:
  1. VAD immediately detects speech onset exceeding the energy threshold.
  2. Signal cancellation event dispatched to `AudioPipeline`.
  3. `asyncio.Task` cancelled; active `AudioBufferSourceNode` in browser calls `.stop()`.
  4. Interruption event recorded in SQLite database turn record (`was_interrupted = 1`).
  5. UI state smoothly transitions through `interrupted` back to `listening`.

---

## 4. Latency Telemetry Breakdown

All conversation turns are instrumented with high-resolution timestamps (`time.perf_counter()`):
- **$T_{STT}$:** Whisper transcription duration (typically 200–350ms on CPU).
- **$T_{SER}$:** Acoustic emotion classification duration (typically 5–25ms).
- **$T_{LLM}$:** Time-to-first-token (TTFT) and total generation time (typically 80–300ms).
- **$T_{TTS}$:** Time-to-first-audio chunk (TTFA) and total synthesis time (typically 300–600ms).
- **$T_{Total}$:** End-of-utterance (EOU) to first playable response audio.

---

## 5. Storage & Persistence Schema

Auralis uses SQLite (`auralis.db`) via `aiosqlite` for zero-latency metadata persistence.

- `sessions`: Stores `session_id`, `scenario`, `start_time`, `end_time`, `total_turns`, `status`, and `avg_latency_ms`.
- `conversation_turns`: Stores `turn_id`, `session_id`, `turn_index`, `user_transcript`, `detected_emotion`, `emotion_confidence`, `ai_response`, detailed latency timings, and `was_interrupted`.
- **Privacy Guarantee:** Raw microphone audio waveforms are processed transiently in RAM and never written to disk by default.
