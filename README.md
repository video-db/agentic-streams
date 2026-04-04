<div align="center">

# 🎬 Agentic Videos

**Autonomous agents that deliver information in video** — research any topic, gather real-world assets, and produce broadcast-ready content.

[![VideoDB](https://img.shields.io/badge/Powered_by-VideoDB-orange?style=for-the-badge)](https://videodb.io)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![GitHub stars](https://img.shields.io/github/stars/video-db/agentic-videos?style=for-the-badge)](https://github.com/video-db/agentic-videos)

[View Agents](#available-agents) • [Quick Start](#quick-start) • [Documentation](https://docs.videodb.io)

</div>

---

## What Is This?

Autonomous agents that **research, investigate, and deliver information as video**. Give an agent a topic—any topic—and it will:

- Research across the web (news, social, video sources)
- Gather real assets (clips, screenshots, charts)
- Produce a professional video with voiceover

**Video is the delivery medium. Research is the engine.**

Built on [VideoDB](https://videodb.io) for video infrastructure and designed for Claude Code agents.

---

## Available Agents

| Agent | Description | Output | Demo |
|-------|-------------|--------|------|
| **[news-digest](news-digest/)** | Research any topic, gather multi-source evidence (YouTube, tweets, articles), deliver as broadcast-style video | 3-4 min video report | [▶ Watch](https://console.videodb.io/player?url=https://play.videodb.io/v1/43570285-1d6e-4548-86e6-294201d2418f.m3u8) |
| **[financial-market-analysis](financial-market-analysis/)** | Investigate financial markets with charts, screenshots, and verified clips | Custom length market report | [▶ Watch](https://console.videodb.io/player?url=https://play.videodb.io/v1/f37914dd-5239-4c10-aa2e-006f9095ac7c.m3u8) |

---

## Quick Start

### Prerequisites

1. **VideoDB API Key** (get free at [console.videodb.io](https://console.videodb.io))
   ```bash
   export VIDEO_DB_API_KEY=your_key_here
   ```

2. **VideoDB Python SDK**
   ```bash
   pip install videodb python-dotenv
   ```

3. **VideoDB Skill**
   ```bash
   npx skills add video-db/skills
   ```

### Usage

Each agent has its own detailed README. Pick one and give the agent a topic:

**News Digest** (works on any topic):
```
Create a video report about "climate summit 2026"
```

**Financial Analysis:**
```
Create a market report for 2026-04-01
```

The agent will autonomously research the topic, gather assets, and deliver the video.

---

## How It Works

Each agent follows this pattern:

1. **Research** — Deep web research via browser-use (no hallucinated data)
2. **Asset Gathering** — YouTube clips, tweets, article screenshots, charts
3. **Script Generation** — Professional voiceover scripts with TTS
4. **Video Assembly** — Multi-track composition with VideoDB Editor
5. **Delivery** — Stream URL ready to share

**Input:** A topic. **Output:** A video report.

---

## Example Outputs

### News Digest
**Iran War 2026** — Multi-source analysis with Al Jazeera, BBC, CNN  
[▶ Watch Video](https://console.videodb.io/player?url=https://play.videodb.io/v1/43570285-1d6e-4548-86e6-294201d2418f.m3u8)

### Financial Market Analysis
**Daily Market Recap** — Proof-backed financial news with charts, screenshots, and clips  
[▶ Watch Video](https://console.videodb.io/player?url=https://play.videodb.io/v1/f37914dd-5239-4c10-aa2e-006f9095ac7c.m3u8)

---

## Key Features

### 🔍 Deep Research
Every fact, URL, and asset comes from real web sources. Browser-use handles all internet access. No hallucinated data.

### 📺 Video as Delivery
Information delivered as professional video—broadcast-style overlays, multi-track composition, voiceovers, and clean typography.

### 🤖 Fully Autonomous
Give the agent a topic → get a finished video. No manual intervention required.

### 📊 Evidence-Based
Every claim is sourced. Every asset is verified. Perfect for news, research, finance, and compliance use cases.

---

## Philosophy

Each agent is:
- **Self-contained** — All dependencies documented
- **Reproducible** — Same topic → consistent quality
- **Autonomous** — Clear instructions, no hand-holding
- **Production-ready** — Battle-tested workflows

---

## Requirements

- Python 3.8+
- VideoDB API key ([get free](https://console.videodb.io))
- VideoDB SDK and skill
- Claude Code or compatible agent framework

---

## Contributing

Contributions welcome! To add a new agent:

1. Create a new folder with `SKILL.md`, `AGENTS.md`, and `README.md`
2. Follow the structure of existing agents
3. Include working examples
4. Submit a PR

---


## Community & Support

- **Docs**: [docs.videodb.io](https://docs.videodb.io)
- **Issues**: [GitHub Issues](https://github.com/video-db/agentic-videos/issues)
- **Discord**: [Join community](https://discord.gg/py9P639jGz)
- **Console**: [Get API key](https://console.videodb.io)

---

<p align="center">Made with ❤️ by the <a href="https://videodb.io">VideoDB</a> team</p>

---
