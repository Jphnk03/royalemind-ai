"""Command-line tournament runner."""
import argparse
from .core import Battle
from .agents import RandomAgent, RushAgent


def main():
    parser = argparse.ArgumentParser(description='RoyaleMind AI battle simulator')
    parser.add_argument('--matches', type=int, default=100)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--duration', type=int, default=180)
    args = parser.parse_args()
    if args.matches < 1:
        parser.error('--matches must be positive')
    wins = [0, 0]
    draws = 0
    for index in range(args.matches):
        battle = Battle(seed=args.seed + index, duration=args.duration)
        agents = (RushAgent(), RandomAgent()) if index % 2 == 0 else (RandomAgent(), RushAgent())
        while not battle.done:
            battle.step(tuple(agent.choose(battle, player)
                              for player, agent in enumerate(agents)))
        if battle.winner is None:
            draws += 1
        else:
            wins[0 if isinstance(agents[battle.winner], RushAgent) else 1] += 1
    print(f'Matches: {args.matches} | Seed: {args.seed}')
    print(f'RushAgent: {wins[0]} wins ({100*wins[0]/args.matches:.1f}%)')
    print(f'RandomAgent: {wins[1]} wins ({100*wins[1]/args.matches:.1f}%)')
    print(f'Draws: {draws} ({100*draws/args.matches:.1f}%)')


if __name__ == '__main__':
    main()
