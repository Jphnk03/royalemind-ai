# RoyaleMind branch review — November 11, 2026

Tracks #10 and Jphnk03/ai-command-center#14. Local prototype only. No host, paid provider, real replay or credential was used.

## Branches and tests

| Branch | Reviewed head | Test result |
|---|---|---|
| main | 4a74f5d6375801bde33ede1674eb645d5ee3a230 | 22 passed |
| learning draft #4 | 0b0b7112838239117d5ccb8cd3cbfc03eaebb799 | 30 passed |
| coaching stack tip #8 | 41781b62f39e01bb0823d4cd517416288c9e2402 | 34 passed before fixes; 36 passed after |

Coaching sequence is #5 -> #6 -> #7 -> #8; #9 is separate Claude tooling. Learning #4 is six commits ahead of the shared ancestor while coaching #8 is nineteen ahead. Neither includes the other. Do not merge them in arbitrary order. Tests at #8 exercise accumulated coaching code, but individual intermediate tips were not rerun independently. Test execution used Python 3.11 and pytest in an isolated venv.

## Hardening in this draft

- An OpenAI key alone previously permitted paid replay analysis. Calls now require the exact ROYALEMIND_REPLAY_AI_ENABLED=true switch as well as a key. Default is off; no runtime switch was enabled. Tests assert zero frame extraction/network calls while disabled, even with a synthetic supplied key.
- The loopback-only server now rejects foreign Host headers and cross-origin/missing-origin POSTs before opening the journal or analyzing a replay. Tests send real HTTP requests only to an ephemeral local server and prove blocked requests create no database and call no analyzer.
- Keep sparse-frame limitations explicit. This remains eight sampled stills, not continuous card/elixir tracking or a validated prediction of player improvement.

## Remaining limits and smallest safe next version

Keep simulator/RL and manual coaching local first. The current web parser uses cgi, removed in Python 3.13; documented support remains Python 3.10–3.12. No packaging for newer Python or claim of secure mobile hosting is made.

For an iPhone-accessible version: preserve the journal data model, add authenticated single-owner access, private per-user media storage with size/type validation and deletion, authenticated streaming, a bounded processing queue, and backup/isolated-restore checks. Keep journal/challenge/elixir tools free of provider calls. AI replay analysis must remain disabled until a separate approved design supplies hard spending limits, concurrency/rate limits and reviewed privacy controls. Current code has no dollar cap. Do not simply expose the localhost port or deploy this draft.

No hosted deployment or production backup exists to verify. Existing local databases/uploads were not opened; all tests use temporary fictional fixtures. Retain a private copy of both journal SQLite and uploaded files before any later local migration. A Git commit is a code rollback, not a data backup.

The new hardening draft is based on #8 and targets its branch so reviewers see only the added fixes; it is not independently mergeable into main before the reviewed stack. Owner must approve the final stack/learning integration order and any hosting or model spending.
