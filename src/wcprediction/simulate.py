from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from math import exp, lgamma, log
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

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


DEFAULT_SCORER_POOL_PATH = Path("data/player_scorer_pool_2026.yaml")

CARD_DEDUCTIONS = {
    "yellow": -1,
    "second_yellow": -3,
    "indirect_red": -3,
    "direct_red": -4,
    "yellow_direct_red": -5,
}

THIRD_PLACE_SLOTS = {
    "1A": {"match_number": 79, "allowed_groups": ["C", "E", "F", "H", "I"]},
    "1B": {"match_number": 85, "allowed_groups": ["E", "F", "G", "I", "J"]},
    "1D": {"match_number": 81, "allowed_groups": ["B", "E", "F", "I", "J"]},
    "1E": {"match_number": 74, "allowed_groups": ["A", "B", "C", "D", "F"]},
    "1G": {"match_number": 82, "allowed_groups": ["A", "E", "H", "I", "J"]},
    "1I": {"match_number": 77, "allowed_groups": ["C", "D", "F", "G", "H"]},
    "1K": {"match_number": 87, "allowed_groups": ["D", "E", "I", "J", "L"]},
    "1L": {"match_number": 80, "allowed_groups": ["E", "H", "I", "J", "K"]},
}

ROUND_OF_32_TEMPLATES = [
    {"match_number": 73, "date": "2026-06-28", "venue": "SoFi Stadium", "home": ("runner_up", "A"), "away": ("runner_up", "B")},
    {"match_number": 74, "date": "2026-06-29", "venue": "Gillette Stadium", "home": ("winner", "E"), "away": ("third", "1E")},
    {"match_number": 75, "date": "2026-06-29", "venue": "Estadio BBVA", "home": ("winner", "F"), "away": ("runner_up", "C")},
    {"match_number": 76, "date": "2026-06-29", "venue": "NRG Stadium", "home": ("winner", "C"), "away": ("runner_up", "F")},
    {"match_number": 77, "date": "2026-06-30", "venue": "MetLife Stadium", "home": ("winner", "I"), "away": ("third", "1I")},
    {"match_number": 78, "date": "2026-06-30", "venue": "AT&T Stadium", "home": ("runner_up", "E"), "away": ("runner_up", "I")},
    {"match_number": 79, "date": "2026-06-30", "venue": "Estadio Azteca", "home": ("winner", "A"), "away": ("third", "1A")},
    {"match_number": 80, "date": "2026-07-01", "venue": "Mercedes-Benz Stadium", "home": ("winner", "L"), "away": ("third", "1L")},
    {"match_number": 81, "date": "2026-07-01", "venue": "Levi's Stadium", "home": ("winner", "D"), "away": ("third", "1D")},
    {"match_number": 82, "date": "2026-07-01", "venue": "Lumen Field", "home": ("winner", "G"), "away": ("third", "1G")},
    {"match_number": 83, "date": "2026-07-02", "venue": "BMO Field", "home": ("runner_up", "K"), "away": ("runner_up", "L")},
    {"match_number": 84, "date": "2026-07-02", "venue": "SoFi Stadium", "home": ("winner", "H"), "away": ("runner_up", "J")},
    {"match_number": 85, "date": "2026-07-02", "venue": "BC Place", "home": ("winner", "B"), "away": ("third", "1B")},
    {"match_number": 86, "date": "2026-07-03", "venue": "Hard Rock Stadium", "home": ("winner", "J"), "away": ("runner_up", "H")},
    {"match_number": 87, "date": "2026-07-03", "venue": "Arrowhead Stadium", "home": ("winner", "K"), "away": ("third", "1K")},
    {"match_number": 88, "date": "2026-07-03", "venue": "AT&T Stadium", "home": ("runner_up", "D"), "away": ("runner_up", "G")},
]

KNOCKOUT_DEPENDENCY_TEMPLATES = [
    {"match_number": 89, "stage": "round_of_16", "date": "2026-07-04", "venue": "Lincoln Financial Field", "home": 74, "away": 77},
    {"match_number": 90, "stage": "round_of_16", "date": "2026-07-04", "venue": "NRG Stadium", "home": 73, "away": 75},
    {"match_number": 91, "stage": "round_of_16", "date": "2026-07-05", "venue": "MetLife Stadium", "home": 76, "away": 78},
    {"match_number": 92, "stage": "round_of_16", "date": "2026-07-05", "venue": "Estadio Azteca", "home": 79, "away": 80},
    {"match_number": 93, "stage": "round_of_16", "date": "2026-07-06", "venue": "AT&T Stadium", "home": 83, "away": 84},
    {"match_number": 94, "stage": "round_of_16", "date": "2026-07-06", "venue": "Lumen Field", "home": 81, "away": 82},
    {"match_number": 95, "stage": "round_of_16", "date": "2026-07-07", "venue": "Mercedes-Benz Stadium", "home": 86, "away": 88},
    {"match_number": 96, "stage": "round_of_16", "date": "2026-07-07", "venue": "BC Place", "home": 85, "away": 87},
    {"match_number": 97, "stage": "quarterfinal", "date": "2026-07-09", "venue": "Gillette Stadium", "home": 89, "away": 90},
    {"match_number": 98, "stage": "quarterfinal", "date": "2026-07-10", "venue": "SoFi Stadium", "home": 93, "away": 94},
    {"match_number": 99, "stage": "quarterfinal", "date": "2026-07-11", "venue": "Hard Rock Stadium", "home": 91, "away": 92},
    {"match_number": 100, "stage": "quarterfinal", "date": "2026-07-11", "venue": "Arrowhead Stadium", "home": 95, "away": 96},
    {"match_number": 101, "stage": "semifinal", "date": "2026-07-14", "venue": "AT&T Stadium", "home": 97, "away": 98},
    {"match_number": 102, "stage": "semifinal", "date": "2026-07-15", "venue": "Mercedes-Benz Stadium", "home": 99, "away": 100},
    {"match_number": 103, "stage": "third_place", "date": "2026-07-18", "venue": "Hard Rock Stadium", "home": ("loser", 101), "away": ("loser", 102)},
    {"match_number": 104, "stage": "final", "date": "2026-07-19", "venue": "MetLife Stadium", "home": 101, "away": 102},
]


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


def _recent_form_delta(model: TrainedModel, team: str) -> float:
    profile = (model.profiles or {}).get(canonical_team(team)) if hasattr(model, "profiles") else None
    if profile is None:
        return 0.0
    snapshot = profile.snapshot()
    return float(np.clip(snapshot["recent_gd"] * 4.0 + (snapshot["recent_points"] - 1.25) * 6.0, -24.0, 24.0))


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
    return prior_delta + _team_adjustment_delta(config, team) + _recent_form_delta(model, team)


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
        "recent_form_delta": _recent_form_delta(model, team),
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


def load_scorer_pool(path: Path | str = DEFAULT_SCORER_POOL_PATH) -> dict[str, Any]:
    pool_path = Path(path)
    if not pool_path.exists():
        return {"source_notes": [], "teams": {}}
    raw = yaml.safe_load(pool_path.read_text(encoding="utf-8")) or {}
    teams = {
        canonical_team(team): sorted(rows or [], key=lambda row: float(row.get("weight", 0.0)), reverse=True)
        for team, rows in raw.get("teams", {}).items()
    }
    return {"source_notes": list(raw.get("source_notes", [])), "teams": teams}


def _poisson_log_probability(goals: int, rate: float) -> float:
    return -rate + goals * log(max(rate, 1e-9)) - lgamma(goals + 1)


def _most_likely_score(home_rate: float, away_rate: float, max_goals: int = 6) -> tuple[int, int]:
    best_score = (0, 0)
    best_probability = float("-inf")
    for home_goals in range(max_goals + 1):
        for away_goals in range(max_goals + 1):
            probability = _poisson_log_probability(home_goals, home_rate) + _poisson_log_probability(away_goals, away_rate)
            if probability > best_probability:
                best_probability = probability
                best_score = (home_goals, away_goals)
    return best_score


def _card_deduction(card: str) -> int:
    return CARD_DEDUCTIONS.get(card.lower().replace("-", "_"), 0)


def _fixture_conduct_delta(fixture: Fixture, team: str) -> int:
    team = canonical_team(team)
    return sum(
        _card_deduction(card.card)
        for card in fixture.discipline or []
        if canonical_team(card.team) == team
    )


def _fixture_scorers(fixture: Fixture) -> list[dict[str, Any]]:
    return [
        {
            "team": scorer.team,
            "player": scorer.player,
            "minute": scorer.minute,
            **({"note": scorer.note} if scorer.note else {}),
        }
        for scorer in fixture.scorers or []
    ]


def _predicted_scorers(
    scorer_pool: dict[str, list[dict[str, Any]]],
    team: str,
    goals: int,
    side: str,
) -> list[dict[str, Any]]:
    if goals <= 0:
        return []
    team = canonical_team(team)
    candidates = scorer_pool.get(team) or [{"player": f"{team} scorer", "role": "team", "weight": 1.0}]
    minute_bases = [16, 38, 57, 73, 86] if side == "home" else [23, 44, 61, 78, 89]
    scorers = []
    for index in range(goals):
        candidate = candidates[index % len(candidates)]
        minute = minute_bases[index % len(minute_bases)] + (index // len(minute_bases)) * 2
        scorers.append(
            {
                "team": team,
                "player": str(candidate["player"]),
                "minute": min(minute, 120),
                "predicted": True,
            }
        )
    return scorers


def _deterministic_match_prediction(
    model: TrainedModel,
    home: str,
    away: str,
    fixture: Fixture,
    scorer_pool: dict[str, list[dict[str, Any]]],
    prior_ratings: dict[str, float],
    last_dates: dict[str, date],
    last_venues: dict[str, str],
    config: TournamentConfig,
    knockout: bool = False,
) -> dict[str, Any]:
    if fixture.status == "played" and fixture.home_goals is not None and fixture.away_goals is not None:
        result = MatchResult(fixture.home, fixture.away, fixture.home_goals, fixture.away_goals)
        return {
            "result": result,
            "scorers": _fixture_scorers(fixture),
            "winner": result.winner,
            "decided_by": "regulation",
            "status": "played",
        }

    home_context = _context_delta(config, model, home, fixture, prior_ratings, last_dates, last_venues)
    away_context = _context_delta(config, model, away, fixture, prior_ratings, last_dates, last_venues)
    home_delta = (
        home_context["prior_delta"]
        + home_context["availability_delta"]
        + home_context["recent_form_delta"]
        - home_context["travel_penalty"]
        + home_context["rest_delta"]
    )
    away_delta = (
        away_context["prior_delta"]
        + away_context["availability_delta"]
        + away_context["recent_form_delta"]
        - away_context["travel_penalty"]
        + away_context["rest_delta"]
    )
    home_rate, away_rate = _goal_rates(
        model,
        home,
        away,
        neutral=True,
        home_delta=home_delta,
        away_delta=away_delta,
        goal_multiplier=_environment_goal_multiplier(config, fixture),
    )
    home_goals, away_goals = _most_likely_score(home_rate, away_rate)
    decided_by = "regulation"
    winner: str | None = None
    if home_goals > away_goals:
        winner = home
    elif away_goals > home_goals:
        winner = away
    elif knockout:
        effective_home = _rating(model, home) + home_delta
        effective_away = _rating(model, away) + away_delta
        winner = home if effective_home >= effective_away else away
        if winner == home:
            home_goals += 1
        else:
            away_goals += 1
        decided_by = "extra_time"

    result = MatchResult(home, away, home_goals, away_goals)
    scorers = [
        *_predicted_scorers(scorer_pool, home, home_goals, "home"),
        *_predicted_scorers(scorer_pool, away, away_goals, "away"),
    ]
    return {
        "result": result,
        "scorers": sorted(scorers, key=lambda scorer: scorer["minute"]),
        "winner": winner,
        "decided_by": decided_by,
        "status": "predicted",
        "home_expected_goals": round(home_rate, 3),
        "away_expected_goals": round(away_rate, 3),
    }


def _match_record(
    match_number: int,
    stage: str,
    fixture: Fixture,
    prediction: dict[str, Any],
    group: str | None = None,
    source_slot: str | None = None,
) -> dict[str, Any]:
    result: MatchResult = prediction["result"]
    return {
        "matchNumber": match_number,
        "stage": stage,
        "group": group,
        "date": str(fixture.date),
        "venue": fixture.venue,
        "home": result.home,
        "away": result.away,
        "homeGoals": result.home_goals,
        "awayGoals": result.away_goals,
        "winner": prediction.get("winner"),
        "status": prediction["status"],
        "decidedBy": prediction.get("decided_by", "regulation"),
        "scorers": prediction.get("scorers", []),
        "sourceSlot": source_slot,
        **(
            {
                "expectedGoals": {
                    "home": prediction["home_expected_goals"],
                    "away": prediction["away_expected_goals"],
                }
            }
            if "home_expected_goals" in prediction
            else {}
        ),
    }


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
    shootout_strengths = model.shootout_strengths or {}
    home_shootout = shootout_strengths.get(canonical_team(home), 0.5)
    away_shootout = shootout_strengths.get(canonical_team(away), 0.5)
    home_penalty_strength = 0.72 * home_penalty_strength + 0.28 * (
        home_shootout / max(home_shootout + away_shootout, 1e-9)
    )
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
        team: {"team": team, "group": group_name, "points": 0, "gf": 0, "ga": 0, "gd": 0, "conduct_score": 0}
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
        if fixture.status == "played" and fixture.home_goals is not None and fixture.away_goals is not None:
            result = MatchResult(home, away, fixture.home_goals, fixture.away_goals)
        else:
            home_context = (
                _context_delta(config, model, home, fixture, prior_ratings, last_dates, last_venues)
                if config
                else {
                    "prior_delta": 0.0,
                    "availability_delta": 0.0,
                    "recent_form_delta": 0.0,
                    "travel_penalty": 0.0,
                    "rest_delta": 0.0,
                }
            )
            away_context = (
                _context_delta(config, model, away, fixture, prior_ratings, last_dates, last_venues)
                if config
                else {
                    "prior_delta": 0.0,
                    "availability_delta": 0.0,
                    "recent_form_delta": 0.0,
                    "travel_penalty": 0.0,
                    "rest_delta": 0.0,
                }
            )
            home_delta = (
                home_context["prior_delta"]
                + home_context["availability_delta"]
                + home_context["recent_form_delta"]
                - home_context["travel_penalty"]
                + home_context["rest_delta"]
            )
            away_delta = (
                away_context["prior_delta"]
                + away_context["availability_delta"]
                + away_context["recent_form_delta"]
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
        table[home]["conduct_score"] += _fixture_conduct_delta(fixture, home)
        table[away]["conduct_score"] += _fixture_conduct_delta(fixture, away)
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
        row["fifa_points_tiebreak"] = config.team_priors.get(row["team"]).points if config and row["team"] in config.team_priors else 0.0
        row["rating"] = _rating(model, row["team"]) + prior_delta + adjustment_delta + _recent_form_delta(model, row["team"])
        row["draw_lots"] = float(rng.random())

    standings = sorted(
        table.values(),
        key=lambda row: (row["points"], row["gd"], row["gf"], row["conduct_score"], row["fifa_points_tiebreak"], row["draw_lots"]),
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


def _ranking_context(config: TournamentConfig, model: TrainedModel, team: str, prior_ratings: dict[str, float]) -> dict[str, float]:
    prior = config.team_priors.get(team)
    prior_delta = 0.0
    if team in prior_ratings:
        prior_delta = 0.35 * (prior_ratings[team] - _rating(model, team))
    return {
        "rating": _rating(model, team) + prior_delta + _team_adjustment_delta(config, team) + _recent_form_delta(model, team),
        "fifa_points_tiebreak": prior.points if prior and prior.points is not None else 0.0,
    }


def _apply_result_to_table(table: dict[str, dict[str, Any]], fixture: Fixture, result: MatchResult) -> None:
    home = result.home
    away = result.away
    table[home]["gf"] += result.home_goals
    table[home]["ga"] += result.away_goals
    table[away]["gf"] += result.away_goals
    table[away]["ga"] += result.home_goals
    table[home]["conduct_score"] += _fixture_conduct_delta(fixture, home)
    table[away]["conduct_score"] += _fixture_conduct_delta(fixture, away)
    if result.home_goals > result.away_goals:
        table[home]["points"] += 3
    elif result.away_goals > result.home_goals:
        table[away]["points"] += 3
    else:
        table[home]["points"] += 1
        table[away]["points"] += 1


def _finalize_standings(
    table: dict[str, dict[str, Any]],
    config: TournamentConfig,
    model: TrainedModel,
    prior_ratings: dict[str, float],
) -> list[dict[str, Any]]:
    rows = []
    for row in table.values():
        context = _ranking_context(config, model, row["team"], prior_ratings)
        row["gd"] = row["gf"] - row["ga"]
        row["rating"] = context["rating"]
        row["fifa_points_tiebreak"] = context["fifa_points_tiebreak"]
        rows.append(row)
    standings = sorted(
        rows,
        key=lambda row: (
            row["points"],
            row["gd"],
            row["gf"],
            row["conduct_score"],
            row["fifa_points_tiebreak"],
            row["rating"],
        ),
        reverse=True,
    )
    for index, row in enumerate(standings, start=1):
        row["position"] = index
        row["qualified"] = index <= 2
        row["thirdCandidate"] = index == 3
    return standings


def _predict_group_for_bracket(
    group_name: str,
    teams: list[str],
    model: TrainedModel,
    config: TournamentConfig,
    scorer_pool: dict[str, list[dict[str, Any]]],
    prior_ratings: dict[str, float],
    last_dates: dict[str, date],
    last_venues: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    table = {
        team: {"team": team, "group": group_name, "points": 0, "gf": 0, "ga": 0, "gd": 0, "conduct_score": 0}
        for team in teams
    }
    match_records: list[dict[str, Any]] = []
    for fixture in config.fixtures_for_group(group_name):
        prediction = _deterministic_match_prediction(
            model,
            fixture.home,
            fixture.away,
            fixture,
            scorer_pool,
            prior_ratings,
            last_dates,
            last_venues,
            config,
        )
        result: MatchResult = prediction["result"]
        _apply_result_to_table(table, fixture, result)
        match_records.append(_match_record(fixture.match_number, "group", fixture, prediction, group=group_name))
        last_dates[result.home] = fixture.date
        last_dates[result.away] = fixture.date
        last_venues[result.home] = fixture.venue
        last_venues[result.away] = fixture.venue
    return _finalize_standings(table, config, model, prior_ratings), match_records


def _third_place_slot_assignment(third_groups: list[str]) -> dict[str, str]:
    groups = sorted(third_groups)
    if len(groups) != 8:
        raise ValueError("exactly eight third-place groups are required")

    def backtrack(remaining_slots: list[str], remaining_groups: set[str], assigned: dict[str, str]) -> dict[str, str] | None:
        if not remaining_slots:
            return dict(assigned)
        slot = min(
            remaining_slots,
            key=lambda candidate: (
                len(set(THIRD_PLACE_SLOTS[candidate]["allowed_groups"]) & remaining_groups),
                candidate,
            ),
        )
        candidates = sorted(set(THIRD_PLACE_SLOTS[slot]["allowed_groups"]) & remaining_groups)
        for group in candidates:
            next_slots = [candidate for candidate in remaining_slots if candidate != slot]
            assigned[slot] = group
            result = backtrack(next_slots, remaining_groups - {group}, assigned)
            if result is not None:
                return result
            assigned.pop(slot, None)
        return None

    assignment = backtrack(list(THIRD_PLACE_SLOTS), set(groups), {})
    if assignment is None:
        raise ValueError(f"could not assign third-place groups to Round-of-32 slots: {groups}")
    return assignment


def _team_from_round_of_32_ref(
    ref: tuple[str, str],
    group_rows: dict[str, list[dict[str, Any]]],
    third_rows_by_group: dict[str, dict[str, Any]],
    third_slot_assignment: dict[str, str],
) -> tuple[str, str | None]:
    ref_type, value = ref
    if ref_type == "winner":
        return group_rows[value][0]["team"], None
    if ref_type == "runner_up":
        return group_rows[value][1]["team"], None
    if ref_type == "third":
        group = third_slot_assignment[value]
        return third_rows_by_group[group]["team"], f"3{group}"
    raise ValueError(f"unknown Round-of-32 ref: {ref}")


def _knockout_fixture(template: dict[str, Any], home: str, away: str) -> Fixture:
    return Fixture(
        match_number=int(template["match_number"]),
        group="KO",
        date=date.fromisoformat(str(template["date"])),
        kickoff_et="",
        kickoff_local="",
        home=home,
        away=away,
        venue=str(template["venue"]),
    )


def _loser_for_match(record: dict[str, Any]) -> str:
    return record["away"] if record["winner"] == record["home"] else record["home"]


def build_bracket_challenge(
    config: TournamentConfig,
    model: TrainedModel,
    scorer_pool_path: Path | str = DEFAULT_SCORER_POOL_PATH,
    as_of_date: str = "2026-06-11",
) -> dict[str, Any]:
    scorer_data = load_scorer_pool(scorer_pool_path)
    scorer_pool = scorer_data["teams"]
    prior_ratings = _prior_rating_map(config, model)
    last_dates: dict[str, date] = {}
    last_venues: dict[str, str] = {}
    group_rows: dict[str, list[dict[str, Any]]] = {}
    group_matches: list[dict[str, Any]] = []

    for group_name, teams in config.groups.items():
        standings, matches = _predict_group_for_bracket(
            group_name,
            teams,
            model,
            config,
            scorer_pool,
            prior_ratings,
            last_dates,
            last_venues,
        )
        group_rows[group_name] = standings
        group_matches.extend(matches)

    third_rows = [rows[2] for rows in group_rows.values()]
    third_rows = sorted(
        third_rows,
        key=lambda row: (
            row["points"],
            row["gd"],
            row["gf"],
            row["conduct_score"],
            row["fifa_points_tiebreak"],
            row["rating"],
        ),
        reverse=True,
    )
    for index, row in enumerate(third_rows, start=1):
        row["thirdRank"] = index
        row["qualified"] = index <= 8
    best_third_rows = third_rows[:8]
    third_rows_by_group = {row["group"]: row for row in best_third_rows}
    third_slot_assignment = _third_place_slot_assignment([row["group"] for row in best_third_rows])

    knockout_records: list[dict[str, Any]] = []
    winners: dict[int, str] = {}
    losers: dict[int, str] = {}
    third_assignments = []

    for template in ROUND_OF_32_TEMPLATES:
        home, home_slot = _team_from_round_of_32_ref(template["home"], group_rows, third_rows_by_group, third_slot_assignment)
        away, away_slot = _team_from_round_of_32_ref(template["away"], group_rows, third_rows_by_group, third_slot_assignment)
        source_slot = home_slot or away_slot
        fixture = _knockout_fixture(template | {"stage": "round_of_32"}, home, away)
        prediction = _deterministic_match_prediction(
            model,
            home,
            away,
            fixture,
            scorer_pool,
            prior_ratings,
            last_dates,
            last_venues,
            config,
            knockout=True,
        )
        record = _match_record(fixture.match_number, "round_of_32", fixture, prediction, source_slot=source_slot)
        knockout_records.append(record)
        winners[fixture.match_number] = record["winner"]
        losers[fixture.match_number] = _loser_for_match(record)
        last_dates[home] = fixture.date
        last_dates[away] = fixture.date
        last_venues[home] = fixture.venue
        last_venues[away] = fixture.venue
        if source_slot:
            slot = next(key for key, group in third_slot_assignment.items() if f"3{group}" == source_slot)
            third_assignments.append(
                {
                    "slot": slot,
                    "matchNumber": fixture.match_number,
                    "thirdGroup": source_slot,
                    "team": away if away_slot else home,
                }
            )

    for template in KNOCKOUT_DEPENDENCY_TEMPLATES:
        home_ref = template["home"]
        away_ref = template["away"]
        home = losers[home_ref[1]] if isinstance(home_ref, tuple) and home_ref[0] == "loser" else winners[int(home_ref)]
        away = losers[away_ref[1]] if isinstance(away_ref, tuple) and away_ref[0] == "loser" else winners[int(away_ref)]
        fixture = _knockout_fixture(template, home, away)
        prediction = _deterministic_match_prediction(
            model,
            home,
            away,
            fixture,
            scorer_pool,
            prior_ratings,
            last_dates,
            last_venues,
            config,
            knockout=True,
        )
        record = _match_record(fixture.match_number, template["stage"], fixture, prediction)
        knockout_records.append(record)
        winners[fixture.match_number] = record["winner"]
        losers[fixture.match_number] = _loser_for_match(record)
        last_dates[home] = fixture.date
        last_dates[away] = fixture.date
        last_venues[home] = fixture.venue
        last_venues[away] = fixture.venue

    knockout_by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in knockout_records:
        knockout_by_stage[record["stage"]].append(record)

    group_picks = [
        {
            "group": group,
            "winner": rows[0]["team"],
            "runnerUp": rows[1]["team"],
            "third": rows[2]["team"],
            "standings": rows,
        }
        for group, rows in group_rows.items()
    ]
    all_matches = sorted(group_matches + knockout_records, key=lambda row: row["matchNumber"])
    return {
        "asOfDate": as_of_date,
        "mode": "most_likely_path",
        "format": "Top two in each group plus eight best third-place teams; deterministic knockout scores.",
        "groupPicks": group_picks,
        "bestThirds": best_third_rows,
        "thirdPlaceRanking": third_rows,
        "thirdPlaceAssignments": sorted(third_assignments, key=lambda row: row["matchNumber"]),
        "matches": all_matches,
        "knockoutBracket": {stage: rows for stage, rows in knockout_by_stage.items()},
        "playedResults": [match for match in all_matches if match["status"] == "played"],
        "champion": winners[104],
        "runnerUp": losers[104],
        "thirdPlace": winners[103],
        "sourceNotes": [
            "Match 1 and Match 2 are locked as played results from 2026-06-11.",
            "Round-of-32 slots use FIFA's official group-winner/runner-up slots and third-place slot eligibility from the FIFA World Cup 26 regulations.",
            "Knockout scorelines are deterministic most-likely model scorelines; tied knockout scorelines are resolved in extra time for a bracket winner.",
        ],
        "scorerModelNotes": scorer_data["source_notes"],
    }


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
    scorer_pool_path: Path | str = DEFAULT_SCORER_POOL_PATH,
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
    team_context: dict[str, dict[str, float | int | None]] = {}
    for team in all_teams:
        prior = config.team_priors.get(team)
        prior_delta = 0.0
        if team in prior_ratings:
            prior_delta = 0.35 * (prior_ratings[team] - _rating(model, team))
        profile = (model.profiles or {}).get(team)
        profile_snapshot = profile.snapshot() if profile else {}
        team_context[team] = {
            "eloRating": round(_rating(model, team), 2),
            "fifaRank": prior.rank if prior else None,
            "fifaPoints": prior.points if prior else None,
            "priorDelta": round(prior_delta, 2),
            "availabilityDelta": round(_team_adjustment_delta(config, team), 2),
            "recentFormDelta": round(_recent_form_delta(model, team), 2),
            "recentPoints": round(float(profile_snapshot.get("recent_points", 0.0)), 3),
            "recentGoalDifference": round(float(profile_snapshot.get("recent_gd", 0.0)), 3),
            "penaltyStrength": round(float((model.shootout_strengths or {}).get(team, 0.5)), 3),
        }
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
            "uses_recent_form": bool(getattr(model, "profiles", None)),
            "uses_shootout_history": bool(getattr(model, "shootout_strengths", None)),
        },
        "tiebreak_notes": [
            "Group standings sort by points, goal difference, goals for, conduct score, FIFA ranking-points prior, then seeded drawing lots.",
            "Knockout penalty decisions blend match-model strength with historical shootout success where available.",
        ],
        "team_context": team_context,
        "bracket_challenge": build_bracket_challenge(config, model, scorer_pool_path=scorer_pool_path),
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
