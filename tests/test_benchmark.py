import pytest
from royalemind.benchmark import benchmark, compare
from royalemind.learning import train
from royalemind.strategy import StrategyAgent


def test_paired_side_counts_and_reproducibility():
    a = compare(StrategyAgent, StrategyAgent, matches=10, seed=17, duration=25)
    assert a == compare(StrategyAgent, StrategyAgent, matches=10, seed=17, duration=25)
    assert sum(a[key] for key in ('learned', 'opponent', 'draws')) == 10
    for side in (0, 1):
        assert sum(a['by_side'][side].values()) == 5


def test_benchmark_has_three_opponents_and_self_play():
    results = benchmark(train(episodes=3, duration=10), matches=4, seeds=(10,), duration=10)
    assert set(results) == {'strategy', 'random', 'rush', 'strategy_self_play'}
    assert all(sum(run[0][k] for k in ('learned', 'opponent', 'draws')) == 4
               for run in results.values())


@pytest.mark.parametrize('matches,duration', [(1, 180), (3, 180), (4, 0)])
def test_compare_rejects_bad_configuration(matches, duration):
    with pytest.raises(ValueError):
        compare(StrategyAgent, StrategyAgent, matches=matches, duration=duration)
