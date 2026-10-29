"""Baseline agents; replace with learned policies later."""

class RandomAgent:
    def choose(self, battle, player):
        actions = battle.legal_actions(player)
        if not actions or battle.rng.random() < 0.25:
            return None
        return battle.rng.choice(actions)


class RushAgent:
    def choose(self, battle, player):
        actions = battle.legal_actions(player)
        if not actions:
            return None
        # Favor faster troops in lane zero, then cheaper cards.
        return min(actions, key=lambda a: (a.lane, a.card != 'scout',
                                           a.card != 'guard'))
