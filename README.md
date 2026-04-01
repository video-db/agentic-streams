# agentic-video-creator

A repo for building **agent-driven video creation workflows**.

This repository is organized as a collection of reusable use cases, each showing how an agent can:
- gather source material
- structure evidence
- assemble media assets
- render a final video

---

## Current use cases

### 1. financial-market-analysis
Proof-first financial news video creation.

Location:
- `financial-market-analysis/`

What it demonstrates:
- article extraction
- screenshot proof
- chart generation
- VideoDB clip search and transcript indexing
- narrated video assembly
- subtitle pass
- caching/reuse strategy for faster iteration

Start here:
- `financial-market-analysis/README.md`

Example:
- `financial-market-analysis/examples/2026-04-01/`

---

## Repo philosophy

Each use case should be:
- self-contained
- reproducible
- easy for agents to follow
- documented with setup, workflow, and example outputs

Recommended structure for each use case:

```text
use-case-name/
  README.md
  AGENTS.md
  docs/
  skills/
  examples/
```

---

## Setup

Each use case may have its own setup instructions.

For the first use case, see:
- `financial-market-analysis/docs/SETUP.md`

---

## Skills

Use-case-specific skills live under each use case.

Example:
- `financial-market-analysis/skills/financial-news-video-agent/SKILL.md`

---

## Intended audience

This repo is for:
- agent builders
- workflow designers
- developers creating automated video pipelines
- teams building proof-backed media generation systems

---

## Next direction

Future use cases can include:
- product demo video generation
- research-to-video explainers
- meeting recap videos
- compliance/evidence video workflows
- educational content generation
