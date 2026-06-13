from pathlib import Path

from wcprediction.tournament import group_fixtures, load_tournament_config


def test_2026_config_has_48_unique_teams() -> None:
    config = load_tournament_config(Path("configs/tournaments/2026.yaml"))
    assert len(config.groups) == 12
    assert all(len(teams) == 4 for teams in config.groups.values())
    assert len(config.teams) == 48
    assert len(set(config.teams)) == 48


def test_group_fixture_count() -> None:
    assert len(group_fixtures(["A", "B", "C", "D"])) == 6


def test_2026_config_includes_context_inputs() -> None:
    config = load_tournament_config(Path("configs/tournaments/2026.yaml"))
    assert len(config.fixtures) == 72
    assert len(config.venues) == 16
    assert len(config.team_priors) == 48
    assert len(config.team_adjustments) == 48
    assert config.team_priors["Morocco"].rank == 8
    assert config.team_priors["Colombia"].rank == 13


def test_2026_config_loads_played_fixture_results() -> None:
    config = load_tournament_config(Path("configs/tournaments/2026.yaml"))
    opener = config.fixtures[0]
    second_match = config.fixtures[1]
    third_match = config.fixtures[2]

    assert opener.status == "played"
    assert (opener.home, opener.away) == ("Mexico", "South Africa")
    assert (opener.home_goals, opener.away_goals) == (2, 0)
    assert [scorer.player for scorer in opener.scorers or []] == ["Julián Quiñones", "Raúl Jiménez"]
    assert len(opener.discipline or []) == 3
    assert second_match.status == "played"
    assert (second_match.home_goals, second_match.away_goals) == (2, 1)
    assert third_match.status == "played"
    assert (third_match.home, third_match.away) == ("Canada", "Bosnia and Herzegovina")
    assert (third_match.home_goals, third_match.away_goals) == (1, 1)
    assert [scorer.player for scorer in third_match.scorers or []] == ["Jovo Lukic", "Cyle Larin"]
