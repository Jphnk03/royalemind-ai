import json
import pytest
from royalemind import Action, Battle
from royalemind.learning import QAgent, action_id, encode_state, evaluate, load_model, save_model, train

def test_actions_legal_and_pass_without_elixir():
    battle = Battle()
    battle.elixir[0] = 0
    assert QAgent(seed=4).choose(battle, 0) is None
    battle.elixir[0] = 10
    assert QAgent(seed=4).choose(battle, 0) in [None] + battle.legal_actions(0)

def test_action_encoding_and_relative_state():
    battle = Battle()
    assert action_id(None) == 0
    assert action_id(Action('archer', 1)) == 6
    assert len(encode_state(battle, 0)) == 12
    assert encode_state(battle, 0) == encode_state(battle, 1)

def test_training_reproducible():
    assert train(episodes=8, seed=9, duration=15) == train(episodes=8, seed=9, duration=15)

def test_model_roundtrip(tmp_path):
    table = train(episodes=8, duration=15)
    path = tmp_path / 'model.json'
    save_model(table, path)
    assert load_model(path) == table
    assert json.loads(path.read_text())['format'] == 'royalemind-tabular-q-v2'

def test_invalid_model_rejected(tmp_path):
    path = tmp_path / 'bad.json'
    path.write_text('{"format":"unknown"}')
    with pytest.raises(ValueError):
        load_model(path)

def test_evaluation_counts_and_reproducibility():
    table = train(episodes=5, duration=12)
    first = evaluate(table, matches=10, seed=900, duration=12)
    assert first == evaluate(table, matches=10, seed=900, duration=12)
    assert sum(first.values()) == 10

def test_invalid_configuration():
    with pytest.raises(ValueError):
        train(episodes=0)
    with pytest.raises(ValueError):
        evaluate({}, matches=0)
    with pytest.raises(ValueError):
        QAgent(epsilon=1.1)

def test_unseen_state_uses_strategy_teacher():
    from royalemind.strategy import StrategyAgent
    battle = Battle(seed=12)
    assert QAgent({}).choose(battle, 0) == StrategyAgent().choose(battle, 0)

def test_state_tracks_enemy_advance():
    from royalemind.core import Unit
    battle = Battle()
    initial = encode_state(battle, 0)
    battle.units.append(Unit(1, 'scout', 0, 10, 60, 0))
    assert encode_state(battle, 0) != initial

def test_old_model_version_rejected(tmp_path):
    path = tmp_path / 'old.json'
    path.write_text(json.dumps({'format': 'royalemind-tabular-q-v1', 'actions': 7, 'q': []}))
    with pytest.raises(ValueError):
        load_model(path)
