"""Train, save and independently evaluate a tabular Q-learning agent."""
import argparse
from .learning import evaluate, load_model, save_model, train

def main():
    parser = argparse.ArgumentParser(description='RoyaleMind v0.3 Q-learning')
    parser.add_argument('--episodes', type=int, default=1000)
    parser.add_argument('--matches', type=int, default=200)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--duration', type=int, default=180)
    parser.add_argument('--model', default='royalemind-q.json')
    parser.add_argument('--evaluate-only', action='store_true')
    args = parser.parse_args()
    if args.matches < 1 or args.duration < 1 or (not args.evaluate_only and args.episodes < 1):
        parser.error('matches, duration and training episodes must be positive')
    if args.evaluate_only:
        table = load_model(args.model)
    else:
        table = train(args.episodes, args.seed, args.duration)
        save_model(table, args.model)
        table = load_model(args.model)
    results = evaluate(table, args.matches, args.seed + max(args.episodes, 1) + 10000, args.duration)
    print(f'Q-learning states: {len(table)} | model: {args.model}')
    print(f'Evaluation ({args.matches} matches): {results}')

if __name__ == '__main__':
    main()
