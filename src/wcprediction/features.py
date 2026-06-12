from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import log1p

import pandas as pd

from .elo import EloSystem, tournament_weight
from .teams import canonical_team

FEATURE_COLUMNS = [
    "elo_diff",
    "home_rating",
    "away_rating",
    "neutral",
    "home_advantage",
    "importance",
    "home_recent_points",
    "away_recent_points",
    "recent_points_diff",
    "home_recent_gd",
    "away_recent_gd",
    "recent_gd_diff",
    "home_recent_goals_for",
    "away_recent_goals_for",
    "home_recent_goals_against",
    "away_recent_goals_against",
    "home_match_volume",
    "away_match_volume",
    "match_volume_diff",
    "home_days_since_match",
    "away_days_since_match",
    "days_since_diff",
    "home_country_match",
    "away_country_match",
    "neutral_country_match",
    "home_attack_strength",
    "away_attack_strength",
    "home_defense_strength",
    "away_defense_strength",
    "attack_strength_diff",
    "defense_strength_diff",
]


def outcome_label(home_goals: int, away_goals: int) -> int:
    if home_goals > away_goals:
        return 0
    if home_goals == away_goals:
        return 1
    return 2


def _bounded_days_since(value: float | None) -> float:
    if value is None:
        return 30.0
    return float(min(max(value, 0.0), 180.0))


@dataclass
class TeamRollingProfile:
    matches: int = 0
    recent_points: tuple[float, ...] = ()
    recent_gd: tuple[float, ...] = ()
    recent_gf: tuple[float, ...] = ()
    recent_ga: tuple[float, ...] = ()
    last_match_date: date | None = None
    goals_for: int = 0
    goals_against: int = 0

    def snapshot(self, current_date: date | None = None) -> dict[str, float]:
        def average(values: tuple[float, ...]) -> float:
            return float(sum(values) / len(values)) if values else 0.0

        days_since = None
        if current_date is not None and self.last_match_date is not None:
            days_since = float((current_date - self.last_match_date).days)

        return {
            "recent_points": average(self.recent_points),
            "recent_gd": average(self.recent_gd),
            "recent_goals_for": average(self.recent_gf),
            "recent_goals_against": average(self.recent_ga),
            "match_volume": float(log1p(self.matches)),
            "days_since_match": _bounded_days_since(days_since),
            "attack_strength": float(self.goals_for / self.matches) if self.matches else 0.0,
            "defense_strength": float(self.goals_against / self.matches) if self.matches else 0.0,
        }

    def updated(self, points: float, gf: int, ga: int, match_date: date | None) -> "TeamRollingProfile":
        return TeamRollingProfile(
            matches=self.matches + 1,
            recent_points=(*self.recent_points, float(points))[-10:],
            recent_gd=(*self.recent_gd, float(gf - ga))[-10:],
            recent_gf=(*self.recent_gf, float(gf))[-10:],
            recent_ga=(*self.recent_ga, float(ga))[-10:],
            last_match_date=match_date or self.last_match_date,
            goals_for=self.goals_for + int(gf),
            goals_against=self.goals_against + int(ga),
        )


def points_for(goals_for: int, goals_against: int) -> float:
    if goals_for > goals_against:
        return 3.0
    if goals_for == goals_against:
        return 1.0
    return 0.0


@dataclass
class FeatureBuilder:
    elo: EloSystem
    profiles: dict[str, TeamRollingProfile] | None = None

    def __post_init__(self) -> None:
        if self.profiles is None:
            self.profiles = {}

    def profile(self, team: str) -> TeamRollingProfile:
        assert self.profiles is not None
        team = canonical_team(team)
        if team not in self.profiles:
            self.profiles[team] = TeamRollingProfile()
        return self.profiles[team]

    def row_features(
        self,
        home: str,
        away: str,
        neutral: bool,
        tournament: str,
        match_date: date | None = None,
        country: str | None = None,
    ) -> dict[str, float]:
        home = canonical_team(home)
        away = canonical_team(away)
        country = canonical_team(country) if country else None
        home_rating = self.elo.rating(home)
        away_rating = self.elo.rating(away)
        home_advantage = 0.0 if neutral else self.elo.home_advantage
        home_profile = self.profile(home).snapshot(match_date)
        away_profile = self.profile(away).snapshot(match_date)
        home_country = float(country == home)
        away_country = float(country == away)
        return {
            "elo_diff": home_rating + home_advantage - away_rating,
            "home_rating": home_rating,
            "away_rating": away_rating,
            "neutral": float(neutral),
            "home_advantage": home_advantage,
            "importance": tournament_weight(tournament),
            "home_recent_points": home_profile["recent_points"],
            "away_recent_points": away_profile["recent_points"],
            "recent_points_diff": home_profile["recent_points"] - away_profile["recent_points"],
            "home_recent_gd": home_profile["recent_gd"],
            "away_recent_gd": away_profile["recent_gd"],
            "recent_gd_diff": home_profile["recent_gd"] - away_profile["recent_gd"],
            "home_recent_goals_for": home_profile["recent_goals_for"],
            "away_recent_goals_for": away_profile["recent_goals_for"],
            "home_recent_goals_against": home_profile["recent_goals_against"],
            "away_recent_goals_against": away_profile["recent_goals_against"],
            "home_match_volume": home_profile["match_volume"],
            "away_match_volume": away_profile["match_volume"],
            "match_volume_diff": home_profile["match_volume"] - away_profile["match_volume"],
            "home_days_since_match": home_profile["days_since_match"],
            "away_days_since_match": away_profile["days_since_match"],
            "days_since_diff": home_profile["days_since_match"] - away_profile["days_since_match"],
            "home_country_match": home_country,
            "away_country_match": away_country,
            "neutral_country_match": float(bool(neutral) and country is not None and not home_country and not away_country),
            "home_attack_strength": home_profile["attack_strength"],
            "away_attack_strength": away_profile["attack_strength"],
            "home_defense_strength": home_profile["defense_strength"],
            "away_defense_strength": away_profile["defense_strength"],
            "attack_strength_diff": home_profile["attack_strength"] - away_profile["attack_strength"],
            "defense_strength_diff": away_profile["defense_strength"] - home_profile["defense_strength"],
        }

    def update_profiles(self, home: str, away: str, home_goals: int, away_goals: int, match_date: date | None) -> None:
        assert self.profiles is not None
        home = canonical_team(home)
        away = canonical_team(away)
        self.profiles[home] = self.profile(home).updated(points_for(home_goals, away_goals), home_goals, away_goals, match_date)
        self.profiles[away] = self.profile(away).updated(points_for(away_goals, home_goals), away_goals, home_goals, match_date)

    def build_training_frame(self, matches: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, EloSystem]:
        rows: list[dict[str, float]] = []
        labels: list[int] = []
        for match in matches.itertuples(index=False):
            match_date = match.date.date() if hasattr(match.date, "date") else match.date
            rows.append(
                self.row_features(
                    match.home_team,
                    match.away_team,
                    match.neutral,
                    match.tournament,
                    match_date=match_date,
                    country=getattr(match, "country", None),
                )
            )
            labels.append(outcome_label(match.home_score, match.away_score))
            self.elo.update_match(
                match.home_team,
                match.away_team,
                match.home_score,
                match.away_score,
                match.tournament,
                match.neutral,
            )
            self.update_profiles(match.home_team, match.away_team, match.home_score, match.away_score, match_date)
        return pd.DataFrame(rows, columns=FEATURE_COLUMNS), pd.Series(labels, name="outcome"), self.elo
