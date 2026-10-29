"""Reproducible 1,000-match evaluation of the v0.2 strategy agent."""
import argparse
from .agents import RandomAgent, RushAgent
from .core import Battle
from .strategy import StrategyAgent


def evaluate(matches=1000, seed=42, duration=180):
    """Return match counts; split matches across two baselines, alternating sides."""
    if matches < 2 or duration < 1:
        raise ValueError('matches must be >= 2 and duration must be positive')
    results = {}
    for name, baseline in [('RandomAgent', RandomAgent), ('RushAgent', RushAgent)]:
        n = matches // 2 + (1 if name == 'RandomAgent' and matches % 2 else 0)
        results[name] = {'strategy': 0, 'baseline': 0, 'draws': 0, 'matches': n}
        offset = 0 if name == 'RandomAgent' else (matches + 1) // 2
        for i in range(n):
            battle = Battle(seed=seed + offset + i, duration=duration)
            strategy_player = i % 2
            agents = (StrategyAgent(), baseline()) if strategy_player == 0 else (baseline(), StrategyAgent())
            while not battle.done:
                battle.step(tuple(agent.choose(battle, p) for p, agent in enumerate(agents)))
            if battle.winner is None:
                results[name]['draws'] += 1
            elif battle.winner == strategy_player:
                results[name]['strategy'] += 1
            else:
                results[name]['baseline'] += 1
    return results


def main():
    parser = argparse.ArgumentParser(description='RoyaleMind v0.2 tournament')
    parser.add_argument('--matches', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--duration', type=int, default=180)
    args = parser.parse_args()
    if args.matches < 2 or args.duration < 1:
        parser.error('--matches must be >= 2 and --duration must be positive')
    results = evaluate(args.matches, args.seed, args.duration)
    print(f'RoyaleMind v0.2 | {args.matches} matches | seed {args.seed} | duration {args.duration}')
    for name, stats in results.items():
        print(f'vs {name}: StrategyAgent {stats["strategy"]} wins, '
              f'{name} {stats["baseline"]} wins, {stats["draws"]} draws '
              f'({stats["matches"]} matches)')


if __name__ == '__main__':
    main()
