"""Side-aware holdout benchmarks for learned and scripted RoyaleMind agents."""
import argparse
from .agents import RandomAgent, RushAgent
from .core import Battle
from .learning import QAgent, load_model
from .strategy import StrategyAgent

BASELINES = {'strategy': StrategyAgent, 'random': RandomAgent, 'rush': RushAgent}


def compare(learner_factory, opponent_factory, matches=200, seed=200000, duration=180):
    """Play paired seeds with swapped sides and report outcomes per side."""
    if matches < 2 or matches % 2 or duration < 1:
        raise ValueError('matches must be even and >= 2; duration must be positive')
    result = {'learned': 0, 'opponent': 0, 'draws': 0,
              'by_side': {0: {'learned': 0, 'opponent': 0, 'draws': 0},
                          1: {'learned': 0, 'opponent': 0, 'draws': 0}}}
    for i in range(matches // 2):
        for player in (0, 1):
            battle = Battle(seed=seed+i, duration=duration)
            learner = learner_factory()
            opponent = opponent_factory()
            while not battle.done:
                action = learner.choose(battle, player)
                other = opponent.choose(battle, 1-player)
                battle.step((action, other) if player == 0 else (other, action))
            outcome = ('draws' if battle.winner is None else
                       'learned' if battle.winner == player else 'opponent')
            result[outcome] += 1
            result['by_side'][player][outcome] += 1
    return result


def benchmark(table, matches=200, seeds=(200000, 300000, 400000), duration=180):
    if not seeds:
        raise ValueError('at least one seed required')
    output = {}
    for name, opponent in BASELINES.items():
        output[name] = []
        for seed in seeds:
            output[name].append(compare(lambda: QAgent(table), opponent,
                                        matches=matches, seed=seed, duration=duration))
    output['strategy_self_play'] = [compare(StrategyAgent, StrategyAgent,
                                           matches=matches, seed=seed, duration=duration)
                                    for seed in seeds]
    return output


def main():
    parser = argparse.ArgumentParser(description='Side-aware multi-seed holdout benchmark')
    parser.add_argument('--model', default='royalemind-q.json')
    parser.add_argument('--matches', type=int, default=200)
    parser.add_argument('--seeds', type=int, nargs='+', default=[200000, 300000, 400000])
    parser.add_argument('--duration', type=int, default=180)
    args = parser.parse_args()
    results = benchmark(load_model(args.model), args.matches, tuple(args.seeds), args.duration)
    for name, runs in results.items():
        for seed, stats in zip(args.seeds, runs):
            print(f'{name} seed={seed}: {stats}')


if __name__ == '__main__':
    main()
