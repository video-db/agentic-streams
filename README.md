<div align="center">

# 🎬 Agentic Streams

**Take back control of your content.**  
Agents research the internet, filter noise, and stream you clean video briefings.

[![VideoDB](https://img.shields.io/badge/Powered_by-VideoDB-orange?style=for-the-badge)](https://videodb.io)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![GitHub stars](https://img.shields.io/github/stars/video-db/agentic-videos?style=for-the-badge)](https://github.com/video-db/agentic-videos)

[View Agents](#available-agents) • [Quick Start](#quick-start) • [Documentation](https://docs.videodb.io)

</div>

### Autonomous agents that:
- Crawl the internet (news, social, video sources incl. Youtube)
- Filter bias, noise, and low-signal content
- Gather real assets (video clips, screenshots, charts)
- Generate clean, structured **video streams** with voiceovers and music.
- Stream them directly to you.

👉 No feeds  
👉 No scrolling  
👉 No algorithmic manipulation

---
The internet is noisy, biased, and algorithm-driven.

You don’t control:
- what content reaches you  
- how it is filtered  
- how it is presented  

**Agentic Streams replaces feeds with streams.**

Built on [VideoDB](https://videodb.io), enabling agents to see, hear, and understand the world.

---

## Available Agents

| Agent | Description | Output | Demo |
|-------|-------------|--------|------|
| **[content-creator](content-creator/)** | Research any topic, produce a video briefing, then self-review using VideoDB's See + Understand to verify visual-narration alignment frame by frame | 1-2 min video briefing | [▶ Watch](https://console.videodb.io/player?url=https://play.videodb.io/v1/a43d5463-a39d-4aac-994f-abdfb5b3bf2d.m3u8) |
| **[news-digest](news-digest/)** | Research any topic, gather multi-source evidence (YouTube, tweets, articles), deliver as broadcast-style video | 3-4 min video report | [▶ Watch](https://console.videodb.io/player?url=https://play.videodb.io/v1/43570285-1d6e-4548-86e6-294201d2418f.m3u8) |
| **[financial-market-analysis](financial-market-analysis/)** | Investigate financial markets with charts, screenshots, and verified clips | Custom length market report | [▶ Watch](https://console.videodb.io/player?url=https://play.videodb.io/v1/f37914dd-5239-4c10-aa2e-006f9095ac7c.m3u8) |



## Quick Start

1. **VideoDB Skill**
   ```bash
   npx skills add video-db/skills
   ```
2. **VideoDB API Key** (get free at [console.videodb.io](https://console.videodb.io))
   ```bash
   export VIDEO_DB_API_KEY=your_key_here
   ```


### How It Works

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
### Create your own agents

Each agent follows this pattern:

1. **Research** — Deep web research via browser-use (no hallucinated data)
2. **Asset Gathering** — YouTube clips, tweets, article screenshots, charts
3. **Script Generation** — Professional voiceover scripts with TTS
4. **Video Assembly** — Multi-track composition with VideoDB
5. **Delivery** — Stream URL ready to play and share

**Input:** A topic. **Output:** video stream.


### To add a new agent:
1. Create a new folder with `SKILL.md`, `AGENTS.md`, and `README.md`
2. Follow the structure of existing agents
3. Include working examples

Create your own personalized agent that deliver content according to your preferences. 


---

## More Example Outputs

**r/ClaudeAI Weekly Recap** — Self-reviewed video briefing covering top posts, memes, and drama  
[▶ Watch Video](https://console.videodb.io/player?url=https://play.videodb.io/v1/a43d5463-a39d-4aac-994f-abdfb5b3bf2d.m3u8)

**Iran War 2026** — Multi-source analysis with Al Jazeera, BBC, CNN  
[▶ Watch Video](https://console.videodb.io/player?url=https://play.videodb.io/v1/43570285-1d6e-4548-86e6-294201d2418f.m3u8)

**Daily Market Recap** — Proof-backed financial news with charts, screenshots, and clips  
[▶ Watch Video](https://console.videodb.io/player?url=https://play.videodb.io/v1/f37914dd-5239-4c10-aa2e-006f9095ac7c.m3u8)

---

## Philosophy

Each agent is:

- **Self-contained** — All dependencies are documented. Every fact, URL, and asset comes from real web sources via browser-based research. No hallucinated data.  
- **Reproducible** — Same topic leads to consistent, high-quality outputs.  
- **Fully autonomous** — Give the agent a topic and get a finished video. No manual intervention required.  
- **Evidence-based** — Every claim is sourced. Every asset is verified. Built for news, research, finance, and compliance workflows.  
- **Production-ready** — Reliable, battle-tested pipelines designed for real-world use.  
---

## Community & Support

- **Docs**: [docs.videodb.io](https://docs.videodb.io)
- **Issues**: [GitHub Issues](https://github.com/video-db/agentic-videos/issues)
- **Discord**: [Join community](https://discord.gg/py9P639jGz)
- **Console**: [Get API key](https://console.videodb.io)

---

<p align="center">Made with ❤️ by the <a href="https://videodb.io">VideoDB</a> team</p>

---
