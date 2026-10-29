# RoyaleMind AI v0.1

A standalone, deterministic, **headless** Python simulator inspired by lane-based tower defense games. It does **not** connect to Clash Royale or automate gameplay.

## Requirements

Python 3.10+; no runtime dependencies. `pytest` is needed only for tests.

## Run

From the repository root:

```bash
python -m royalemind.cli
python -m royalemind.cli --matches 100 --seed 42 --duration 180
```

## Test

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Rules

- Two players each defend one tower with 1,000 HP.
- Two lanes (0 and 1), positions 0 through 12. Player 0 starts at 0, player 1 at 12.
- Both start with 5 elixir, regenerate 1 per tick, capped at 10.
- Each tick, players may deploy one affordable troop or pass. Illegal actions raise `ValueError` before either deployment is applied.
- Three troops: scout (fast/cheap), guard (tanky), archer (ranged).
- Units target the nearest enemy in their lane within range; otherwise attack the enemy tower when in range, or advance.
- Combat damage is simultaneous. Dead units are removed after all attacks resolve.
- Tower destruction or timeout ends the match. Higher remaining tower HP wins; equal HP is a draw.
- Seeded randomness controls random agent decisions. No external I/O or wall-clock dependence in simulation.
- Tournament alternates agent sides to reduce side advantage.

## Project layout

- `royalemind/core.py`: environment, actions, observation and step function.
- `royalemind/agents.py`: random and rush baseline policies.
- `royalemind/cli.py`: tournament entrypoint.
- `tests/`: pytest coverage for core mechanics.

## Future reinforcement learning

An RL policy can call `observe(player)`, choose an `Action` from `legal_actions(player)` (or pass), then call `step((action0, action1))`. Add observation encoding, reward functions, action masks and separate seeded policy RNGs before training. This toy simulator is intentionally not a faithful implementation of Clash Royale.

## v0.2 strategy agent and tournament

`StrategyAgent` is a deterministic **heuristic** policy (not reinforcement learning). It evaluates friendly lane support, nearby enemy pressure, troop strength and available elixir, while leaving the v0.1 battle rules unchanged.

Run a reproducible tournament with 1,000 matches, split evenly between RandomAgent and RushAgent, alternating sides within each matchup:

```bash
python -m royalemind.tournament --matches 1000 --seed 42 --duration 180
python -m pytest -q
```

The tournament reports wins, losses, and draws per opponent. Results are from the simplified simulator and do not measure performance against human Clash Royale players.

## v0.3 reinforcement learning

The new `QAgent` uses **tabular Q-learning**, with a compact player-relative state encoding, epsilon-greedy exploration, terminal win/loss rewards, and tower-damage shaping. It trains against the existing `StrategyAgent` while leaving `core.py` and all battle rules unchanged. No extra runtime packages are required.

Train, save a JSON model, reload it, and evaluate against StrategyAgent on separate seeds with alternating sides:

```bash
python -m royalemind.train --episodes 1000 --matches 200 --seed 42 --model royalemind-q.json
```

Evaluate an existing saved model:

```bash
python -m royalemind.train --evaluate-only --matches 200 --seed 42 --model royalemind-q.json
```

Run tests: `python -m pytest -q`. The model file is gitignored because it is a generated training artifact. This is a small, interpretable learning baseline, not a neural network. Evaluation is against a scripted agent in a toy simulator; results do not imply performance in live Clash Royale.

## v0.3.1 learning repair

The Q-learning agent now observes relative lane counts and advance, elixir, tower health, and remaining time. Training uses StrategyAgent as a **teacher prior** (imitation-shaped rewards and initial action values) with exploratory Q-learning updates; unseen states fall back to StrategyAgent. This is a hybrid learner, **not an independently learned policy**, so compare against the teacher carefully.

The saved JSON format is now `royalemind-tabular-q-v2`. Old v0.3 models are incompatible; retrain them. No battle rules have changed.

```bash
python -m pytest -q
python -m royalemind.train --episodes 1000 --matches 200 --seed 42
```

Local evaluation with seed 42 and 180 ticks after 1,000 training episodes: learned agent 100 wins, StrategyAgent 100 wins, 0 draws (200 matches). This is **50%**, not a demonstrated improvement over the teacher, and further evaluation is needed.

### Side-aware multi-seed benchmark

Train a model, then benchmark on three held-out seeds against StrategyAgent, RandomAgent, and RushAgent, plus a StrategyAgent self-play control:

```bash
python -m royalemind.train --episodes 1000 --matches 200 --seed 42
python -m royalemind.benchmark --model royalemind-q.json --matches 200 --seeds 200000 300000 400000
python -m pytest -q
```

Local results from 600 matches per opponent: vs StrategyAgent **300 wins / 300 losses**; vs RandomAgent **511 wins / 88 losses / 1 draw**; vs RushAgent **600 wins / 0 losses**. The StrategyAgent self-play control also finished 300/300, with **player 1 winning every match**. Against StrategyAgent, the learner won only as player 1, revealing a strong simulator side bias. Therefore, **50% is not evidence of improved learning**. The battle engine remains unchanged. The benchmark prints per-side breakdowns to prevent misleading aggregate comparisons.
