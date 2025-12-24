# ASX Financial Podcast Automation 🇦🇺📈

**A "Headless Content Factory" that autonomously produces broadcast-quality financial news podcasts.**

This system acts as a fully automated media pipeline. It ingests raw market data from RSS and YouTube, filters news using semantic vector search to prevent repetition, scripts a professional briefing using GPT-4o, and synthesizes audio using ElevenLabs.

The result is a twice-daily podcast (Morning & Afternoon editions) distributed automatically to Spotify and Apple Podcasts via a self-hosted RSS feed.

---

## 🏗 System Architecture

The pipeline follows a strict **ETL (Extract, Transform, Load)** pattern optimized for audio:

1.  **Ingest (The Senses):**
    * **RSS Scrapers:** Monitors *Market Index*, *Motley Fool*, and *Livewire* for text updates.
    * **Audio Extractors:** Uses `yt-dlp` to pull audio from *CommSec*, *Rask*, and *Ausbiz* YouTube channels.
    * **Transcription:** Deepgram Nova-2 (Finance Model) converts audio to text in milliseconds.

2.  **Memory (The Brain):**
    * **Deduplication:** Uses **ChromaDB** (Vector Database) + OpenAI Embeddings to semantically compare new stories against the last 24 hours of coverage.
    * *Result:* Prevents the "broken record" effect where the bot repeats the same story from different sources.

3.  **Production (The Studio):**
    * **Scripting Agent:** GPT-4o writes a concise script with a "Senior Financial Analyst" persona (Direct, Terse, No Fluff).
    * **Audio Synthesis:** ElevenLabs Turbo v2.5 generates human-parity speech (Australian Accent).
    * **Mixing:** `FFmpeg` stitches voice segments with Intro/Outro music and normalizes loudness to -16 LUFS (Broadcast Standard).

4.  **Distribution (The Network):**
    * **Hosting:** Uploads MP3s to **Cloudflare R2** (S3-compatible, Zero Egress Fees).
    * **RSS:** Automatically updates the XML feed to trigger push notifications on podcast apps.

---

## 🛠 Tech Stack

* **Core:** Python 3.11+, `asyncio`
* **Data Models:** `Pydantic` v2 (Strict Typing)
* **AI & Logic:** `OpenAI` (GPT-4o), `Deepgram` (Nova-2), `ElevenLabs` (Turbo v2.5)
* **Memory:** `ChromaDB` (Local Vector Store)
* **Infrastructure:** `Docker` (Optional), `FFmpeg`, `Cloudflare R2` (via `boto3`)

---
⚠️ Disclaimer
This project is an automated news aggregation tool. It does not provide financial advice. All content is AI-generated summaries of public news sources.

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/yourusername/asx-automation-bot.git](https://github.com/yourusername/asx-automation-bot.git)
cd asx-automation-bot

├── app/
│   ├── audio/          # ElevenLabs & FFmpeg mixing logic
│   ├── core/           # Config & Logging
│   ├── distribution/   # RSS & Cloudflare R2 uploader
│   ├── engine/         # LLM Scripting Agent
│   ├── ingest/         # RSS & YouTube Workers
│   ├── memory/         # Vector Deduplication (ChromaDB)
│   └── models/         # Pydantic Data Contracts
├── assets/             # Intro/Outro music files
├── main.py             # Entry point & Orchestration
└── requirements.txt

# AI Providers
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...
ELEVENLABS_API_KEY=...

# Storage (Cloudflare R2)
R2_ENDPOINT_URL=https://...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=...
R2_PUBLIC_DOMAIN=...
