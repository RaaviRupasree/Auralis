"""
========================================================================================
Auralis — Real-Time Voice-to-Voice Emotion Engine (Student Edition)
========================================================================================
A lightweight, beginner-friendly Generative AI application for a Crisis Negotiation
Training Simulator built with Streamlit, Faster-Whisper, Wav2Vec2 Emotion AI, Ollama,
and Text-to-Speech.

Workflow:
1. Microphone Audio Capture -> Browser audio recording via Streamlit
2. Speech-to-Text          -> Faster-Whisper (int8 quantized CPU)
3. Emotion Recognition     -> Pretrained Wav2Vec2 / Acoustic Prosody Model
4. Conversational AI       -> Local Ollama LLM (e.g., Llama 3.2 / Llama 3)
5. Text-to-Speech (TTS)    -> Neural Edge-TTS / Offline Windows pyttsx3
6. Audio Playback          -> Interactive Streamlit audio player with real metrics
========================================================================================
"""

import os
import sys
import time
import io
import tempfile
import asyncio
import numpy as np
import requests
import streamlit as st
import soundfile as sf
import av

# -----------------------------------------------------------------------------
# 1. Page Configuration & Theme
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Auralis — Voice-to-Voice Emotion Engine",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern, clean, student-friendly presentation
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .badge-calm { background-color: #DEF7EC; color: #03543F; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .badge-angry { background-color: #FDE8E8; color: #9B1C1C; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .badge-sad { background-color: #EDEBFE; color: #5521B5; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .badge-neutral { background-color: #E1EFFE; color: #1E429F; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .badge-happy { background-color: #FEF08A; color: #713F12; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Cached Model Loaders (Loaded once for speed)
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading Faster-Whisper speech model...")
def load_whisper():
    """Loads Faster-Whisper tiny.en model for fast CPU transcription."""
    from faster_whisper import WhisperModel
    # Using tiny.en with int8 quantization for ultra-fast, low-memory CPU execution
    return WhisperModel("tiny.en", device="cpu", compute_type="int8")

@st.cache_resource(show_spinner="Loading pretrained Wav2Vec2 Emotion model...")
def load_wav2vec2_emotion_pipeline():
    """Loads pretrained Wav2Vec2 speech emotion classification model."""
    try:
        from transformers import pipeline
        # Pretrained IEMOCAP speech emotion recognition model
        pipe = pipeline("audio-classification", model="superb/wav2vec2-base-superb-er")
        return pipe
    except Exception as e:
        return None

# -----------------------------------------------------------------------------
# 3. Audio Decoding & Preprocessing Utilities
# -----------------------------------------------------------------------------
def decode_audio_bytes(audio_bytes: bytes) -> tuple[str, np.ndarray]:
    """
    Decodes audio bytes from the browser (WAV, WebM, OGG) into:
    1. A temporary standard 16kHz mono 16-bit PCM WAV file.
    2. A float32 NumPy array normalized to [-1.0, 1.0].
    """
    container = av.open(io.BytesIO(audio_bytes))
    resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)
    frames = []
    for frame in container.decode(audio=0):
        for r_frame in resampler.resample(frame):
            frames.append(r_frame.to_ndarray())
    container.close()

    if not frames:
        raise ValueError("The recorded audio file is empty or has no audio frames.")

    audio_int16 = np.concatenate(frames, axis=1).squeeze()
    audio_float32 = audio_int16.astype(np.float32) / 32768.0

    # Write clean 16kHz mono WAV file for models
    temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_wav_path = temp_wav.name
    temp_wav.close()

    sf.write(temp_wav_path, audio_int16, 16000, subtype="PCM_16")
    return temp_wav_path, audio_float32

# -----------------------------------------------------------------------------
# 4. Speech-to-Text (Faster-Whisper)
# -----------------------------------------------------------------------------
def transcribe_speech(wav_path: str) -> tuple[str, str]:
    """Transcribes audio file to text using Faster-Whisper."""
    whisper_model = load_whisper()
    segments, info = whisper_model.transcribe(wav_path, beam_size=1)
    transcript = " ".join(s.text.strip() for s in segments).strip()
    return transcript, info.language

# -----------------------------------------------------------------------------
# 5. Speech Emotion Recognition (SER)
# -----------------------------------------------------------------------------
def predict_emotion_wav2vec2(wav_path: str) -> tuple[str, float, dict]:
    """Predicts emotion using the pretrained Wav2Vec2 model."""
    classifier = load_wav2vec2_emotion_pipeline()
    if classifier is None:
        return "neutral", 0.5, {"neutral": 0.5}

    results = classifier(wav_path)
    # Mapping IEMOCAP labels (neu, hap, ang, sad) to human-readable names
    label_map = {
        "neu": "Calm / Neutral",
        "hap": "Relieved / Positive",
        "ang": "Agitated / Angry",
        "sad": "Distressed / Sad"
    }

    scores = {}
    for item in results:
        mapped = label_map.get(item["label"], item["label"])
        scores[mapped] = float(item["score"])

    # Highest score
    top_label = label_map.get(results[0]["label"], results[0]["label"])
    top_score = float(results[0]["score"])
    return top_label, top_score, scores

def predict_emotion_acoustic(audio_np: np.ndarray, sr: int = 16000) -> tuple[str, float, dict]:
    """
    Lightweight acoustic prosodic emotion analyzer using pitch, energy, and spectral dynamics.
    Acts as a 100% offline, zero-dependency alternative.
    """
    if len(audio_np) == 0:
        return "Calm / Neutral", 0.5, {}

    rms = np.sqrt(np.mean(audio_np**2) + 1e-9)
    rms_db = 20 * np.log10(rms + 1e-9)

    # Autocorrelation pitch estimate
    corr = np.correlate(audio_np, audio_np, mode="full")
    corr = corr[len(corr)//2:]
    d = np.diff(corr)
    start = np.where(d > 0)[0]
    pitch = 140.0
    if len(start) > 0:
        peak = np.argmax(corr[start[0]:]) + start[0]
        if peak > 0:
            pitch = float(sr / peak)

    # Heuristic acoustic classification
    if rms_db > -18.0 and pitch > 210.0:
        label = "Agitated / Angry"
        conf = 0.85
    elif rms_db > -24.0 and pitch > 180.0:
        label = "Anxious / Tense"
        conf = 0.78
    elif rms_db < -36.0 or pitch < 110.0:
        label = "Distressed / Sad"
        conf = 0.75
    else:
        label = "Calm / Empathetic"
        conf = 0.82

    return label, conf, {"Energy (dB)": round(float(rms_db), 1), "Pitch (Hz)": round(pitch, 1)}

# -----------------------------------------------------------------------------
# 6. Ollama LLM Connection & Fallback
# -----------------------------------------------------------------------------
def check_ollama_status(host: str = "http://localhost:11434") -> tuple[bool, list[str]]:
    """Checks if Ollama server is running and lists available models."""
    try:
        res = requests.get(f"{host}/api/tags", timeout=2)
        if res.status_code == 200:
            models = [m["name"] for m in res.json().get("models", [])]
            return True, models
    except Exception:
        pass
    return False, []

def generate_ollama_response(transcript: str, emotion: str, model: str = "llama3.2", host: str = "http://localhost:11434") -> tuple[str, bool]:
    """Sends prompt with transcript and detected emotion to Ollama."""
    system_prompt = (
        "You are Jordan, an emotionally distressed individual barricaded inside a building in a crisis negotiation training simulator.\n"
        "A crisis negotiation trainee is speaking with you through a telephone.\n"
        f'The trainee spoke with a "{emotion}" vocal tone and said: "{transcript}"\n\n'
        "Guidelines:\n"
        "- Respond in 1 to 2 realistic spoken sentences as Jordan.\n"
        "- If the trainee sounds calm and empathetic, soften your tone slightly and show hesitant openness.\n"
        "- If the trainee sounds aggressive or dismissive, demand they back off and show rising panic.\n"
        "- Do not use stage directions or quotation marks. Speak directly to them."
    )

    try:
        res = requests.post(
            f"{host}/api/generate",
            json={
                "model": model,
                "prompt": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 60
                }
            },
            timeout=15
        )
        if res.status_code == 200:
            text = res.json().get("response", "").strip()
            return text, True
        return f"Ollama error: HTTP {res.status_code}", False
    except Exception as e:
        # Fallback simulation response if Ollama is not yet started by the student
        fallback = simulate_negotiation_response(transcript, emotion)
        return fallback, False

def simulate_negotiation_response(transcript: str, emotion: str) -> str:
    """Intelligent fallback for students testing before Ollama is installed."""
    emotion_lower = emotion.lower()
    if "angry" in emotion_lower or "agitated" in emotion_lower:
        return "Don't you raise your voice at me! You stay away from that door, or nobody is walking out of here!"
    elif "distressed" in emotion_lower or "sad" in emotion_lower:
        return "I... I just didn't want things to end up like this. I don't know who I can even trust anymore."
    elif "relieved" in emotion_lower or "positive" in emotion_lower:
        return "You sound serious about helping. If you can guarantee my sister is safe outside, maybe we can talk."
    else:
        return "I hear you, but you need to promise me you're not just stalling for time out there."

# -----------------------------------------------------------------------------
# 7. Text-to-Speech (TTS)
# -----------------------------------------------------------------------------
def synthesize_tts(text: str, engine_choice: str = "Edge-TTS (Neural)") -> str:
    """Converts text into audio file using chosen TTS engine."""
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3" if "Edge" in engine_choice else ".wav")
    out_path = temp_audio.name
    temp_audio.close()

    if "Edge" in engine_choice:
        try:
            import edge_tts
            async def _run():
                comm = edge_tts.Communicate(text, "en-US-GuyNeural")
                await comm.save(out_path)
            asyncio.run(_run())
            return out_path
        except Exception:
            # Fall back to pyttsx3 if network request fails
            pass

    # Offline Windows pyttsx3 fallback
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", 160)
    engine.save_to_file(text, out_path)
    engine.runAndWait()
    return out_path

# -----------------------------------------------------------------------------
# 8. User Interface Layout
# -----------------------------------------------------------------------------
st.markdown('<div class="main-header">🎙️ Auralis — Real-Time Voice-to-Voice Emotion Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Crisis Negotiation Training Simulator • Student Edition (Faster-Whisper + Wav2Vec2 + Ollama + TTS)</div>', unsafe_allow_html=True)

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ System Status & Settings")

    # Check Ollama Server
    ollama_online, detected_models = check_ollama_status()
    if ollama_online:
        st.success("🟢 Ollama Connected (Localhost:11434)")
        if detected_models:
            selected_model = st.selectbox("Select Ollama Model", detected_models, index=0)
        else:
            selected_model = st.text_input("Model Name", value="llama3.2")
            st.caption("No models detected. Pull one with: `ollama run llama3.2`")
    else:
        st.warning("🟠 Ollama Offline (Using Smart Fallback)")
        selected_model = st.text_input("Target Model", value="llama3.2")

    st.divider()

    # Emotion Model Selection
    emotion_engine = st.radio(
        "Emotion Recognition Model",
        ["Pretrained Wav2Vec2 (superb/wav2vec2-base-superb-er)", "Acoustic Prosody (Offline Pitch & Energy)"],
        index=0
    )

    # TTS Engine Selection
    tts_engine = st.radio(
        "Text-to-Speech Engine",
        ["Edge-TTS (Neural High-Fidelity)", "pyttsx3 (Offline Windows Native)"],
        index=0
    )

    st.divider()

    # Expandable Help Guide for Students
    with st.expander("📖 How to Setup Ollama"):
        st.markdown("""
        **1. Download Ollama:**
        Go to [ollama.com](https://ollama.com) and install it on Windows.
        
        **2. Pull a local model:**
        Open PowerShell and run:
        ```bash
        ollama run llama3.2
        ```
        *(Or run `ollama run mistral` or `ollama run phi3`)*
        
        **3. Click Rerun:**
        Ollama will show as 🟢 **Connected** automatically!
        """)

# --- Main Workspace ---
col_record, col_info = st.columns([1.1, 0.9])

with col_record:
    st.subheader("1. Speak into Microphone")
    st.write("Click the microphone icon below, speak your negotiation statement, and click stop when finished.")

    # Native Streamlit audio recorder (1.55+ built-in)
    audio_data = st.audio_input("Record your voice")

with col_info:
    st.subheader("💡 Crisis Scenario Context")
    st.info(
        "**Role:** You are the Lead Crisis Negotiator.\n\n"
        "**Subject:** Jordan, an individual in high emotional distress.\n\n"
        "**Objective:** Speak with steady empathy to de-escalate tension, or observe how Jordan reacts if you speak aggressively."
    )

# Sample audio alternative if mic is unavailable
st.write("")
use_sample = st.checkbox("Or test with a pre-recorded negotiation sample (if microphone is blocked)", value=False)
sample_choice = None
if use_sample:
    sample_choice = st.selectbox(
        "Select sample phrase:",
        [
            "Calm: Jordan, I am listening. Take your time, nobody is going to hurt you.",
            "Firm: Put the weapon down right now Jordan, this ends today!",
            "Empathetic: I know you are terrified right now Jordan, let's find a way through this together."
        ]
    )

# -----------------------------------------------------------------------------
# 9. Pipeline Execution
# -----------------------------------------------------------------------------
has_input = (audio_data is not None) or (use_sample and st.button("▶️ Process Selected Sample"))

if has_input:
    st.divider()
    st.subheader("2. Pipeline Processing & Results")

    with st.spinner("Processing speech, emotion, and AI response..."):
        t_start = time.time()
        temp_input_wav = None

        try:
            # --- Audio Ingestion ---
            if audio_data is not None:
                audio_bytes = audio_data.read()
                temp_input_wav, audio_np = decode_audio_bytes(audio_bytes)
            else:
                # Generate sample audio dynamically for testing
                import pyttsx3
                temp_f = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                temp_input_wav = temp_f.name
                temp_f.close()
                sample_text = sample_choice.split(": ", 1)[1]
                eng = pyttsx3.init()
                eng.save_to_file(sample_text, temp_input_wav)
                eng.runAndWait()
                data_pcm, _ = sf.read(temp_input_wav)
                audio_np = data_pcm.astype(np.float32)

            # --- Step A: Speech-to-Text ---
            t_stt_start = time.time()
            transcript, lang = transcribe_speech(temp_input_wav)
            t_stt = time.time() - t_stt_start

            if not transcript.strip():
                st.error("⚠️ No clear speech was detected in your recording. Please try speaking a bit louder or closer to the mic.")
                st.stop()

            # --- Step B: Speech Emotion Recognition ---
            t_emo_start = time.time()
            if "Wav2Vec2" in emotion_engine:
                top_emotion, conf, all_scores = predict_emotion_wav2vec2(temp_input_wav)
            else:
                top_emotion, conf, all_scores = predict_emotion_acoustic(audio_np)
            t_emo = time.time() - t_emo_start

            # --- Step C: LLM Response (Ollama) ---
            t_llm_start = time.time()
            ai_reply, was_real_ollama = generate_ollama_response(
                transcript, top_emotion, model=selected_model
            )
            t_llm = time.time() - t_llm_start

            # --- Step D: Text-to-Speech ---
            t_tts_start = time.time()
            tts_file_path = synthesize_tts(ai_reply, engine_choice=tts_engine)
            t_tts = time.time() - t_tts_start

            t_total = time.time() - t_start

            # --- Results Display ---
            res_col1, res_col2 = st.columns([1, 1])

            with res_col1:
                # 1. Recognized Speech
                st.markdown("#### 📝 1. Recognized Speech (Faster-Whisper)")
                st.success(f'"{transcript}"')
                st.caption(f"Detected Language: {lang.upper()} • Whisper Latency: {t_stt:.2f}s")

                # 2. Detected Vocal Emotion
                st.markdown("#### 🎭 2. Vocal Emotion Recognition")
                badge_class = "badge-neutral"
                if "Angry" in top_emotion or "Agitated" in top_emotion:
                    badge_class = "badge-angry"
                elif "Sad" in top_emotion or "Distressed" in top_emotion:
                    badge_class = "badge-sad"
                elif "Relieved" in top_emotion:
                    badge_class = "badge-happy"
                elif "Calm" in top_emotion:
                    badge_class = "badge-calm"

                st.markdown(
                    f'Detected Emotion: <span class="{badge_class}">{top_emotion} ({conf*100:.1f}%)</span>',
                    unsafe_allow_html=True
                )
                st.progress(float(conf))
                st.caption(f"Model: {emotion_engine} • Emotion Latency: {t_emo:.2f}s")

            with res_col2:
                # 3. AI Response
                st.markdown("#### 🤖 3. Jordan's AI Response (Ollama)")
                st.info(f'"{ai_reply}"')
                if was_real_ollama:
                    st.caption(f"Generated via Ollama model `{selected_model}` • LLM Latency: {t_llm:.2f}s")
                else:
                    st.caption(f"Generated via Smart Crisis Simulator (Ollama offline) • Latency: {t_llm:.2f}s")

                # 4. Spoken Audio Playback
                st.markdown("#### 🔊 4. Generated Voice Playback")
                with open(tts_file_path, "rb") as f:
                    audio_output_bytes = f.read()
                st.audio(audio_output_bytes, format="audio/mp3" if tts_file_path.endswith(".mp3") else "audio/wav")
                st.caption(f"Synthesized using {tts_engine} • TTS Latency: {t_tts:.2f}s")

            st.divider()

            # --- Processing Time & Metrics ---
            st.markdown("#### ⏱️ Actual Measured Processing Latencies")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total Latency", f"{t_total:.2f} s")
            m2.metric("Speech-to-Text", f"{t_stt:.2f} s")
            m3.metric("Emotion Recognition", f"{t_emo:.2f} s")
            m4.metric("LLM Response", f"{t_llm:.2f} s")
            m5.metric("Text-to-Speech", f"{t_tts:.2f} s")

        except Exception as e:
            st.error(f"❌ An error occurred during processing: {str(e)}")
        finally:
            # Clean up temporary WAV file
            if temp_input_wav and os.path.exists(temp_input_wav):
                try:
                    os.remove(temp_input_wav)
                except Exception:
                    pass

# -----------------------------------------------------------------------------
# 10. Footer
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<center><small>Auralis: Real-Time Voice-to-Voice Emotion Engine • Built for Crisis Negotiation AI Training • Powered by Streamlit & Faster-Whisper</small></center>",
    unsafe_allow_html=True
)
