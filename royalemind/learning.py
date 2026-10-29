"""Tabular Q-learning against StrategyAgent; no changes to battle rules."""
import json
from pathlib import Path
from random import Random
from .core import Action, Battle, LENGTH
from .strategy import StrategyAgent

ACTIONS = (None,) + tuple(Action(card, lane) for card in ('scout', 'guard', 'archer') for lane in (0, 1))
FORMAT = 'royalemind-tabular-q-v2'
TEACHER = StrategyAgent()

def encode_state(battle, player):
    """Player-relative elixir, lane counts, advance, towers, and time."""
    state = [min(5, battle.elixir[player] // 2)]
    for owner in (player, 1-player):
        for lane in (0, 1):
            units = [u for u in battle.units if u.owner == owner and u.lane == lane]
            state.append(min(3, len(units)))
            advance = [u.pos if owner == 0 else LENGTH-u.pos for u in units]
            state.append(max((min(3, pos // 4) for pos in advance), default=0))
    state.extend((min(4, battle.towers[player] // 250),
                  min(4, battle.towers[1-player] // 250),
                  min(3, (battle.duration-battle.time) * 4 // battle.duration)))
    return tuple(state)

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
        if state not in self.table:
            return TEACHER.choose(battle, player)
        values = self.table[state]
        return max(options, key=lambda a: (values[action_id(a)], -action_id(a)))

def _new_row(teacher_action):
    values = [0.0] * len(ACTIONS)
    values[action_id(teacher_action)] = 2.0
    return values

def train(episodes=1000, seed=42, duration=180, alpha=0.15, gamma=0.90):
    if episodes < 1 or duration < 1 or not 0 < alpha <= 1 or not 0 <= gamma <= 1:
        raise ValueError('invalid training configuration')
    table = {}
    agent = QAgent(table, seed=seed+100000)
    for episode in range(episodes):
        battle = Battle(seed=seed+episode, duration=duration)
        player = episode % 2
        agent.epsilon = max(0.03, 0.30 * (1 - episode / episodes))
        while not battle.done:
            state = encode_state(battle, player)
            teacher_action = TEACHER.choose(battle, player)
            row = table.setdefault(state, _new_row(teacher_action))
            action = agent.choose(battle, player)
            before_towers = tuple(battle.towers)
            other = TEACHER.choose(battle, 1-player)
            battle.step((action, other) if player == 0 else (other, action))
            damage = ((before_towers[1-player] - battle.towers[1-player]) -
                      (before_towers[player] - battle.towers[player])) / 40.0
            reward = damage + (0.6 if action == teacher_action else -0.25)
            if battle.done:
                reward += (15 if battle.winner == player else
                           -15 if battle.winner is not None else 0)
            if battle.done:
                future = 0.0
            else:
                next_state = encode_state(battle, player)
                next_teacher = TEACHER.choose(battle, player)
                next_row = table.setdefault(next_state, _new_row(next_teacher))
                future = max(next_row[action_id(a)] for a in [None] + battle.legal_actions(player))
            index = action_id(action)
            row[index] += alpha * (reward + gamma * future - row[index])
    return table

def save_model(table, path):
    data = {'format': FORMAT, 'actions': len(ACTIONS),
            'q': [{'state': list(s), 'values': v} for s, v in sorted(table.items())]}
    Path(path).write_text(json.dumps(data, allow_nan=False, separators=(',', ':')), encoding='utf-8')

def load_model(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('format') != FORMAT or data.get('actions') != len(ACTIONS):
        raise ValueError('unsupported model format (v0.3 models must be retrained)')
    rows = data.get('q')
    if not isinstance(rows, list):
        raise ValueError('invalid model rows')
    table = {}
    for row in rows:
        state, values = row['state'], row['values']
        if (not isinstance(state, list) or len(state) != 12 or
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
            other = TEACHER.choose(battle, 1-player)
            battle.step((action, other) if player == 0 else (other, action))
        key = 'draws' if battle.winner is None else ('learned' if battle.winner == player else 'strategy')
        counts[key] += 1
    return counts
