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


def load_source_metadata(config_path: str) -> dict[str, object]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency is part of project runtime
        raise RuntimeError("PyYAML is required to export source metadata") from exc

    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    rankings = config.get("fifa_rankings", {})
    return {
        "sourceNotes": config.get("source_notes", []),
        "fifaRankingSource": rankings.get("source"),
        "fifaRankingPulledAt": rankings.get("pulled_at"),
        "fifaRankingOfficialDate": rankings.get("official_date"),
        "fixtureCount": len(config.get("fixtures", [])),
        "venueCount": len(config.get("venues", [])),
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
    source_metadata = load_source_metadata(args.tournament_config)

    improved = backtest["improved"]
    baseline = backtest["baseline"]

    payload = {
        "model": {
            "rows": model.metadata["rows"],
            "firstMatch": model.metadata["first_match"],
            "lastMatch": model.metadata["last_match"],
            "blendWeight": model.metadata.get("blend_weight", 0.75),
            "cValue": model.metadata.get("c_value"),
            "featureColumns": model.metadata.get("feature_columns", []),
            "featureSummary": model.metadata.get("feature_summary", {}),
            "selection": model.metadata.get("selection"),
        },
        "backtest": {
            "cutoff": backtest["cutoff"],
            "trainMatches": backtest["train_matches"],
            "testMatches": backtest["test_matches"],
            "improved": backtest["improved"],
            "baseline": backtest["baseline"],
            "selection": backtest.get("selection"),
            "rollingWindows": backtest.get("rolling_windows", []),
            "deltas": {
                "logLoss": baseline["log_loss"] - improved["log_loss"],
                "brierScore": baseline["brier_score"] - improved["brier_score"],
                "accuracy": improved["accuracy"] - baseline["accuracy"],
            },
        },
        "simulation": {
            "runs": simulation["runs"],
            "seed": simulation["seed"],
            "year": simulation["year"],
            "contextFeatures": simulation.get("context_features", {}),
            "tiebreakNotes": simulation.get("tiebreak_notes", []),
        },
        "champions": simulation["champion_probabilities"],
        "stageProbabilities": simulation["stage_probabilities"],
        "groupAdvancementProbabilities": simulation["group_advancement_probabilities"],
        "teamMetadata": team_metadata,
        "teamContext": simulation.get("team_context", {}),
        "bracketChallenge": simulation.get("bracket_challenge", {}),
        "sources": source_metadata,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
