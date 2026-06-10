from __future__ import annotations

from dataclasses import dataclass, field
from math import log

TOURNAMENT_WEIGHTS = {
    "FIFA World Cup": 2.00,
    "FIFA World Cup qualification": 1.35,
    "UEFA Euro": 1.65,
    "UEFA Euro qualification": 1.20,
    "Copa America": 1.60,
    "AFC Asian Cup": 1.45,
    "African Cup of Nations": 1.45,
    "CONCACAF Gold Cup": 1.35,
    "Oceania Nations Cup": 1.25,
    "Friendly": 0.70,
}


def tournament_weight(name: str) -> float:
    return TOURNAMENT_WEIGHTS.get(str(name), 1.0)


def expected_score(rating_a: float, rating_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))


def actual_score(goals_for: int, goals_against: int) -> float:
    if goals_for > goals_against:
        return 1.0
    if goals_for < goals_against:
        return 0.0
    return 0.5


def margin_multiplier(goal_diff: int, rating_diff: float) -> float:
    diff = abs(goal_diff)
    if diff <= 1:
        return 1.0
    return log(diff + 1.0) * (2.2 / (0.001 * abs(rating_diff) + 2.2))


@dataclass
class EloSystem:
    base_rating: float = 1500.0
    k_factor: float = 22.0
    home_advantage: float = 65.0
    ratings: dict[str, float] = field(default_factory=dict)

    def rating(self, team: str) -> float:
        return self.ratings.setdefault(team, self.base_rating)

    def expected_home(self, home: str, away: str, neutral: bool) -> float:
        home_rating = self.rating(home) + (0.0 if neutral else self.home_advantage)
        return expected_score(home_rating, self.rating(away))

    def update_match(
        self,
        home: str,
        away: str,
        home_goals: int,
        away_goals: int,
        tournament: str = "",
        neutral: bool = True,
    ) -> None:
        home_rating = self.rating(home)
        away_rating = self.rating(away)
        adjusted_home = home_rating + (0.0 if neutral else self.home_advantage)
        expected_home = expected_score(adjusted_home, away_rating)
        actual_home = actual_score(home_goals, away_goals)
        rating_diff = adjusted_home - away_rating
        k = self.k_factor * tournament_weight(tournament) * margin_multiplier(home_goals - away_goals, rating_diff)
        delta = k * (actual_home - expected_home)
        self.ratings[home] = home_rating + delta
        self.ratings[away] = away_rating - delta


@dataclass
class SimpleEloBaseline:
    base_rating: float = 1500.0
    k_factor: float = 30.0
    draw_probability: float = 0.25
    ratings: dict[str, float] = field(default_factory=dict)

    def rating(self, team: str) -> float:
        return self.ratings.setdefault(team, self.base_rating)

    def predict(self, home: str, away: str) -> list[float]:
        p_home_two_way = expected_score(self.rating(home), self.rating(away))
        non_draw = 1.0 - self.draw_probability
        return [
            p_home_two_way * non_draw,
            self.draw_probability,
            (1.0 - p_home_two_way) * non_draw,
        ]

    def update_match(self, home: str, away: str, home_goals: int, away_goals: int) -> None:
        exp_home = expected_score(self.rating(home), self.rating(away))
        act_home = actual_score(home_goals, away_goals)
        delta = self.k_factor * (act_home - exp_home)
        self.ratings[home] = self.rating(home) + delta
        self.ratings[away] = self.rating(away) - delta
