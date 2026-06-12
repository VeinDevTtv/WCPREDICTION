from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from itertools import combinations
from pathlib import Path
from typing import Any

import yaml

from .teams import canonical_team


@dataclass(frozen=True)
class Venue:
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    altitude_m: float = 0.0
    roof: str = "open"
    avg_temp_c: float | None = None
    avg_humidity_pct: float | None = None


@dataclass(frozen=True)
class FixtureScorer:
    team: str
    player: str
    minute: int
    note: str | None = None


@dataclass(frozen=True)
class FixtureDiscipline:
    team: str
    player: str
    card: str
    minute: int | None = None


@dataclass(frozen=True)
class Fixture:
    match_number: int
    group: str
    date: date
    kickoff_et: str
    kickoff_local: str
    home: str
    away: str
    venue: str
    status: str = "predicted"
    home_goals: int | None = None
    away_goals: int | None = None
    scorers: list[FixtureScorer] | None = None
    discipline: list[FixtureDiscipline] | None = None


@dataclass(frozen=True)
class TeamPrior:
    rank: int
    points: float | None = None


@dataclass(frozen=True)
class TeamAdjustment:
    squad_strength_delta: float = 0.0
    injury_penalty: float = 0.0
    suspension_penalty: float = 0.0
    recent_minutes_penalty: float = 0.0


@dataclass(frozen=True)
class TournamentConfig:
    year: int
    name: str
    hosts: list[str]
    groups: dict[str, list[str]]
    source_notes: list[str]
    venues: dict[str, Venue]
    fixtures: list[Fixture]
    team_priors: dict[str, TeamPrior]
    team_adjustments: dict[str, TeamAdjustment]

    @property
    def teams(self) -> list[str]:
        return [team for group in self.groups.values() for team in group]

    def fixtures_for_group(self, group_name: str) -> list[Fixture]:
        return sorted(
            [fixture for fixture in self.fixtures if fixture.group == group_name],
            key=lambda fixture: fixture.match_number,
        )


def _load_venues(raw: dict[str, Any]) -> dict[str, Venue]:
    venues: dict[str, Venue] = {}
    for venue in raw.get("venues", []):
        name = str(venue["name"])
        venues[name] = Venue(
            name=name,
            city=str(venue["city"]),
            country=str(venue["country"]),
            latitude=float(venue["latitude"]),
            longitude=float(venue["longitude"]),
            altitude_m=float(venue.get("altitude_m", 0.0)),
            roof=str(venue.get("roof", "open")),
            avg_temp_c=float(venue["avg_temp_c"]) if venue.get("avg_temp_c") is not None else None,
            avg_humidity_pct=(
                float(venue["avg_humidity_pct"]) if venue.get("avg_humidity_pct") is not None else None
            ),
        )
    return venues


def _load_fixtures(raw: dict[str, Any]) -> list[Fixture]:
    fixtures: list[Fixture] = []
    for fixture in raw.get("fixtures", []):
        scorers = [
            FixtureScorer(
                team=canonical_team(str(row["team"])),
                player=str(row["player"]),
                minute=int(row["minute"]),
                note=str(row["note"]) if row.get("note") is not None else None,
            )
            for row in fixture.get("scorers", [])
        ]
        discipline = [
            FixtureDiscipline(
                team=canonical_team(str(row["team"])),
                player=str(row["player"]),
                card=str(row["card"]),
                minute=int(row["minute"]) if row.get("minute") is not None else None,
            )
            for row in fixture.get("discipline", [])
        ]
        fixtures.append(
            Fixture(
                match_number=int(fixture["match_number"]),
                group=str(fixture["group"]),
                date=date.fromisoformat(str(fixture["date"])),
                kickoff_et=str(fixture["kickoff_et"]),
                kickoff_local=str(fixture["kickoff_local"]),
                home=canonical_team(str(fixture["home"])),
                away=canonical_team(str(fixture["away"])),
                venue=str(fixture["venue"]),
                status=str(fixture.get("status", "predicted")),
                home_goals=int(fixture["home_goals"]) if fixture.get("home_goals") is not None else None,
                away_goals=int(fixture["away_goals"]) if fixture.get("away_goals") is not None else None,
                scorers=scorers,
                discipline=discipline,
            )
        )
    return sorted(fixtures, key=lambda fixture: fixture.match_number)


def _load_team_priors(raw: dict[str, Any]) -> dict[str, TeamPrior]:
    priors: dict[str, TeamPrior] = {}
    for row in raw.get("fifa_rankings", {}).get("teams", []):
        points = row.get("points")
        priors[canonical_team(str(row["team"]))] = TeamPrior(
            rank=int(row["rank"]),
            points=float(points) if points is not None else None,
        )
    return priors


def _load_team_adjustments(raw: dict[str, Any]) -> dict[str, TeamAdjustment]:
    adjustments: dict[str, TeamAdjustment] = {}
    for row in raw.get("team_adjustments", []):
        adjustments[canonical_team(str(row["team"]))] = TeamAdjustment(
            squad_strength_delta=float(row.get("squad_strength_delta", 0.0)),
            injury_penalty=float(row.get("injury_penalty", 0.0)),
            suspension_penalty=float(row.get("suspension_penalty", 0.0)),
            recent_minutes_penalty=float(row.get("recent_minutes_penalty", 0.0)),
        )
    return adjustments


def load_tournament_config(path: Path | str) -> TournamentConfig:
    with Path(path).open("r", encoding="utf-8") as file:
        raw: dict[str, Any] = yaml.safe_load(file)
    groups = {
        group: [canonical_team(team) for team in teams]
        for group, teams in raw["groups"].items()
    }
    return TournamentConfig(
        year=int(raw["year"]),
        name=str(raw["name"]),
        hosts=[canonical_team(host) for host in raw.get("hosts", [])],
        groups=groups,
        source_notes=list(raw.get("source_notes", [])),
        venues=_load_venues(raw),
        fixtures=_load_fixtures(raw),
        team_priors=_load_team_priors(raw),
        team_adjustments=_load_team_adjustments(raw),
    )


def group_fixtures(teams: list[str]) -> list[tuple[str, str]]:
    return list(combinations(teams, 2))
