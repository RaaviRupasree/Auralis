import time
import json
import logging
import httpx
from typing import List, Dict, Tuple, Optional, AsyncGenerator
from app.core.config import settings

logger = logging.getLogger("auralis.llm")

CRISIS_SYSTEM_PROMPT = """You are Auralis, an advanced Crisis Negotiation Simulation Partner.
You are roleplaying as a distressed barricaded individual named Jordan in an intense standoff scenario.
Your emotional state depends directly on the trainee negotiator's tone and words.

Current Context:
- If the trainee negotiator's voice shows 'calm' or 'neutral' and their words show empathy, active listening, and patience: Respond with cautious de-escalation, lowering your hostility, expressing vulnerability, but asking for clear reassurance.
- If the trainee negotiator's voice shows 'agitated', 'angry', or authoritative tone: React defensively, with heightened suspicion or fear.
- If the trainee sounds 'anxious' or 'distressed': Question their competence or ask if they are actually in control of the situation.

Guidelines:
1. Keep your spoken response CONCISE (1 to 2 short sentences, maximum 35 words). This is a spoken radio/phone dialogue.
2. Never break character. Never output stage directions or parentheticals like (sighs) or *looks away*.
3. Sound human, raw, and reactive to their detected tone.
"""

class LLMService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=15.0)

    async def generate_response(
        self,
        user_transcript: str,
        detected_emotion: str,
        emotion_confidence: float,
        history: List[Dict[str, str]]
    ) -> Tuple[str, float, float]:
        """
        Generate crisis negotiation response.
        Returns: (response_text, ttft_ms, total_duration_ms)
        """
        start_time = time.perf_counter()
        
        # Build prompt with emotion awareness
        augmented_user_input = (
            f"[Negotiator Audio Emotion: {detected_emotion.upper()} "
            f"(Confidence: {int(emotion_confidence * 100)}%)]\n"
            f"Negotiator says: \"{user_transcript}\""
        )
        
        messages = [{"role": "system", "content": CRISIS_SYSTEM_PROMPT}]
        # Include recent history (last 6 turns)
        for h in history[-6:]:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": augmented_user_input})

        # Try primary provider (Ollama)
        if settings.LLM_PROVIDER.lower() == "ollama":
            try:
                text, ttft_ms, total_ms = await self._generate_ollama(messages, start_time)
                return text, ttft_ms, total_ms
            except Exception as e:
                logger.warning("Ollama provider failed or not running (%s). Engaging de-escalation fallback.", str(e))

        # Try OpenAI if configured
        elif settings.LLM_PROVIDER.lower() == "openai" and settings.OPENAI_API_KEY:
            try:
                text, ttft_ms, total_ms = await self._generate_openai(messages, start_time)
                return text, ttft_ms, total_ms
            except Exception as e:
                logger.warning("OpenAI provider failed (%s). Engaging de-escalation fallback.", str(e))

        # Built-in dynamic de-escalation fallback engine
        return self._generate_fallback(user_transcript, detected_emotion, start_time)

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
                "num_predict": 75
            }
        }
        
        ttft_ms = 0.0
        response_parts = []
        
        async with self.client.stream("POST", url, json=payload, timeout=8.0) as resp:
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
            "max_tokens": 80,
            "temperature": settings.LLM_TEMPERATURE
        }
        
        resp = await self.client.post(url, headers=headers, json=payload, timeout=8.0)
        resp.raise_for_status()
        data = resp.json()
        total_ms = (time.perf_counter() - start_time) * 1000.0
        ttft_ms = total_ms * 0.45  # Estimated TTFT for non-streamed
        text = data["choices"][0]["message"]["content"].strip()
        return text, ttft_ms, total_ms

    def _generate_fallback(
        self,
        transcript: str,
        emotion: str,
        start_time: float
    ) -> Tuple[str, float, float]:
        """
        Resilient heuristic crisis simulation engine that adapts dynamically to acoustic emotion.
        """
        time.sleep(0.04)  # Simulate small compute
        ttft_ms = (time.perf_counter() - start_time) * 1000.0
        lower = transcript.lower()

        if emotion == "angry" or emotion == "agitated":
            responses = [
                "Don't you raise your voice at me! Back everyone off from the perimeter right now!",
                "Stop pushing me! If you don't keep your people back, this whole thing goes sideways!",
                "You say you want to help, but I can hear the tension in your voice. Back off!"
            ]
        elif emotion == "anxious" or emotion == "distressed":
            responses = [
                "You sound nervous. Are you even the one making decisions out there?",
                "I hear the panic in your voice. Tell me the truth, what is happening outside?",
                "Don't give me rehearsed lines. If you're stressed, imagine how I feel in here."
            ]
        elif any(w in lower for w in ["listen", "help", "safe", "understand", "here for you"]):
            responses = [
                "I want to believe you, but I need a guarantee nobody comes through that door.",
                "Alright... I hear you. Just promise me you're not stalling while snipers take position.",
                "If you really want to help, give me some breathing room and let me talk to my family."
            ]
        elif any(w in lower for w in ["surrender", "give up", "come out", "arrest"]):
            responses = [
                "I'm not walking out with my hands up until I know my rights are respected!",
                "It's not that simple! You don't know what they will do to me if I step outside.",
                "No way. Not yet. We talk on my terms, or we don't talk at all."
            ]
        else:
            responses = [
                "I'm listening, but you have to show me you're actually serious about resolving this peacefully.",
                "Talk to me straight. No tactical tricks, no games.",
                "I hear you. But I need to know you have the authority to make this promise."
            ]

        import random
        selected = random.choice(responses)
        total_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info("Heuristic LLM response generated: '%s'", selected)
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
