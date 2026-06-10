from collections import Counter

import numpy as np

from wcprediction.simulate import _first_knockout_round, simulate_group


class DummyElo:
    home_advantage = 0

    def rating(self, team: str) -> float:
        return {"A": 1700, "B": 1600, "C": 1500, "D": 1400}.get(team, 1500)


class DummyEstimator:
    def predict_proba(self, features):
        return np.array([[0.45, 0.25, 0.30]])


class DummyModel:
    elo = DummyElo()
    estimator = DummyEstimator()

    def predict_match(self, home, away, neutral=True, tournament="FIFA World Cup"):
        return {"home_win": 0.45, "draw": 0.25, "away_win": 0.30}


def test_simulated_group_returns_ranked_table() -> None:
    ranked, table = simulate_group("X", ["A", "B", "C", "D"], DummyModel(), np.random.default_rng(7))
    assert len(ranked) == 4
    assert len(table) == 4
    assert Counter(row["team"] for row in table) == Counter(["A", "B", "C", "D"])


def test_first_knockout_round_has_32_teams() -> None:
    winners = [f"W{i}" for i in range(12)]
    runners = [f"R{i}" for i in range(12)]
    thirds = [f"T{i}" for i in range(8)]
    bracket = _first_knockout_round(winners, runners, thirds)
    assert len(bracket) == 32
    assert len(set(bracket)) == 32
