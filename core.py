"""Deterministic, discrete-time two-lane battle environment."""
from dataclasses import dataclass
from random import Random

TROOPS = {
    'scout': {'cost': 2, 'hp': 60, 'damage': 16, 'speed': 2, 'range': 1},
    'guard': {'cost': 3, 'hp': 140, 'damage': 22, 'speed': 1, 'range': 1},
    'archer': {'cost': 4, 'hp': 70, 'damage': 25, 'speed': 1, 'range': 3},
}
LANES = (0, 1)
LENGTH = 12
MAX_ELIXIR = 10


@dataclass(frozen=True)
class Action:
    card: str
    lane: int


@dataclass
class Unit:
    owner: int
    card: str
    lane: int
    pos: int
    hp: int
    uid: int


class Battle:
    """Both agents act simultaneously; one step represents one second."""
    def __init__(self, seed=0, duration=180):
        if duration < 1:
            raise ValueError('duration must be positive')
        self.rng = Random(seed)
        self.duration = duration
        self.time = 0
        self.elixir = [5, 5]
        self.towers = [1000, 1000]
        self.units = []
        self.next_uid = 0
        self.done = False
        self.winner = None

    def legal_actions(self, player):
        self._check_player(player)
        if self.done:
            return []
        return [Action(card, lane) for card, stats in TROOPS.items()
                if stats['cost'] <= self.elixir[player] for lane in LANES]

    @staticmethod
    def _check_player(player):
        if player not in (0, 1):
            raise ValueError('player must be 0 or 1')

    def _deploy(self, player, action):
        if action is None:
            return
        if not isinstance(action, Action) or action not in self.legal_actions(player):
            raise ValueError(f'illegal action for player {player}: {action!r}')
        stats = TROOPS[action.card]
        self.elixir[player] -= stats['cost']
        self.units.append(Unit(player, action.card, action.lane,
                               0 if player == 0 else LENGTH,
                               stats['hp'], self.next_uid))
        self.next_uid += 1

    def step(self, actions=(None, None)):
        if self.done:
            raise RuntimeError('match is finished')
        if len(actions) != 2:
            raise ValueError('expected two actions')
        # Validate both before mutating state.
        for player, action in enumerate(actions):
            if action is not None and action not in self.legal_actions(player):
                raise ValueError(f'illegal action for player {player}: {action!r}')
        for player, action in enumerate(actions):
            self._deploy(player, action)

        # Every living unit chooses one target based on the same pre-combat snapshot.
        attacks = []
        for unit in self.units:
            stats = TROOPS[unit.card]
            enemies = [e for e in self.units if e.owner != unit.owner
                       and e.lane == unit.lane and e.hp > 0]
            enemies.sort(key=lambda e: (abs(e.pos - unit.pos), e.uid))
            if enemies and abs(enemies[0].pos - unit.pos) <= stats['range']:
                attacks.append(('unit', enemies[0].uid, stats['damage']))
            elif (LENGTH - unit.pos if unit.owner == 0 else unit.pos) <= stats['range']:
                attacks.append(('tower', 1 - unit.owner, stats['damage']))
            else:
                direction = 1 if unit.owner == 0 else -1
                unit.pos = max(0, min(LENGTH, unit.pos + direction * stats['speed']))
        for kind, target, damage in attacks:
            if kind == 'tower':
                self.towers[target] = max(0, self.towers[target] - damage)
            else:
                for unit in self.units:
                    if unit.uid == target:
                        unit.hp -= damage
                        break
        self.units = [unit for unit in self.units if unit.hp > 0]
        self.time += 1
        self.elixir = [min(MAX_ELIXIR, value + 1) for value in self.elixir]
        if min(self.towers) <= 0 or self.time >= self.duration:
            self.done = True
            self.winner = (0 if self.towers[0] > self.towers[1] else
                           1 if self.towers[1] > self.towers[0] else None)
        return self.done

    def observe(self, player):
        self._check_player(player)
        return {'time': self.time, 'elixir': tuple(self.elixir),
                'towers': tuple(self.towers),
                'units': tuple((u.owner, u.card, u.lane, u.pos, u.hp)
                               for u in sorted(self.units, key=lambda u: u.uid)),
                'legal_actions': tuple(self.legal_actions(player)),
                'done': self.done, 'winner': self.winner}
