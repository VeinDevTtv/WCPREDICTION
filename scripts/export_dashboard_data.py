from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export compact dashboard data for the static web app.")
    parser.add_argument("--backtest", default="outputs/backtest.json")
    parser.add_argument("--simulation", default="outputs/sim_2026.json")
    parser.add_argument("--model-output", default="artifacts/model.joblib")
    parser.add_argument("--output", default="web/src/data/dashboard.json")
    args = parser.parse_args()

    import joblib

    backtest = json.loads(Path(args.backtest).read_text(encoding="utf-8"))
    simulation = json.loads(Path(args.simulation).read_text(encoding="utf-8"))
    model = joblib.load(args.model_output)

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
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
