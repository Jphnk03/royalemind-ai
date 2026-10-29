# RoyaleMind Coach Phase 1

Run from the repository root (Python 3.10–3.12):

```bash
python -m royalemind.coach_web
```

Open http://127.0.0.1:8765 on the **same computer**. Data is stored under `coach_data/` by default. Set `ROYALEMIND_COACH_DATA` to another directory to change it. The server intentionally binds to localhost only and is **not accessible from a phone on a different device**. No login, public hosting, video understanding, or third-party AI service is included.

Features: optional MP4/MOV/WebM uploads up to 100 MB, video playback, written decision notes, deterministic coaching exercises, match history, win rate, and recurring focus topics.

**Honest scope:** coaching feedback is keyword-based from notes; uploading a replay alone does not produce visual AI analysis. A later phase can add consent-based replay interpretation, authentication, deployment, and richer progress metrics. This does not connect to the live Clash Royale game.

Test: `python -m pytest -q`. Existing battle rules in `royalemind/core.py` remain untouched.
