# Auralis: Real-Time Voice-to-Voice Emotion Engine (Student Edition)

> **A beginner-friendly Generative AI project for a Crisis Negotiation Training Simulator.**  
> Built with **Streamlit**, **Faster-Whisper**, **Pretrained Speech Emotion AI (Wav2Vec2)**, **Ollama (Llama 3.2)**, and **Text-to-Speech**.

---

## 1. Project Overview & Workflow

Auralis is an emotion-aware conversational AI designed for crisis negotiation training. A student trainee speaks into the microphone. The application captures the speech, transcribes the words, detects the vocal emotion in the speaker's tone of voice, generates a context-aware response roleplaying Jordan (the barricaded subject), and speaks the response back to the trainee.

### The Complete End-to-End Workflow:
```
🎙️ Microphone Audio
         ↓
📝 Speech-to-Text (Faster-Whisper int8 on CPU)
         ↓
🎭 Vocal Emotion Recognition (Wav2Vec2 / Acoustic Prosody)
         ↓
🤖 Local LLM Reasoning (Ollama: Llama 3.2 / Llama 3)
         ↓
🔊 Text-to-Speech (Neural Edge-TTS / Offline Windows pyttsx3)
         ↓
🎧 Audio Playback & Real Telemetry Display
```

---

## 2. Technologies Used

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend UI** | Streamlit (Python) | Simple web dashboard with built-in microphone recording |
| **Speech-to-Text** | Faster-Whisper (`tiny.en`) | Ultra-fast sub-second speech transcription on CPU |
| **Emotion Recognition** | Hugging Face Wav2Vec2 (`superb/wav2vec2-base-superb-er`) + Acoustic Prosody | Identifies vocal emotion (Calm, Agitated/Angry, Distressed/Sad, Relieved) |
| **Language Model** | Ollama (`llama3.2`) | Generates roleplay negotiation dialogue based on tone & words |
| **Speech Synthesis** | Edge-TTS / pyttsx3 | Speaks response with neural or offline Windows SAPI5 voice |

---

## 3. Quick Start (Windows Setup)

### Step 1: Open PowerShell or Command Prompt
Navigate to your project folder:
```powershell
cd c:\auralis
```

### Step 2: Install Python Dependencies
```powershell
python -m pip install -r requirements_student.txt
```

### Step 3: Launch the Application
You can run:
```powershell
python -m streamlit run app.py
```
*(Or simply double-click **`run_app.bat`**)*

Open **`http://localhost:8501`** in your browser.

---

## 4. How to Setup & Run Ollama (Local LLM)

Auralis connects directly to **Ollama** running locally on your computer.

### 1. Download Ollama
Download and install Ollama for Windows from [https://ollama.com](https://ollama.com).

### 2. Download the Model
Open a new PowerShell terminal and run:
```powershell
ollama run llama3.2
```
*Note: If you have less than 8GB of RAM, you can also use `ollama run phi3` or `ollama run mistral`.*

### 3. Check Connection in Auralis
When Ollama is running in the background, Auralis will automatically detect it and display:
`🟢 Ollama Connected (Localhost:11434)`.

> **💡 Smart Fallback for Testing:**  
> If Ollama is not installed or offline, Auralis automatically engages an **integrated Crisis Negotiation Simulator** so you can test the full audio recording, transcription, emotion recognition, and TTS playback without errors!

---

## 5. Using the Application

1. **Record:** Click the microphone button in the **"Record your voice"** widget.
2. **Speak:** Say a negotiation phrase, for example:
   - *Empathetic:* "Jordan, we're listening to you. Nobody wants anyone to get hurt."
   - *Firm:* "You need to put down the weapon right now, Jordan!"
3. **Stop:** Click the stop button on the recorder.
4. **Inspect Results:**
   - **Recognized Speech:** View your transcribed words.
   - **Vocal Emotion:** View whether your tone sounded calm, angry, sad, or relieved.
   - **Jordan's AI Response:** Read Jordan's psychological reaction.
   - **Audio Playback:** Click play on the generated voice to hear Jordan speak.
   - **Measured Latency:** View real processing time metrics (no fake values).

---

## 6. Project Structure

```
c:\auralis/
├── app.py                     # Single self-contained Streamlit application
├── requirements_student.txt   # Clean Python dependencies list
├── run_app.bat                # 1-click Windows startup batch script
└── README_STUDENT.md          # Complete project instructions & guide
```

---

## 7. Troubleshooting

- **Microphone permission blocked:** Click the lock icon next to the URL in your browser address bar and enable "Microphone". You can also test with the built-in negotiation audio samples.
- **Audio synthesis:** If internet is disconnected, Auralis automatically switches from Edge-TTS to `pyttsx3` (Windows built-in speech).
- **Ollama connection refused:** Ensure Ollama is running in your taskbar or terminal (`ollama serve`).
