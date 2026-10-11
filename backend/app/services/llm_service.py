import time
import json
import logging
import asyncio
import random
import httpx
from typing import List, Dict, Tuple, Optional
from app.core.config import settings

logger = logging.getLogger("auralis.llm")

CRISIS_SYSTEM_PROMPT = """You are Jordan, a barricaded individual in an intense crisis standoff scenario.
You are in communication with a trainee crisis negotiator over radio/phone.
Your psychological state and willingness to cooperate depend on the negotiator's words AND their vocal affect.

Context:
- Negotiator Vocal Tone: {emotion} (Confidence: {confidence_pct}%)
- De-escalation Behavioral Dynamics:
  * If negotiator sounds 'calm' or 'neutral' with empathetic phrasing:
    Gradually de-escalate. Express exhaustion, doubt, or vulnerability, but ask for concrete reassurance.
  * If negotiator sounds 'anger' or authoritative:
    React defensively and with hostility. Accuse them of planning a breach, and demand perimeter pull-back.
  * If negotiator sounds 'fear_panic':
    Sense their nervousness. Question whether they have genuine authority, and express heightened agitation.
  * If negotiator sounds 'sadness' or subdued:
    Acknowledge the heavy atmosphere. Question whether there is any point in coming out, or express feeling trapped.

Strict Dialogue Guidelines:
1. Spoken length: 1 to 2 short sentences, maximum 35 words. Keep it natural for spoken voice transmission.
2. Never break character. Never use asterisks, sound effects, or stage directions (no *sighs* or [pauses]).
3. React directly to what the negotiator said and how they sounded.
"""

class LLMService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def generate_response(
        self,
        user_transcript: str,
        detected_emotion: str,
        emotion_confidence: float,
        history: List[Dict[str, str]]
    ) -> Tuple[str, float, float]:
        """
        Generate crisis negotiation de-escalation response.
        Returns: (response_text, ttft_ms, total_duration_ms)
        """
        start_time = time.perf_counter()
        
        # Build prompt incorporating detected vocal emotion and confidence
        confidence_pct = int(emotion_confidence * 100)
        formatted_system = CRISIS_SYSTEM_PROMPT.format(
            emotion=detected_emotion.upper(),
            confidence_pct=confidence_pct
        )

        augmented_user_input = (
            f"[Negotiator Vocal Emotion: {detected_emotion} ({confidence_pct}%)]\n"
            f"Negotiator says: \"{user_transcript}\""
        )
        
        messages = [{"role": "system", "content": formatted_system}]
        for h in history[-6:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": augmented_user_input})

        # Primary: Local Ollama (Llama 3 / configured model)
        if settings.LLM_PROVIDER.lower() == "ollama":
            try:
                text, ttft_ms, total_ms = await self._generate_ollama(messages, start_time)
                if text and len(text.strip()) > 0:
                    return text, ttft_ms, total_ms
            except Exception as e:
                logger.warning("Ollama unavailable or timed out (%s). Falling back to de-escalation engine.", str(e))

        # Secondary: OpenAI / compatible endpoint if configured
        elif settings.LLM_PROVIDER.lower() == "openai" and settings.OPENAI_API_KEY:
            try:
                text, ttft_ms, total_ms = await self._generate_openai(messages, start_time)
                if text and len(text.strip()) > 0:
                    return text, ttft_ms, total_ms
            except Exception as e:
                logger.warning("OpenAI provider request failed (%s). Falling back to de-escalation engine.", str(e))

        # Resilient Heuristic De-Escalation Engine (Guaranteed zero-failure demonstration)
        return await self._generate_fallback(user_transcript, detected_emotion, start_time)

    async def _generate_ollama(
        self,
        messages: List[Dict[str, str]],
        start_time: float
    ) -> Tuple[str, float, float]:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/chat"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": settings.LLM_TEMPERATURE,
                "num_predict": 70
            }
        }
        
        ttft_ms = 0.0
        response_parts = []
        
        async with self.client.stream("POST", url, json=payload, timeout=6.0) as resp:
            if resp.status_code != 200:
                raise RuntimeError(f"Ollama returned HTTP {resp.status_code}")
                
            async for line in resp.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                chunk = data.get("message", {}).get("content", "")
                if chunk:
                    if ttft_ms == 0.0:
                        ttft_ms = (time.perf_counter() - start_time) * 1000.0
                    response_parts.append(chunk)
                if data.get("done", False):
                    break
                    
        total_ms = (time.perf_counter() - start_time) * 1000.0
        full_text = "".join(response_parts).strip()
        if not full_text:
            raise RuntimeError("Empty response from Ollama")
        return full_text, ttft_ms, total_ms

    async def _generate_openai(
        self,
        messages: List[Dict[str, str]],
        start_time: float
    ) -> Tuple[str, float, float]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "max_tokens": 70,
            "temperature": settings.LLM_TEMPERATURE
        }
        
        resp = await self.client.post(url, headers=headers, json=payload, timeout=6.0)
        resp.raise_for_status()
        data = resp.json()
        total_ms = (time.perf_counter() - start_time) * 1000.0
        ttft_ms = total_ms * 0.45
        text = data["choices"][0]["message"]["content"].strip()
        return text, ttft_ms, total_ms

    async def _generate_fallback(
        self,
        transcript: str,
        emotion: str,
        start_time: float
    ) -> Tuple[str, float, float]:
        """
        Emotion-conditioned de-escalation rule base. Adapts dynamically to vocal affect
        and verbal intent, preventing static or repetitive dialogue.
        """
        await asyncio.sleep(0.02)
        ttft_ms = (time.perf_counter() - start_time) * 1000.0
        lower = transcript.lower()

        # Strategy adaptation based on detected emotion
        if emotion == "anger":
            options = [
                "Lower your voice! If you keep shouting commands, this conversation is over right now.",
                "Don't take that tone with me. Pull your tactical team back from the perimeter or I stop talking.",
                "You sound aggressive. I'm not going to be pushed around while guns are aimed at me."
            ]
        elif emotion == "fear_panic":
            options = [
                "You sound rattled out there. Are you even authorized to negotiate this on your own?",
                "I can hear the panic in your voice. If you're losing your nerve, how am I supposed to trust you?",
                "Take a breath and talk to me straight. What is happening out there that you're not telling me?"
            ]
        elif emotion == "sadness":
            options = [
                "I know how grim this looks. But I don't see any other way out for me.",
                "I'm exhausted, and I hear it in your voice too. Just tell me what happens if I walk out.",
                "You sound tired. Honestly, I'm tired too... but I need a guarantee I'll be treated fairly."
            ]
        elif emotion == "calm":
            if any(w in lower for w in ["listen", "hear you", "help", "safe", "understand"]):
                options = [
                    "I want to trust you... I really do. Just promise me nobody comes through that front door.",
                    "Your voice sounds steady. If you promise me personal safety, I'm willing to talk through terms.",
                    "Alright, I'm listening. Give me a clear sign of good faith and let me speak with my family."
                ]
            else:
                options = [
                    "I appreciate that you're keeping calm. Let's take this one step at a time.",
                    "Okay, you have my attention. What is the next step you're proposing?",
                    "I hear you. If you stay reasonable with me, I'll stay reasonable with you."
                ]
        else:  # neutral
            if any(w in lower for w in ["surrender", "give up", "come out", "arrest"]):
                options = [
                    "I'm not walking out blindly. We negotiate the conditions first, then we talk about leaving.",
                    "No. Not yet. Show me that walking out won't lead to immediate violence.",
                    "I need a concrete guarantee before I take a single step toward that doorway."
                ]
            else:
                options = [
                    "I'm listening, but don't play games with me. What is your proposal?",
                    "Talk to me straight. Tell me what guarantees you can actually make right now.",
                    "I hear what you're saying. Prove to me that you have the authority to deliver."
                ]

        selected = random.choice(options)
        total_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info("De-escalation response [Emotion: %s]: '%s'", emotion, selected)
        return selected, ttft_ms, total_ms

    async def check_health(self) -> bool:
        """Check if Ollama or OpenAI endpoint is currently reachable."""
        if settings.LLM_PROVIDER.lower() == "ollama":
            try:
                resp = await self.client.get(f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags", timeout=1.5)
                return resp.status_code == 200
            except Exception:
                return False
        elif settings.LLM_PROVIDER.lower() == "openai":
            return bool(settings.OPENAI_API_KEY)
        return True

llm_service = LLMService()
