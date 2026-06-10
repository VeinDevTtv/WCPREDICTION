from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .elo import EloSystem, tournament_weight

FEATURE_COLUMNS = [
    "elo_diff",
    "home_rating",
    "away_rating",
    "neutral",
    "home_advantage",
    "importance",
]


def outcome_label(home_goals: int, away_goals: int) -> int:
    if home_goals > away_goals:
        return 0
    if home_goals == away_goals:
        return 1
    return 2


@dataclass
class FeatureBuilder:
    elo: EloSystem

    def row_features(self, home: str, away: str, neutral: bool, tournament: str) -> dict[str, float]:
        home_rating = self.elo.rating(home)
        away_rating = self.elo.rating(away)
        home_advantage = 0.0 if neutral else self.elo.home_advantage
        return {
            "elo_diff": home_rating + home_advantage - away_rating,
            "home_rating": home_rating,
            "away_rating": away_rating,
            "neutral": float(neutral),
            "home_advantage": home_advantage,
            "importance": tournament_weight(tournament),
        }

    def build_training_frame(self, matches: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, EloSystem]:
        rows: list[dict[str, float]] = []
        labels: list[int] = []
        for match in matches.itertuples(index=False):
            rows.append(self.row_features(match.home_team, match.away_team, match.neutral, match.tournament))
            labels.append(outcome_label(match.home_score, match.away_score))
            self.elo.update_match(
                match.home_team,
                match.away_team,
                match.home_score,
                match.away_score,
                match.tournament,
                match.neutral,
            )
        return pd.DataFrame(rows, columns=FEATURE_COLUMNS), pd.Series(labels, name="outcome"), self.elo
