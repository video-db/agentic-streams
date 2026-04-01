# Setup Guide

## 1. Clone the repo

```bash
git clone <your-repo-url>
cd fin-news
```

---

## 2. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:
```bash
uv --version
```

---

## 3. Install Node.js

Playwright screenshots require Node.

Verify:
```bash
node --version
npm --version
npx --version
```

---

## 4. Install Playwright browser

```bash
npx playwright install chromium
```

This is only needed if you want webpage screenshots.

---

## 5. Configure VideoDB

Create `.env` in repo root:

```env
VIDEO_DB_API_KEY=your_api_key_here
```

Get a key from:
- https://console.videodb.io

---

## 6. Optional market data configuration

If you later add premium market data:

```env
POLYGON_API_KEY=
ALPHA_VANTAGE_API_KEY=
FINNHUB_API_KEY=
```

Current examples in this repo can work with Yahoo Finance public endpoints for chart generation.

---

## 7. Recommended agent skills

If your agent platform supports skills, make sure it can access:

### Required
- VideoDB skill
- URL-to-Markdown skill
- uv skill

### Helpful
- screenshot/browser skill
- market-data skill
- SEC filing skill

---

## 8. Test the environment

### Test VideoDB auth
```bash
uv run --with videodb --with python-dotenv python - <<'PY'
from dotenv import load_dotenv
load_dotenv('.env')
import videodb
conn = videodb.connect()
print('connected')
PY
```

### Test Playwright
```bash
npx playwright screenshot https://example.com test.png
```

---

## 9. Run an example day

```bash
uv run 2026-04-01/make_video.py
```

---

## 10. Common issues

### VideoDB auth failure
Make sure:
- `.env` exists
- `VIDEO_DB_API_KEY` is valid
- scripts are run from repo root

### Playwright browser missing
Run:
```bash
npx playwright install chromium
```

### Voice-generation plan limits
If your VideoDB plan limits TTS generation:
- reuse existing narration assets
- store audio ids in `audio_registry.json`
- do subtitle/final polish after draft approval

### Repeated uploads slow things down
Use registries and reuse asset ids instead of re-uploading screenshots and clips.
