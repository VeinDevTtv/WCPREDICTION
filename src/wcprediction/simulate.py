from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from math import exp, log
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .model import TrainedModel
from .teams import canonical_team
from .tournament import Fixture, TournamentConfig, group_fixtures, load_tournament_config


@dataclass
class MatchResult:
    home: str
    away: str
    home_goals: int
    away_goals: int

    @property
    def winner(self) -> str | None:
        if self.home_goals > self.away_goals:
            return self.home
        if self.away_goals > self.home_goals:
            return self.away
        return None


def _rating(model: TrainedModel, team: str) -> float:
    return model.elo.rating(canonical_team(team))


def _distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_miles = 3958.8
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    haversine = (
        np.sin(delta_phi / 2.0) ** 2
        + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    )
    return float(2 * radius_miles * np.arcsin(np.sqrt(haversine)))


def _venue_travel(config: TournamentConfig, previous_venue: str | None, current_venue: str) -> float:
    if previous_venue is None or previous_venue == current_venue:
        return 0.0
    previous = config.venues.get(previous_venue)
    current = config.venues.get(current_venue)
    if previous is None or current is None:
        return 0.0
    return _distance_miles(previous.latitude, previous.longitude, current.latitude, current.longitude)


def _rest_days(previous_date: date | None, current_date: date) -> float:
    if previous_date is None:
        return 6.0
    return float((current_date - previous_date).days)


def _rank_implied_points(rank: int) -> float:
    return float(np.clip(1880.0 - 6.8 * (rank - 1), 1250.0, 1900.0))


def _prior_rating_map(config: TournamentConfig, model: TrainedModel) -> dict[str, float]:
    priors = {
        team: prior.points if prior.points is not None else _rank_implied_points(prior.rank)
        for team, prior in config.team_priors.items()
    }
    if len(priors) < 2:
        return {}
    teams = [team for team in config.teams if team in priors]
    prior_values = np.asarray([priors[team] for team in teams], dtype=float)
    elo_values = np.asarray([_rating(model, team) for team in teams], dtype=float)
    prior_std = float(prior_values.std())
    elo_std = float(elo_values.std())
    if prior_std == 0.0 or elo_std == 0.0:
        return {}
    normalized = (prior_values - float(prior_values.mean())) / prior_std
    scaled = float(elo_values.mean()) + normalized * elo_std
    return {team: float(value) for team, value in zip(teams, scaled)}


def _team_adjustment_delta(config: TournamentConfig, team: str) -> float:
    adjustment = config.team_adjustments.get(canonical_team(team))
    if adjustment is None:
        return 0.0
    return (
        adjustment.squad_strength_delta
        - adjustment.injury_penalty
        - adjustment.suspension_penalty
        - adjustment.recent_minutes_penalty
    )


def _static_rating_delta(
    config: TournamentConfig,
    model: TrainedModel,
    team: str,
    prior_ratings: dict[str, float],
) -> float:
    team = canonical_team(team)
    prior_delta = 0.0
    if team in prior_ratings:
        prior_delta = 0.35 * (prior_ratings[team] - _rating(model, team))
    return prior_delta + _team_adjustment_delta(config, team)


def _context_delta(
    config: TournamentConfig,
    model: TrainedModel,
    team: str,
    fixture: Fixture | None,
    prior_ratings: dict[str, float],
    last_dates: dict[str, date],
    last_venues: dict[str, str],
) -> dict[str, float]:
    team = canonical_team(team)
    base_rating = _rating(model, team)
    prior_delta = 0.0
    if team in prior_ratings:
        prior_delta = 0.35 * (prior_ratings[team] - base_rating)

    travel_penalty = 0.0
    rest_delta = 0.0
    travel_miles = 0.0
    rest = 6.0
    if fixture is not None:
        travel_miles = _venue_travel(config, last_venues.get(team), fixture.venue)
        rest = _rest_days(last_dates.get(team), fixture.date)
        travel_penalty = max(0.0, travel_miles - 500.0) * 0.006
        if rest < 4.0:
            rest_delta = -12.0 * (4.0 - rest)
        elif rest > 6.0:
            rest_delta = min(8.0, 2.0 * (rest - 6.0))

    return {
        "prior_delta": prior_delta,
        "availability_delta": _team_adjustment_delta(config, team),
        "travel_penalty": travel_penalty,
        "rest_delta": rest_delta,
        "travel_miles": travel_miles,
        "rest_days": rest,
    }


def _environment_goal_multiplier(config: TournamentConfig, fixture: Fixture | None) -> float:
    if fixture is None:
        return 1.0
    venue = config.venues.get(fixture.venue)
    if venue is None or venue.roof in {"fixed", "retractable_climate_controlled"}:
        return 1.0
    multiplier = 1.0
    if venue.avg_temp_c is not None and venue.avg_temp_c > 27.0:
        multiplier -= min(0.08, (venue.avg_temp_c - 27.0) * 0.012)
    if venue.avg_humidity_pct is not None and venue.avg_humidity_pct > 65.0:
        multiplier -= min(0.05, (venue.avg_humidity_pct - 65.0) * 0.002)
    if venue.altitude_m > 1200.0:
        multiplier -= min(0.06, (venue.altitude_m - 1200.0) / 10000.0)
    return float(np.clip(multiplier, 0.82, 1.05))


def _goal_rates(
    model: TrainedModel,
    home: str,
    away: str,
    neutral: bool,
    home_delta: float = 0.0,
    away_delta: float = 0.0,
    goal_multiplier: float = 1.0,
) -> tuple[float, float]:
    diff = (_rating(model, home) + home_delta) - (_rating(model, away) + away_delta)
    home_adv = 0.0 if neutral else model.elo.home_advantage
    base = log(1.28)
    home_rate = goal_multiplier * exp(base + 0.0018 * (diff + home_adv))
    away_rate = goal_multiplier * exp(base - 0.0018 * (diff + home_adv))
    return float(np.clip(home_rate, 0.15, 4.5)), float(np.clip(away_rate, 0.15, 4.5))


def simulate_score(
    model: TrainedModel,
    home: str,
    away: str,
    rng: np.random.Generator,
    neutral: bool = True,
    home_delta: float = 0.0,
    away_delta: float = 0.0,
    goal_multiplier: float = 1.0,
) -> MatchResult:
    home_rate, away_rate = _goal_rates(
        model,
        home,
        away,
        neutral,
        home_delta=home_delta,
        away_delta=away_delta,
        goal_multiplier=goal_multiplier,
    )
    return MatchResult(home, away, int(rng.poisson(home_rate)), int(rng.poisson(away_rate)))


def simulate_knockout_match(
    model: TrainedModel,
    home: str,
    away: str,
    rng: np.random.Generator,
    config: TournamentConfig | None = None,
    prior_ratings: dict[str, float] | None = None,
) -> str:
    prior_ratings = prior_ratings or {}
    home_delta = _static_rating_delta(config, model, home, prior_ratings) if config else 0.0
    away_delta = _static_rating_delta(config, model, away, prior_ratings) if config else 0.0
    result = simulate_score(model, home, away, rng, neutral=True, home_delta=home_delta, away_delta=away_delta)
    if result.winner:
        return result.winner

    home_rate, away_rate = _goal_rates(
        model,
        home,
        away,
        neutral=True,
        home_delta=home_delta,
        away_delta=away_delta,
    )
    extra_home = int(rng.poisson(home_rate * (30.0 / 90.0)))
    extra_away = int(rng.poisson(away_rate * (30.0 / 90.0)))
    if extra_home > extra_away:
        return home
    if extra_away > extra_home:
        return away

    probs = model.predict_match(home, away, neutral=True)
    home_penalty_strength = probs["home_win"] + 0.5 * probs["draw"]
    return home if rng.random() < home_penalty_strength else away


def simulate_group(
    group_name: str,
    teams: list[str],
    model: TrainedModel,
    rng: np.random.Generator,
    config: TournamentConfig | None = None,
    prior_ratings: dict[str, float] | None = None,
) -> tuple[list[str], list[dict[str, Any]]]:
    table = {
        team: {"team": team, "group": group_name, "points": 0, "gf": 0, "ga": 0, "gd": 0}
        for team in teams
    }
    fixtures = config.fixtures_for_group(group_name) if config and config.fixtures else []
    if not fixtures:
        fixtures = [
            Fixture(index + 1, group_name, date(2026, 1, 1), "", "", home, away, "")
            for index, (home, away) in enumerate(group_fixtures(teams))
        ]
    prior_ratings = prior_ratings or {}
    last_dates: dict[str, date] = {}
    last_venues: dict[str, str] = {}

    for fixture in fixtures:
        home = fixture.home
        away = fixture.away
        if home not in table or away not in table:
            continue
        home_context = (
            _context_delta(config, model, home, fixture, prior_ratings, last_dates, last_venues)
            if config
            else {"prior_delta": 0.0, "availability_delta": 0.0, "travel_penalty": 0.0, "rest_delta": 0.0}
        )
        away_context = (
            _context_delta(config, model, away, fixture, prior_ratings, last_dates, last_venues)
            if config
            else {"prior_delta": 0.0, "availability_delta": 0.0, "travel_penalty": 0.0, "rest_delta": 0.0}
        )
        home_delta = (
            home_context["prior_delta"]
            + home_context["availability_delta"]
            - home_context["travel_penalty"]
            + home_context["rest_delta"]
        )
        away_delta = (
            away_context["prior_delta"]
            + away_context["availability_delta"]
            - away_context["travel_penalty"]
            + away_context["rest_delta"]
        )
        result = simulate_score(
            model,
            home,
            away,
            rng,
            neutral=True,
            home_delta=home_delta,
            away_delta=away_delta,
            goal_multiplier=_environment_goal_multiplier(config, fixture) if config else 1.0,
        )
        table[home]["gf"] += result.home_goals
        table[home]["ga"] += result.away_goals
        table[away]["gf"] += result.away_goals
        table[away]["ga"] += result.home_goals
        if result.home_goals > result.away_goals:
            table[home]["points"] += 3
        elif result.away_goals > result.home_goals:
            table[away]["points"] += 3
        else:
            table[home]["points"] += 1
            table[away]["points"] += 1
        last_dates[home] = fixture.date
        last_dates[away] = fixture.date
        last_venues[home] = fixture.venue
        last_venues[away] = fixture.venue

    for row in table.values():
        row["gd"] = row["gf"] - row["ga"]
        prior_delta = 0.0
        if row["team"] in prior_ratings:
            prior_delta = 0.35 * (prior_ratings[row["team"]] - _rating(model, row["team"]))
        adjustment_delta = _team_adjustment_delta(config, row["team"]) if config else 0.0
        row["rating"] = _rating(model, row["team"]) + prior_delta + adjustment_delta
        row["draw_lots"] = float(rng.random())

    standings = sorted(
        table.values(),
        key=lambda row: (row["points"], row["gd"], row["gf"], row["rating"], row["draw_lots"]),
        reverse=True,
    )
    return [row["team"] for row in standings], standings


def _first_knockout_round(group_winners: list[str], runners_up: list[str], thirds: list[str]) -> list[str]:
    """Create a balanced deterministic 32-team order for the first knockout round.

    FIFA's exact third-place matchup table depends on which groups supply third-place
    qualifiers. This order preserves the 48-team rule shape without pretending the
    config has a fully official dynamic bracket table.
    """
    seeded = group_winners + runners_up[:4]
    unseeded = list(reversed(thirds)) + list(reversed(runners_up[4:]))
    order: list[str] = []
    for seed, opponent in zip(seeded, unseeded):
        order.extend([seed, opponent])
    return order


def simulate_once(config: TournamentConfig, model: TrainedModel, rng: np.random.Generator) -> dict[str, Any]:
    group_winners: list[str] = []
    runners_up: list[str] = []
    third_rows: list[dict[str, Any]] = []
    standings: dict[str, list[dict[str, Any]]] = {}

    prior_ratings = _prior_rating_map(config, model)

    for group_name, teams in config.groups.items():
        ranked, table = simulate_group(group_name, teams, model, rng, config=config, prior_ratings=prior_ratings)
        standings[group_name] = table
        group_winners.append(ranked[0])
        runners_up.append(ranked[1])
        third_rows.append(table[2])

    third_rows = sorted(
        third_rows,
        key=lambda row: (row["points"], row["gd"], row["gf"], row["rating"], row["draw_lots"]),
        reverse=True,
    )
    best_thirds = [row["team"] for row in third_rows[:8]]
    round_teams = _first_knockout_round(group_winners, runners_up, best_thirds)

    reached = {
        "round_of_32": set(round_teams),
        "quarterfinal": set(),
        "semifinal": set(),
        "final": set(),
        "champion": set(),
    }
    while len(round_teams) > 1:
        winners: list[str] = []
        for home, away in zip(round_teams[::2], round_teams[1::2]):
            winners.append(
                simulate_knockout_match(model, home, away, rng, config=config, prior_ratings=prior_ratings)
            )
        if len(winners) == 8:
            reached["quarterfinal"].update(winners)
        elif len(winners) == 4:
            reached["semifinal"].update(winners)
        elif len(winners) == 2:
            reached["final"].update(winners)
        elif len(winners) == 1:
            reached["champion"].add(winners[0])
        round_teams = winners

    return {"standings": standings, "best_thirds": best_thirds, "reached": reached}


def simulate_tournament(
    model: TrainedModel,
    config_path: Path | str,
    runs: int = 10000,
    seed: int = 42,
) -> dict[str, Any]:
    config = load_tournament_config(config_path)
    rng = np.random.default_rng(seed)
    prior_ratings = _prior_rating_map(config, model)
    stage_counts: dict[str, Counter[str]] = defaultdict(Counter)
    group_advance_counts: Counter[str] = Counter()

    for _ in range(runs):
        result = simulate_once(config, model, rng)
        for team in result["reached"]["round_of_32"]:
            group_advance_counts[team] += 1
        for stage, teams in result["reached"].items():
            for team in teams:
                stage_counts[stage][team] += 1

    all_teams = sorted(config.teams)
    stage_probabilities = {
        stage: {team: stage_counts[stage][team] / runs for team in all_teams}
        for stage in ["round_of_32", "quarterfinal", "semifinal", "final", "champion"]
    }
    group_probabilities = {team: group_advance_counts[team] / runs for team in all_teams}
    champion_table = sorted(
        [{"team": team, "probability": probability} for team, probability in stage_probabilities["champion"].items()],
        key=lambda row: row["probability"],
        reverse=True,
    )
    return {
        "tournament": config.name,
        "year": config.year,
        "runs": runs,
        "seed": seed,
        "source_notes": config.source_notes,
        "context_features": {
            "fifa_prior_teams": len(prior_ratings),
            "fixture_count": len(config.fixtures),
            "venue_count": len(config.venues),
            "team_adjustment_count": len(config.team_adjustments),
            "uses_travel_distance": bool(config.fixtures and config.venues),
            "uses_rest_days": bool(config.fixtures),
            "uses_venue_climate": bool(config.fixtures and config.venues),
        },
        "champion_probabilities": champion_table,
        "stage_probabilities": stage_probabilities,
        "group_advancement_probabilities": group_probabilities,
    }


def write_csv_summaries(report: dict[str, Any], csv_dir: Path | str) -> None:
    target = Path(csv_dir)
    target.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(report["champion_probabilities"]).to_csv(target / "champion_probabilities.csv", index=False)
    stage_rows = []
    for stage, probabilities in report["stage_probabilities"].items():
        for team, probability in probabilities.items():
            stage_rows.append({"stage": stage, "team": team, "probability": probability})
    pd.DataFrame(stage_rows).to_csv(target / "stage_probabilities.csv", index=False)
