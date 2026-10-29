"""Tabular Q-learning against StrategyAgent; no changes to battle rules."""
import json
from pathlib import Path
from random import Random
from .core import Action, Battle
from .strategy import StrategyAgent

ACTIONS = (None,) + tuple(Action(card, lane) for card in ('scout', 'guard', 'archer') for lane in (0, 1))
FORMAT = 'royalemind-tabular-q-v1'

def encode_state(battle, player):
    def pressure(owner, lane):
        return min(2, sum(u.owner == owner and u.lane == lane for u in battle.units))
    return (min(3, battle.elixir[player] // 3),
            *(pressure(player, lane) for lane in (0, 1)),
            *(pressure(1-player, lane) for lane in (0, 1)),
            int(battle.towers[player] < battle.towers[1-player]))

def action_id(action):
    return ACTIONS.index(action)

class QAgent:
    def __init__(self, table=None, epsilon=0.0, seed=0):
        if not 0 <= epsilon <= 1:
            raise ValueError('invalid epsilon')
        self.table = {} if table is None else table
        self.epsilon = epsilon
        self.rng = Random(seed)

    def choose(self, battle, player):
        options = [None] + battle.legal_actions(player)
        state = encode_state(battle, player)
        if self.rng.random() < self.epsilon:
            return self.rng.choice(options)
        values = self.table.get(state, [0.0] * len(ACTIONS))
        return max(options, key=lambda a: (values[action_id(a)], -action_id(a)))

def train(episodes=1000, seed=42, duration=180, alpha=0.2, gamma=0.95):
    if episodes < 1 or duration < 1 or not 0 < alpha <= 1 or not 0 <= gamma <= 1:
        raise ValueError('invalid training configuration')
    table = {}
    agent = QAgent(table, seed=seed+100000)
    opponent = StrategyAgent()
    for episode in range(episodes):
        battle = Battle(seed=seed+episode, duration=duration)
        player = episode % 2
        agent.epsilon = max(0.05, 0.8 * (1 - episode / episodes))
        while not battle.done:
            state = encode_state(battle, player)
            action = agent.choose(battle, player)
            before = (battle.towers[player], battle.towers[1-player])
            other = opponent.choose(battle, 1-player)
            battle.step((action, other) if player == 0 else (other, action))
            reward = ((before[1] - battle.towers[1-player]) -
                      (before[0] - battle.towers[player])) / 100.0
            if battle.done:
                reward += 10.0 if battle.winner == player else (-10.0 if battle.winner is not None else 0.0)
            row = table.setdefault(state, [0.0] * len(ACTIONS))
            index = action_id(action)
            if battle.done:
                future = 0.0
            else:
                following = table.get(encode_state(battle, player), [0.0] * len(ACTIONS))
                future = max(following[action_id(a)] for a in [None] + battle.legal_actions(player))
            row[index] += alpha * (reward + gamma * future - row[index])
    return table

def save_model(table, path):
    data = {'format': FORMAT, 'actions': len(ACTIONS),
            'q': [{'state': list(s), 'values': v} for s, v in sorted(table.items())]}
    Path(path).write_text(json.dumps(data, allow_nan=False, separators=(',', ':')), encoding='utf-8')

def load_model(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('format') != FORMAT or data.get('actions') != len(ACTIONS):
        raise ValueError('unsupported model format')
    rows = data.get('q')
    if not isinstance(rows, list):
        raise ValueError('invalid model rows')
    table = {}
    for row in rows:
        state, values = row['state'], row['values']
        if (not isinstance(state, list) or len(state) != 6 or
            not all(type(x) is int for x in state) or
            not isinstance(values, list) or len(values) != len(ACTIONS) or
            not all(type(x) in (int, float) and abs(x) < 1e12 for x in values)):
            raise ValueError('invalid model row')
        key = tuple(state)
        if key in table:
            raise ValueError('duplicate model state')
        table[key] = values
    return table

def evaluate(table, matches=200, seed=100000, duration=180):
    if matches < 1 or duration < 1:
        raise ValueError('invalid evaluation configuration')
    counts = {'learned': 0, 'strategy': 0, 'draws': 0}
    for i in range(matches):
        battle = Battle(seed=seed+i, duration=duration)
        player = i % 2
        learner = QAgent(table, seed=seed+100000+i)
        opponent = StrategyAgent()
        while not battle.done:
            action = learner.choose(battle, player)
            other = opponent.choose(battle, 1-player)
            battle.step((action, other) if player == 0 else (other, action))
        key = 'draws' if battle.winner is None else ('learned' if battle.winner == player else 'strategy')
        counts[key] += 1
    return counts
