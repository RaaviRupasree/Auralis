# Auralis Deployment & Production Guide

This document evaluates hosting providers, network requirements (WebRTC & WebSockets), and provides production deployment configurations.

---

## 1. Production Architecture Evaluation

| Criterion | Evaluation & Recommendation |
|---|---|
| **Frontend + Backend Unification** | Recommended: Host unified via Docker on a persistent container or VM. The FastAPI server directly serves the compiled React SPA from `/assets` and `index.html`. This eliminates CORS and multi-host synchronization. |
| **Transport Protocol** | Auralis supports **both WebSockets (`/ws/audio`) and WebRTC (`aiortc`)**. WebSockets provide 100% firewall, reverse-proxy, and HTTPS penetration across all major cloud providers (Google Cloud Run, AWS App Runner, Render, Railway), avoiding UDP/ICE port blocking common in serverless container environments. |
| **CPU / RAM Sizing** | Recommended minimum: **2 vCPUs, 2 GB RAM**. Faster-Whisper `tiny.en` runs at ~150–300ms on 2 vCPUs without GPU requirement. |
| **Persistent Storage** | Mount a volume for SQLite database (`auralis.db`) to retain session history across container redeployments. |
| **Cold Starts** | Maintain a minimum of 1 warm instance (`min-instances: 1` on Cloud Run) to prevent model download delays during active sessions. |

---

## 2. Docker Production Deployment

### Dockerfile
Auralis includes a production multi-stage `Dockerfile`:
```dockerfile
# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend & Static SPA
FROM python:3.10-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

ENV PYTHONPATH=/app/backend
ENV PORT=8080
ENV HOST=0.0.0.0
ENV ENVIRONMENT=production

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8080/api/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Docker Compose
Run with a single command:
```bash
docker compose up -d --build
```

---

## 3. Cloud Provider Deployments

### Option A: Google Cloud Run (Recommended for Scalability)
Google Cloud Run provides managed HTTPS, automatic TLS certificates, and WebSocket support out of the box.

1. Build and push container to Google Artifact Registry:
   ```bash
   gcloud builds submit --tag gcr.io/[PROJECT-ID]/auralis:latest
   ```
2. Deploy service:
   ```bash
   gcloud run deploy auralis \
     --image gcr.io/[PROJECT-ID]/auralis:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 2Gi \
     --cpu 2 \
     --min-instances 1 \
     --port 8080
   ```

### Option B: Render / Railway / Fly.io (Zero-Config PaaS)
1. Link your GitHub repository.
2. Select **Dockerfile** as the build runtime.
3. Configure environment variables in the dashboard:
   - `PORT=8080`
   - `ENVIRONMENT=production`
   - `LLM_PROVIDER=heuristic_fallback` (or `openai` with `OPENAI_API_KEY`)
4. Deploy. Render and Railway automatically provision SSL/TLS and forward WebSocket connections.

---

## 4. HTTPS & Microphone Security Requirements

Browsers require a **Secure Context (HTTPS or localhost)** to grant `navigator.mediaDevices.getUserMedia` microphone permissions. In production:
- Ensure reverse proxies (Nginx, Caddy, Cloudflare, or AWS ALB) terminate TLS.
- Set header: `Upgrade: $http_upgrade` and `Connection: "upgrade"` to preserve WebSocket upgrades.
