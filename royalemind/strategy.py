"""Deterministic, rule-based strategy policy for the v0.1 simulator.

This is a heuristic baseline, not a trained model. It reads only public battle
state, returns legal actions, and never modifies the simulation environment.
"""
from .core import LENGTH, TROOPS


class StrategyAgent:
    """Respond to threats, support friendly units, and avoid wasting elixir."""

    def choose(self, battle, player):
        actions = battle.legal_actions(player)
        if not actions:
            return None
        # At most one deployment per tick; allow saving for a stronger card.
        own_elixir = battle.elixir[player]
        if own_elixir < 4 and not self._immediate_threat(battle, player):
            return None

        def score(action):
            lane = action.lane
            own = [u for u in battle.units if u.owner == player and u.lane == lane]
            enemy = [u for u in battle.units if u.owner != player and u.lane == lane]
            # Friendly pressure rewards coordinated attacks; hostile pressure
            # near our tower makes defending that lane more urgent.
            own_pressure = sum(u.hp / TROOPS[u.card]['hp'] for u in own)
            enemy_pressure = sum(
                (1 + (u.pos / LENGTH if player == 0 else (LENGTH - u.pos) / LENGTH))
                * u.hp / TROOPS[u.card]['hp'] for u in enemy
            )
            troop = TROOPS[action.card]
            # Guard has the best staying power; archers can hit from range.
            value = {'guard': 4.2, 'archer': 3.9, 'scout': 2.0}[action.card]
            value += 1.1 * min(2.0, own_pressure)
            value += 2.3 * min(3.0, enemy_pressure)
            if enemy:
                value += {'guard': 1.0, 'archer': 0.6, 'scout': -0.8}[action.card]
            # Prefer cheaper deployments when otherwise similar.
            value -= 0.15 * troop['cost']
            # Consistent deterministic tie-breaking by action iteration order.
            return value

        return max(actions, key=score)

    @staticmethod
    def _immediate_threat(battle, player):
        return any(u.owner != player and
                   (u.pos <= 4 if player == 0 else u.pos >= LENGTH - 4)
                   for u in battle.units)
