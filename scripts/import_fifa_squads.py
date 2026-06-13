from __future__ import annotations

import argparse
import re
import unicodedata
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pypdf import PdfReader


SOURCE_URL = "https://fdp.fifa.org/assetspublic/ce281/pdf/SquadLists-English.pdf"
PUBLISHED_AT_UTC = "2026-06-12T21:07:00Z"
VERSION = "Version 1"

TEAM_ALIASES = {
    "Bosnia And Herzegovina": "Bosnia and Herzegovina",
    "Cabo Verde": "Cape Verde",
    "Congo DR": "DR Congo",
    "Côte D'Ivoire": "Ivory Coast",
    "Curaçao": "Curacao",
    "Czechia": "Czech Republic",
    "IR Iran": "Iran",
    "Korea Republic": "South Korea",
    "Türkiye": "Turkey",
    "USA": "United States",
}

POSITION_ROLE = {
    "GK": "goalkeeper",
    "DF": "defender",
    "MF": "midfielder",
    "FW": "forward",
}


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\x00", "")).strip()


def title_name(value: str) -> str:
    value = clean(value)
    value = re.sub(r"\bM\s+AC\b", "MAC", value)
    value = re.sub(r"\bM\s+([A-ZÁÉÍÓÚÏÄÖÜÑÇ]{2,})", r"M\1", value)
    value = value.title()
    replacements = {
        " Fc": " FC",
        " Afc": " AFC",
        " C.F.": " C.F.",
        " C. F.": " C. F.",
        " Ac ": " AC ",
        " Ca ": " CA ",
        " Cd ": " CD ",
        " Cf": " CF",
        " Cp": " CP",
        " Fc ": " FC ",
        " Rb ": " RB ",
        " Rc ": " RC ",
        " Sc ": " SC ",
        " Sl ": " SL ",
        " Usm ": " USM ",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return clean(value)


def normalize_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def display_from_player_name(source_name: str, first_names: str, last_names: str) -> str:
    source_name = clean(source_name)
    tokens = source_name.split()
    split_index = next((index for index, token in enumerate(tokens) if not token.isupper()), None)
    if split_index and split_index > 0:
        given = " ".join(tokens[split_index:])
        family = " ".join(tokens[:split_index])
        return title_name(f"{given} {family}")
    if first_names and last_names:
        return title_name(f"{first_names.split()[0]} {last_names}")
    return title_name(source_name)


def split_player_columns(prefix: str, fallback_starts: list[int]) -> tuple[str, str, str, str]:
    parts = [clean(part) for part in re.split(r"\s{2,}", prefix.strip()) if clean(part)]
    if len(parts) >= 4:
        return parts[0], parts[1], parts[2], parts[3]
    if len(parts) == 3:
        combined, last_names, shirt_name = parts
        if normalize_key(combined).startswith(normalize_key(last_names)):
            first_blob = clean(combined[len(last_names) :])
            if len(first_blob) % 2 == 0:
                half = first_blob[: len(first_blob) // 2]
                if half and first_blob == half + half:
                    first_blob = half
            return clean(f"{last_names} {first_blob}"), first_blob, last_names, shirt_name

    fields = []
    for start, end in zip(fallback_starts, fallback_starts[1:]):
        fields.append(clean(prefix[start:end] if start < len(prefix) else ""))
    while len(fields) < 4:
        fields.append("")
    return fields[0], fields[1], fields[2], fields[3]


def parse_page(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    header = next(line for line in lines if "PLAYER NAME" in line and "NAME ON SHIRT" in line)
    starts = {
        name: header.find(name)
        for name in ["PLAYER NAME", "FIRST NAME(S)", "LAST NAME(S)", "NAME ON SHIRT", "DOB"]
    }
    fallback_starts = [
        0,
        starts["FIRST NAME(S)"] - starts["PLAYER NAME"],
        starts["LAST NAME(S)"] - starts["PLAYER NAME"],
        starts["NAME ON SHIRT"] - starts["PLAYER NAME"],
        starts["DOB"] - starts["PLAYER NAME"],
    ]

    source_team = ""
    fifa_code = ""
    for line in lines:
        match = re.search(r"\b(.+?)\s+\(([A-Z]{3})\)\s*$", line.strip())
        if match and "Page" not in line:
            source_team = clean(match.group(1))
            fifa_code = match.group(2)
            break

    players: list[dict[str, Any]] = []
    for line in lines:
        row = re.match(r"^\s*(\d{1,2})\s*(GK|DF|MF|FW)\s+(.*)$", line)
        if not row:
            continue
        dob_match = re.search(r"\d{2}/\d{2}/\d{4}", row.group(3))
        if not dob_match:
            continue

        prefix = row.group(3)[: dob_match.start()]
        tail = row.group(3)[dob_match.end() :]
        tail_match = re.match(
            r"(?P<club>.*?)(?P<height>\d{3})\s+(?P<caps>\d+)\s+(?P<goals>\d+)\s*$",
            tail,
        )
        club = clean(tail_match.group("club")) if tail_match else ""
        height = int(tail_match.group("height")) if tail_match else None
        caps = int(tail_match.group("caps")) if tail_match else 0
        goals = int(tail_match.group("goals")) if tail_match else 0
        player_name, first_names, last_names, shirt_name = split_player_columns(prefix, fallback_starts)
        display_name = display_from_player_name(player_name, first_names, last_names)
        players.append(
            {
                "number": int(row.group(1)),
                "position": row.group(2),
                "role": POSITION_ROLE[row.group(2)],
                "playerName": title_name(player_name),
                "firstNames": title_name(first_names),
                "lastNames": title_name(last_names),
                "displayName": display_name,
                "nameOnShirt": clean(shirt_name),
                "dateOfBirth": dob_match.group(0),
                "club": title_name(club),
                "heightCm": height,
                "caps": caps,
                "goals": goals,
            }
        )

    coach: dict[str, str] = {}
    for line in lines:
        if "Head coach" not in line:
            continue
        parts = [clean(part) for part in re.split(r"\s{2,}", line.strip()) if clean(part)]
        if len(parts) >= 5:
            coach = {
                "name": title_name(f"{parts[2]} {parts[3]}"),
                "firstNames": title_name(parts[2]),
                "lastNames": title_name(parts[3]),
                "nationality": parts[4],
            }
        elif len(parts) >= 2:
            coach = {"name": title_name(parts[1])}
        break

    return {
        "team": TEAM_ALIASES.get(source_team, source_team),
        "sourceTeamName": source_team,
        "fifaCode": fifa_code,
        "coach": coach,
        "players": players,
    }


def parse_pdf(pdf_path: Path, snapshot_timestamp: str) -> dict[str, Any]:
    reader = PdfReader(str(pdf_path))
    teams = [parse_page(page.extract_text(extraction_mode="layout")) for page in reader.pages]
    return {
        "source": SOURCE_URL,
        "version": VERSION,
        "publishedAtUtc": PUBLISHED_AT_UTC,
        "snapshotTimestampUtc": snapshot_timestamp,
        "teamCount": len(teams),
        "teams": teams,
    }


def download_pdf(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as response:
        target.write_bytes(response.read())


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def player_keys(player: dict[str, Any]) -> set[str]:
    keys = {
        normalize_key(player.get("displayName", "")),
        normalize_key(player.get("playerName", "")),
        normalize_key(player.get("nameOnShirt", "")),
    }
    if player.get("firstNames") and player.get("lastNames"):
        keys.add(normalize_key(f"{player['firstNames'].split()[0]} {player['lastNames']}"))
    return {key for key in keys if key}


def select_scorers(snapshot: dict[str, Any], previous_pool: dict[str, Any]) -> dict[str, Any]:
    previous_teams = previous_pool.get("teams", {}) if previous_pool else {}
    output: dict[str, Any] = {
        "source_notes": [
            "Squad-backed scorer pool regenerated from the official FIFA World Cup 2026 squad list PDF.",
            f"Squad source: {SOURCE_URL}; {VERSION}; published {PUBLISHED_AT_UTC}.",
            "Weights combine current squad position, international goals/caps, and matched prior attacking-role weights when the prior player still appears in the official squad.",
            "Played-match scorers in the tournament config override this pool.",
        ],
        "teams": {},
    }

    for team in snapshot["teams"]:
        previous_by_key: dict[str, dict[str, Any]] = {}
        for row in previous_teams.get(team["team"], []):
            previous_by_key[normalize_key(str(row.get("player", "")))] = row

        candidates: list[dict[str, Any]] = []
        max_goals = max((player.get("goals", 0) for player in team["players"]), default=1) or 1
        max_caps = max((player.get("caps", 0) for player in team["players"]), default=1) or 1
        for player in team["players"]:
            matched_prior = next(
                (previous_by_key[key] for key in player_keys(player) if key in previous_by_key),
                None,
            )
            position_bonus = {"FW": 0.42, "MF": 0.18, "DF": 0.05, "GK": 0.0}[player["position"]]
            production = (player.get("goals", 0) / max_goals) * 1.15
            experience = (player.get("caps", 0) / max_caps) * 0.18
            prior_weight = float(matched_prior.get("weight", 0.0)) if matched_prior else 0.0
            weight = max(0.45 + position_bonus + production + experience, prior_weight)
            candidates.append(
                {
                    "player": matched_prior.get("player", player["displayName"]) if matched_prior else player["displayName"],
                    "officialName": player["displayName"],
                    "number": player["number"],
                    "position": player["position"],
                    "weight": round(weight, 3),
                    "role": POSITION_ROLE[player["position"]],
                    "penalties": bool(matched_prior.get("penalties", False)) if matched_prior else False,
                    "set_pieces": bool(matched_prior.get("set_pieces", False)) if matched_prior else False,
                    "source": "official_squad",
                }
            )
        candidates.sort(
            key=lambda row: (
                row["weight"],
                {"FW": 3, "MF": 2, "DF": 1, "GK": 0}[row["position"]],
                row["number"] * -0.01,
            ),
            reverse=True,
        )
        output["teams"][team["team"]] = candidates[:8]

    return output


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    if snapshot["teamCount"] != 48 or len(snapshot["teams"]) != 48:
        raise ValueError(f"expected 48 teams, found {len(snapshot['teams'])}")
    bad = [team["team"] for team in snapshot["teams"] if len(team.get("players", [])) != 26]
    if bad:
        raise ValueError(f"expected 26 players for every team, failed: {bad}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import official FIFA World Cup 2026 squad PDF.")
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--download-url", default=SOURCE_URL)
    parser.add_argument("--squads-output", type=Path, default=Path("data/squads_2026.yaml"))
    parser.add_argument("--scorer-pool-output", type=Path, default=Path("data/player_scorer_pool_2026.yaml"))
    parser.add_argument("--previous-scorer-pool", type=Path, default=Path("data/player_scorer_pool_2026.yaml"))
    parser.add_argument(
        "--snapshot-timestamp-utc",
        default=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    args = parser.parse_args()

    pdf_path = args.pdf or Path("data/raw/SquadLists-English.pdf")
    if args.pdf is None:
        download_pdf(args.download_url, pdf_path)

    snapshot = parse_pdf(pdf_path, args.snapshot_timestamp_utc)
    validate_snapshot(snapshot)
    previous_pool = load_yaml(args.previous_scorer_pool)
    scorer_pool = select_scorers(snapshot, previous_pool)

    args.squads_output.parent.mkdir(parents=True, exist_ok=True)
    args.squads_output.write_text(
        yaml.safe_dump(snapshot, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    args.scorer_pool_output.parent.mkdir(parents=True, exist_ok=True)
    args.scorer_pool_output.write_text(
        yaml.safe_dump(scorer_pool, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    print(f"Imported {len(snapshot['teams'])} teams into {args.squads_output}")
    print(f"Regenerated scorer pool at {args.scorer_pool_output}")


if __name__ == "__main__":
    main()
