"""
========================================================================================
Auralis — Real-Time Voice-to-Voice Emotion Engine (Student Edition)
========================================================================================
A lightweight Generative AI application for a Crisis Negotiation Training Simulator.
Built with Streamlit, Faster-Whisper, Wav2Vec2 Emotion AI, Ollama (Llama 3.2), and TTS.

Pipeline:
1. Microphone Audio Capture -> Browser audio recording via Streamlit st.audio_input
2. Speech-to-Text          -> Faster-Whisper (tiny.en int8 quantized on CPU)
3. Emotion Recognition     -> Pretrained Wav2Vec2 (superb/wav2vec2-base-superb-er)
4. Conversational AI       -> Local Ollama LLM (Llama 3.2 real generation)
5. Text-to-Speech (TTS)    -> Neural Edge-TTS / Windows Native pyttsx3 (ONLY on success)
6. Audio Playback          -> Interactive audio player + real latency metrics
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
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #4B5563;
        margin-bottom: 1.4rem;
    }
    .badge-calm { background-color: #DEF7EC; color: #03543F; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .badge-angry { background-color: #FDE8E8; color: #9B1C1C; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .badge-sad { background-color: #EDEBFE; color: #5521B5; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .badge-neutral { background-color: #E1EFFE; color: #1E429F; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
    .badge-happy { background-color: #FEF08A; color: #713F12; padding: 4px 10px; border-radius: 6px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "last_processed" not in st.session_state:
    st.session_state.last_processed = None

# -----------------------------------------------------------------------------
# 2. Cached Model Loaders
# -----------------------------------------------------------------------------
@st.cache_resource(show_spinner="Loading Faster-Whisper speech model...")
def load_whisper():
    """Loads Faster-Whisper tiny.en model for fast CPU transcription."""
    from faster_whisper import WhisperModel
    return WhisperModel("tiny.en", device="cpu", compute_type="int8")

@st.cache_resource(show_spinner="Loading pretrained Wav2Vec2 Emotion model...")
def load_wav2vec2_emotion_pipeline():
    """Loads pretrained Wav2Vec2 speech emotion classification model."""
    try:
        from transformers import pipeline
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
        return "Calm / Neutral", 0.5, {"Calm / Neutral": 0.5}

    results = classifier(wav_path)
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

    top_label = label_map.get(results[0]["label"], results[0]["label"])
    top_score = float(results[0]["score"])
    return top_label, top_score, scores

def predict_emotion_acoustic(audio_np: np.ndarray, sr: int = 16000) -> tuple[str, float, dict]:
    """Lightweight acoustic prosodic emotion analyzer using pitch & energy."""
    if len(audio_np) == 0:
        return "Calm / Neutral", 0.5, {}

    rms = np.sqrt(np.mean(audio_np**2) + 1e-9)
    rms_db = 20 * np.log10(rms + 1e-9)

    corr = np.correlate(audio_np, audio_np, mode="full")
    corr = corr[len(corr)//2:]
    d = np.diff(corr)
    start = np.where(d > 0)[0]
    pitch = 140.0
    if len(start) > 0:
        peak = np.argmax(corr[start[0]:]) + start[0]
        if peak > 0:
            pitch = float(sr / peak)

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
# 6. Ollama LLM Connection & Real Generation
# -----------------------------------------------------------------------------
def check_ollama_status(host: str = "http://localhost:11434") -> tuple[bool, list[str]]:
    """Checks if Ollama server is running and lists installed models."""
    try:
        res = requests.get(f"{host}/api/tags", timeout=3)
        if res.status_code == 200:
            models = [m.get("name", "") for m in res.json().get("models", [])]
            return True, [m for m in models if m]
    except Exception:
        pass
    return False, []

def generate_ollama_response(
    transcript: str,
    emotion: str,
    model: str,
    host: str = "http://localhost:11434"
) -> tuple[str, bool, str]:
    """
    Sends actual recognized transcript and predicted vocal emotion to Ollama.
    Returns: (response_text, is_success, error_message)
    """
    system_prompt = (
        "You are Jordan, an emotionally distressed individual barricaded inside a building in a crisis negotiation training simulator.\n"
        "A crisis negotiation trainee is speaking with you over a telephone line.\n"
        f"Trainee's Spoken Words: \"{transcript}\"\n"
        f"Trainee's Vocal Emotion Detected: \"{emotion}\"\n\n"
        "Instructions for your response:\n"
        "- Respond in 1 to 2 realistic spoken sentences as Jordan.\n"
        "- If the trainee sounds calm and empathetic, soften your tone slightly and show hesitant openness.\n"
        "- If the trainee sounds aggressive, impatient, or angry, respond defensively and demand they back off.\n"
        "- Stay strictly in character. Do not include stage directions, parentheses, quotation marks, or conversational prefixes like 'Jordan:'. Speak directly."
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
                    "num_predict": 75
                }
            },
            timeout=25
        )

        if res.status_code == 200:
            data = res.json()
            text = data.get("response", "").strip()
            # Clean any accidental outer quotes
            if text.startswith('"') and text.endswith('"'):
                text = text[1:-1].strip()
            if text:
                return text, True, ""
            return "", False, "Ollama returned an empty response string."

        elif res.status_code == 404:
            err_msg = ""
            try:
                err_msg = res.json().get("error", "")
            except Exception:
                pass
            return "", False, f"Model '{model}' not found in Ollama (HTTP 404). {err_msg}"

        else:
            return "", False, f"Ollama HTTP {res.status_code}: {res.text}"

    except requests.exceptions.ConnectionError:
        return "", False, f"Cannot connect to Ollama at {host}. Verify that Ollama service is running."
    except requests.exceptions.Timeout:
        return "", False, "Ollama request timed out after 25 seconds."
    except Exception as e:
        return "", False, f"Ollama error: {str(e)}"

# -----------------------------------------------------------------------------
# 7. Text-to-Speech (TTS) — Executed ONLY on successful LLM response
# -----------------------------------------------------------------------------
def synthesize_tts(text: str, engine_choice: str = "Edge-TTS (Neural High-Fidelity)") -> str:
    """Converts LLM response text into audio file using chosen TTS engine."""
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

    # Windows native pyttsx3 fallback
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
    ollama_online, installed_models = check_ollama_status()
    if ollama_online:
        st.success("🟢 Ollama Connected (Localhost:11434)")
        if installed_models:
            # Match installed models cleanly
            default_idx = 0
            for idx, m in enumerate(installed_models):
                if "llama3.2" in m:
                    default_idx = idx
                    break
            selected_model = st.selectbox("Select Ollama Model", installed_models, index=default_idx)
            st.caption(f"Ready: `{selected_model}`")
        else:
            st.warning("⚠️ Ollama is running, but no models are installed yet.")
            selected_model = st.text_input("Target Model", value="llama3.2")
            st.code(f"ollama pull {selected_model}", language="powershell")
    else:
        st.error("🔴 Ollama Offline (localhost:11434)")
        st.caption("Start Ollama or run `ollama serve` in PowerShell.")
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
# 9. Pipeline Execution & State Processing
# -----------------------------------------------------------------------------
has_input = (audio_data is not None) or (use_sample and st.button("▶️ Process Selected Sample"))

if has_input:
    with st.spinner("Processing speech, emotion, and AI response..."):
        t_start = time.time()
        temp_input_wav = None

        try:
            # --- Audio Ingestion ---
            if audio_data is not None:
                audio_bytes = audio_data.read()
                temp_input_wav, audio_np = decode_audio_bytes(audio_bytes)
            else:
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
            ai_reply, is_llm_success, llm_error = generate_ollama_response(
                transcript=transcript,
                emotion=top_emotion,
                model=selected_model
            )
            t_llm = time.time() - t_llm_start

            # --- Step D: Text-to-Speech (ONLY on successful LLM response) ---
            tts_file_path = None
            t_tts = 0.0
            audio_output_bytes = None

            if is_llm_success and ai_reply:
                t_tts_start = time.time()
                tts_file_path = synthesize_tts(ai_reply, engine_choice=tts_engine)
                t_tts = time.time() - t_tts_start

                with open(tts_file_path, "rb") as f:
                    audio_output_bytes = f.read()

                # Clean up temporary TTS file
                try:
                    os.remove(tts_file_path)
                except Exception:
                    pass

            t_total = time.time() - t_start

            # Store in session state for rendering & retry
            st.session_state.last_processed = {
                "transcript": transcript,
                "lang": lang,
                "t_stt": t_stt,
                "top_emotion": top_emotion,
                "conf": conf,
                "t_emo": t_emo,
                "emotion_engine": emotion_engine,
                "ai_reply": ai_reply,
                "is_llm_success": is_llm_success,
                "llm_error": llm_error,
                "selected_model": selected_model,
                "t_llm": t_llm,
                "audio_output_bytes": audio_output_bytes,
                "t_tts": t_tts,
                "tts_engine": tts_engine,
                "t_total": t_total
            }

        except Exception as e:
            st.error(f"❌ An error occurred during audio processing: {str(e)}")
        finally:
            if temp_input_wav and os.path.exists(temp_input_wav):
                try:
                    os.remove(temp_input_wav)
                except Exception:
                    pass

# -----------------------------------------------------------------------------
# 10. Display Results & Retry Section
# -----------------------------------------------------------------------------
if st.session_state.last_processed is not None:
    res = st.session_state.last_processed

    st.divider()
    st.subheader("2. Pipeline Processing & Results")

    res_col1, res_col2 = st.columns([1, 1])

    with res_col1:
        # 1. Recognized Speech
        st.markdown("#### 📝 1. Recognized Speech (Faster-Whisper)")
        st.success(f'"{res["transcript"]}"')
        st.caption(f"Detected Language: {res['lang'].upper()} • Whisper Latency: {res['t_stt']:.2f}s")

        # 2. Detected Vocal Emotion
        st.markdown("#### 🎭 2. Vocal Emotion Recognition")
        top_emo = res["top_emotion"]
        badge_class = "badge-neutral"
        if "Angry" in top_emo or "Agitated" in top_emo:
            badge_class = "badge-angry"
        elif "Sad" in top_emo or "Distressed" in top_emo:
            badge_class = "badge-sad"
        elif "Relieved" in top_emo:
            badge_class = "badge-happy"
        elif "Calm" in top_emo:
            badge_class = "badge-calm"

        st.markdown(
            f'Detected Emotion: <span class="{badge_class}">{top_emo} ({res["conf"]*100:.1f}%)</span>',
            unsafe_allow_html=True
        )
        st.progress(float(res["conf"]))
        st.caption(f"Model: {res['emotion_engine']} • Emotion Latency: {res['t_emo']:.2f}s")

    with res_col2:
        # 3. AI Response
        st.markdown("#### 🤖 3. Jordan's AI Response (Ollama)")
        if res["is_llm_success"]:
            st.info(f'"{res["ai_reply"]}"')
            st.caption(f"Generated via Ollama model `{res['selected_model']}` • LLM Latency: {res['t_llm']:.2f}s")
        else:
            st.error(f"❌ {res['llm_error']}")
            st.caption(f"LLM Generation Attempt: {res['t_llm']:.2f}s")

            # Retry Button
            if st.button("🔄 Retry Ollama LLM Generation"):
                with st.spinner(f"Retrying generation with model '{selected_model}'..."):
                    t_retry_start = time.time()
                    retry_reply, retry_success, retry_err = generate_ollama_response(
                        transcript=res["transcript"],
                        emotion=res["top_emotion"],
                        model=selected_model
                    )
                    t_retry_llm = time.time() - t_retry_start

                    retry_audio_bytes = None
                    t_retry_tts = 0.0
                    if retry_success and retry_reply:
                        t_tts_s = time.time()
                        tts_p = synthesize_tts(retry_reply, engine_choice=tts_engine)
                        t_retry_tts = time.time() - t_tts_s
                        with open(tts_p, "rb") as f:
                            retry_audio_bytes = f.read()
                        try:
                            os.remove(tts_p)
                        except Exception:
                            pass

                    # Update session state
                    res["ai_reply"] = retry_reply
                    res["is_llm_success"] = retry_success
                    res["llm_error"] = retry_err
                    res["selected_model"] = selected_model
                    res["t_llm"] = t_retry_llm
                    res["audio_output_bytes"] = retry_audio_bytes
                    res["t_tts"] = t_retry_tts
                    res["t_total"] = res["t_stt"] + res["t_emo"] + t_retry_llm + t_retry_tts
                    st.rerun()

        # 4. Spoken Audio Playback (ONLY shown if valid audio exists)
        st.markdown("#### 🔊 4. Generated Voice Playback")
        if res["is_llm_success"] and res["audio_output_bytes"] is not None:
            st.audio(res["audio_output_bytes"], format="audio/mp3" if "Edge" in res["tts_engine"] else "audio/wav")
            st.caption(f"Synthesized using {res['tts_engine']} • TTS Latency: {res['t_tts']:.2f}s")
        else:
            st.warning("⚠️ Audio playback is unavailable because valid LLM response text was not generated.")

    st.divider()

    # --- Processing Time & Metrics ---
    st.markdown("#### ⏱️ Actual Measured Processing Latencies")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Latency", f"{res['t_total']:.2f} s")
    m2.metric("Speech-to-Text", f"{res['t_stt']:.2f} s")
    m3.metric("Emotion Recognition", f"{res['t_emo']:.2f} s")
    m4.metric("LLM Response", f"{res['t_llm']:.2f} s")
    m5.metric("Text-to-Speech", f"{res['t_tts']:.2f} s" if res["is_llm_success"] else "N/A")

# -----------------------------------------------------------------------------
# 11. Footer
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<center><small>Auralis: Real-Time Voice-to-Voice Emotion Engine • Built for Crisis Negotiation AI Training • Powered by Streamlit & Faster-Whisper</small></center>",
    unsafe_allow_html=True
)
