from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

import yaml

from .teams import canonical_team


@dataclass(frozen=True)
class TournamentConfig:
    year: int
    name: str
    hosts: list[str]
    groups: dict[str, list[str]]
    source_notes: list[str]

    @property
    def teams(self) -> list[str]:
        return [team for group in self.groups.values() for team in group]


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
    )


def group_fixtures(teams: list[str]) -> list[tuple[str, str]]:
    return list(combinations(teams, 2))
