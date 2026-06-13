from collections import Counter
from pathlib import Path

import numpy as np

from wcprediction.simulate import _first_knockout_round, build_bracket_challenge, load_scorer_pool, load_squad_snapshot, simulate_group
from wcprediction.tournament import load_tournament_config


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
    profiles = {}
    shootout_strengths = {}

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


def test_bracket_challenge_locks_played_fixtures() -> None:
    config = load_tournament_config(Path("configs/tournaments/2026.yaml"))
    bracket = build_bracket_challenge(config, DummyModel())
    match_one = next(match for match in bracket["matches"] if match["matchNumber"] == 1)
    match_two = next(match for match in bracket["matches"] if match["matchNumber"] == 2)
    match_three = next(match for match in bracket["matches"] if match["matchNumber"] == 3)

    assert match_one["status"] == "played"
    assert (match_one["homeGoals"], match_one["awayGoals"]) == (2, 0)
    assert [scorer["player"] for scorer in match_one["scorers"]] == ["Julián Quiñones", "Raúl Jiménez"]
    assert match_two["status"] == "played"
    assert (match_two["homeGoals"], match_two["awayGoals"]) == (2, 1)
    assert match_three["status"] == "played"
    assert (match_three["homeGoals"], match_three["awayGoals"]) == (1, 1)
    assert [scorer["player"] for scorer in match_three["scorers"]] == ["Jovo Lukic", "Cyle Larin"]


def test_bracket_challenge_outputs_full_unique_knockout_card() -> None:
    config = load_tournament_config(Path("configs/tournaments/2026.yaml"))
    bracket = build_bracket_challenge(config, DummyModel())
    round_of_32 = bracket["knockoutBracket"]["round_of_32"]
    teams = {team for match in round_of_32 for team in [match["home"], match["away"]]}

    assert len(bracket["matches"]) == 104
    assert len(bracket["bestThirds"]) == 8
    assert len(round_of_32) == 16
    assert len(teams) == 32
    assert bracket["champion"]
    assert bracket["runnerUp"]
    assert bracket["thirdPlace"]
    assert bracket["squadSource"]["teamCount"] == 48
    assert bracket["squads"]


def test_bracket_challenge_scorer_counts_match_goals() -> None:
    config = load_tournament_config(Path("configs/tournaments/2026.yaml"))
    bracket = build_bracket_challenge(config, DummyModel())

    for match in bracket["matches"]:
        scorers = Counter(scorer["team"] for scorer in match["scorers"])
        assert scorers[match["home"]] == match["homeGoals"]
        assert scorers[match["away"]] == match["awayGoals"]


def test_official_squad_snapshot_and_scorer_pool_align() -> None:
    snapshot = load_squad_snapshot(Path("data/squads_2026.yaml"))
    pool = load_scorer_pool(Path("data/player_scorer_pool_2026.yaml"))
    squad_numbers = {
        team["team"]: {player["number"] for player in team["players"]}
        for team in snapshot["teams"]
    }

    assert snapshot["teamCount"] == 48
    assert len(snapshot["teams"]) == 48
    assert all(len(team["players"]) == 26 for team in snapshot["teams"])
    assert set(pool["teams"]) == set(squad_numbers)
    for team, rows in pool["teams"].items():
        assert 5 <= len(rows) <= 8
        for row in rows:
            assert row["number"] in squad_numbers[team]
