import pytest
from royalemind import Action, Battle
from royalemind.core import Unit
from royalemind.strategy import StrategyAgent
from royalemind.tournament import evaluate


def test_strategy_only_chooses_legal_actions():
    agent = StrategyAgent()
    for player in (0, 1):
        battle = Battle(seed=11)
        for _ in range(25):
            action = agent.choose(battle, player)
            assert action is None or action in battle.legal_actions(player)
            battle.step((action, None) if player == 0 else (None, action))


def test_strategy_waits_to_save_elixir_without_threat():
    battle = Battle()
    battle.elixir[0] = 2
    assert StrategyAgent().choose(battle, 0) is None


def test_strategy_defends_when_enemy_is_near_tower():
    battle = Battle()
    battle.elixir[0] = 3
    battle.units.append(Unit(1, 'scout', 1, 2, 60, 0))
    assert StrategyAgent().choose(battle, 0) == Action('guard', 1)


def test_strategy_deterministic_and_no_state_mutation():
    battle = Battle(seed=12)
    agent = StrategyAgent()
    before = battle.observe(0)
    assert agent.choose(battle, 0) == agent.choose(battle, 0)
    assert battle.observe(0) == before


def test_tournament_counts_and_reproducibility():
    first = evaluate(matches=12, seed=42, duration=30)
    assert first == evaluate(matches=12, seed=42, duration=30)
    assert sum(v['matches'] for v in first.values()) == 12
    for result in first.values():
        assert result['strategy'] + result['baseline'] + result['draws'] == result['matches']


@pytest.mark.parametrize('matches,duration', [(1, 180), (10, 0)])
def test_tournament_rejects_invalid_configuration(matches, duration):
    with pytest.raises(ValueError):
        evaluate(matches=matches, duration=duration)
