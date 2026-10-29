import pytest
from royalemind import Action, Battle
from royalemind.agents import RandomAgent


def test_elixir_regenerates_and_caps():
    b = Battle()
    b.step()
    assert b.elixir == [6, 6]
    for _ in range(10):
        b.step()
    assert b.elixir == [10, 10]


def test_deployment_and_cost():
    b = Battle()
    b.step((Action('guard', 1), None))
    assert b.elixir == [3, 6]
    assert len(b.units) == 1
    assert b.units[0].lane == 1


def test_invalid_action_is_atomic():
    b = Battle()
    with pytest.raises(ValueError):
        b.step((Action('scout', 0), Action('fake', 0)))
    assert b.time == 0 and b.units == [] and b.elixir == [5, 5]


def test_units_damage_tower():
    b = Battle(duration=100)
    b.step((Action('scout', 0), None))
    for _ in range(12):
        b.step()
    assert b.towers[1] < 1000


def test_simultaneous_combat():
    b = Battle(duration=100)
    b.step((Action('scout', 0), Action('scout', 0)))
    for _ in range(4):
        b.step()
    assert len(b.units) == 2
    assert all(unit.hp < 60 for unit in b.units)


def test_timeout_draw():
    b = Battle(duration=1)
    assert b.step()
    assert b.winner is None
    with pytest.raises(RuntimeError):
        b.step()


def test_seeded_reproducibility():
    def play():
        b = Battle(seed=99, duration=30)
        agents = (RandomAgent(), RandomAgent())
        while not b.done:
            b.step(tuple(a.choose(b, p) for p, a in enumerate(agents)))
        return b.towers, b.winner, b.observe(0)
    assert play() == play()


def test_observation_is_snapshot():
    b = Battle()
    obs = b.observe(0)
    b.step()
    assert obs['time'] == 0
