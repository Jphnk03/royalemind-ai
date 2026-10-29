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
