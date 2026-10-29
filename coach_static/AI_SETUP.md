# Optional AI replay analysis

The coach app supports **opt-in** analysis of saved replay recordings, via the **Analyze replay with AI** button. Video is never automatically analyzed on upload.

## Local setup

1. Install Python 3.10–3.12 and `ffmpeg`/`ffprobe` on your computer.
2. Configure your OpenAI API key securely in your shell environment: `OPENAI_API_KEY`. **Never commit the key to GitHub.**
3. From the repo root, run `python -m royalemind.coach_web`.
4. Open `http://127.0.0.1:8765`, upload a replay, and explicitly select **Analyze replay with AI**.

The app samples up to 8 still frames and sends them to OpenAI's Responses API. It does not continuously track all card plays, accurately reconstruct every elixir state, or guarantee the right tactical decision. Review confidence and verify against the original video.

This is a **single-user local prototype**, not a deployed iPhone app. The server binds to localhost and has no login or production-ready protections. Do not expose the port publicly. API calls incur model usage charges. Uploaded video stays on the local machine; selected still frames are sent to the model provider only when you request analysis. AI reports are displayed in the current browser session and are not saved to the match database.

For full product readiness: asynchronous background jobs, robust video validation, auth, private cloud storage, data deletion, account settings, model evaluations, tests, and a secure mobile deployment are still required.
