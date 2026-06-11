from __future__ import annotations

import argparse
import json
from pathlib import Path


TEAM_NAME_ALIASES = {
    "Cabo Verde": "Cape Verde",
    "Curaçao": "Curacao",
    "Czechia": "Czech Republic",
    "Türkiye": "Turkey",
}


def normalize_team_name(team: str) -> str:
    return TEAM_NAME_ALIASES.get(team, team)


def load_team_metadata(config_path: str) -> dict[str, dict[str, float | int | str]]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency is part of project runtime
        raise RuntimeError("PyYAML is required to export team metadata") from exc

    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))

    group_by_team = {
        normalize_team_name(team): group
        for group, teams in config.get("groups", {}).items()
        for team in teams
    }
    ranking_by_team = {
        normalize_team_name(row["team"]): {
            "fifaRank": row["rank"],
            "fifaPoints": row["points"],
        }
        for row in config.get("fifa_rankings", {}).get("teams", [])
    }

    return {
        team: {
            "group": group,
            **ranking_by_team.get(team, {}),
        }
        for team, group in group_by_team.items()
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export compact dashboard data for the static web app.")
    parser.add_argument("--backtest", default="outputs/backtest.json")
    parser.add_argument("--simulation", default="outputs/sim_2026.json")
    parser.add_argument("--model-output", default="artifacts/model.joblib")
    parser.add_argument("--tournament-config", default="configs/tournaments/2026.yaml")
    parser.add_argument("--output", default="web/src/data/dashboard.json")
    args = parser.parse_args()

    import joblib

    backtest = json.loads(Path(args.backtest).read_text(encoding="utf-8"))
    simulation = json.loads(Path(args.simulation).read_text(encoding="utf-8"))
    model = joblib.load(args.model_output)
    team_metadata = load_team_metadata(args.tournament_config)

    payload = {
        "model": {
            "rows": model.metadata["rows"],
            "firstMatch": model.metadata["first_match"],
            "lastMatch": model.metadata["last_match"],
            "blendWeight": model.metadata.get("blend_weight", 0.75),
        },
        "backtest": {
            "cutoff": backtest["cutoff"],
            "trainMatches": backtest["train_matches"],
            "testMatches": backtest["test_matches"],
            "improved": backtest["improved"],
            "baseline": backtest["baseline"],
        },
        "simulation": {
            "runs": simulation["runs"],
            "seed": simulation["seed"],
            "year": simulation["year"],
            "contextFeatures": simulation.get("context_features", {}),
        },
        "champions": simulation["champion_probabilities"],
        "stageProbabilities": simulation["stage_probabilities"],
        "groupAdvancementProbabilities": simulation["group_advancement_probabilities"],
        "teamMetadata": team_metadata,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
