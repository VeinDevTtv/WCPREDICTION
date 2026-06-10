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
