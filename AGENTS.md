# Development instructions — RoyaleMind AI

Read `README.md` and the relevant module and tests before making changes.

- Continue the original Python simulator and existing draft RoyaleMind Coach work. The default `main` branch is not the full Coach application; there are multiple stacked, unmerged Coach draft pull requests. Inspect the actual branch and dependency order before changing or merging anything.
- All development goes on a feature branch and draft pull request. Do not merge, publish, start new paid services, or connect to real game accounts without approval.
- Preserve deterministic simulation rules and seeded reproducibility unless the user's requested feature explicitly requires a change. Do not describe simulated performance as real-game win rates.
- AI replay analysis is opt-in; no automatic paid OpenAI/Anthropic requests. Do not upload private videos or screenshots to third parties without authorization.
- No API keys, login tokens, personal recordings or environment files in commits or logs.
- On the existing Python simulator default branch: `python -m pip install -r requirements-dev.txt` only when dependencies are needed, followed by `python -m pytest -q`.
- For Coach-specific features, first inspect the correct existing draft branch and its requirements; do not assume default-branch tests cover the Coach.
- Record tests actually performed and remaining end-to-end/mobile limitations.

Claude Code is a development tool, not a gameplay agent or deployed dependency.