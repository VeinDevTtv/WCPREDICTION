from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from math import exp, log
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .model import TrainedModel
from .teams import canonical_team
from .tournament import TournamentConfig, group_fixtures, load_tournament_config


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


def _goal_rates(model: TrainedModel, home: str, away: str, neutral: bool) -> tuple[float, float]:
    diff = _rating(model, home) - _rating(model, away)
    home_adv = 0.0 if neutral else model.elo.home_advantage
    base = log(1.28)
    home_rate = exp(base + 0.0018 * (diff + home_adv))
    away_rate = exp(base - 0.0018 * (diff + home_adv))
    return float(np.clip(home_rate, 0.15, 4.5)), float(np.clip(away_rate, 0.15, 4.5))


def simulate_score(model: TrainedModel, home: str, away: str, rng: np.random.Generator, neutral: bool = True) -> MatchResult:
    home_rate, away_rate = _goal_rates(model, home, away, neutral)
    return MatchResult(home, away, int(rng.poisson(home_rate)), int(rng.poisson(away_rate)))


def simulate_knockout_match(model: TrainedModel, home: str, away: str, rng: np.random.Generator) -> str:
    result = simulate_score(model, home, away, rng, neutral=True)
    if result.winner:
        return result.winner

    home_rate, away_rate = _goal_rates(model, home, away, neutral=True)
    extra_home = int(rng.poisson(home_rate * (30.0 / 90.0)))
    extra_away = int(rng.poisson(away_rate * (30.0 / 90.0)))
    if extra_home > extra_away:
        return home
    if extra_away > extra_home:
        return away

    probs = model.predict_match(home, away, neutral=True)
    home_penalty_strength = probs["home_win"] + 0.5 * probs["draw"]
    return home if rng.random() < home_penalty_strength else away


def simulate_group(group_name: str, teams: list[str], model: TrainedModel, rng: np.random.Generator) -> tuple[list[str], list[dict[str, Any]]]:
    table = {
        team: {"team": team, "group": group_name, "points": 0, "gf": 0, "ga": 0, "gd": 0}
        for team in teams
    }
    for home, away in group_fixtures(teams):
        result = simulate_score(model, home, away, rng, neutral=True)
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

    for row in table.values():
        row["gd"] = row["gf"] - row["ga"]
        row["rating"] = _rating(model, row["team"])
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

    for group_name, teams in config.groups.items():
        ranked, table = simulate_group(group_name, teams, model, rng)
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
            winners.append(simulate_knockout_match(model, home, away, rng))
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
