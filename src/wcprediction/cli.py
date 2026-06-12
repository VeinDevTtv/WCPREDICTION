from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data import DEFAULT_DATA_DIR, fetch_open_data
from .model import backtest, load_model, train
from .simulate import simulate_tournament, write_csv_summaries


def _write_json(payload: dict, output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wcp", description="World Cup prediction model CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    data_parser = subparsers.add_parser("data", help="Data commands")
    data_subparsers = data_parser.add_subparsers(dest="data_command", required=True)
    fetch_parser = data_subparsers.add_parser("fetch", help="Download open data")
    fetch_parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))

    train_parser = subparsers.add_parser("train", help="Train model")
    train_parser.add_argument("--results", default=str(DEFAULT_DATA_DIR / "results.csv"))
    train_parser.add_argument("--shootouts", default=str(DEFAULT_DATA_DIR / "shootouts.csv"))
    train_parser.add_argument("--output", default="artifacts/model.joblib")
    train_parser.add_argument("--seed", type=int, default=42)

    backtest_parser = subparsers.add_parser("backtest", help="Run chronological backtest")
    backtest_parser.add_argument("--results", default=str(DEFAULT_DATA_DIR / "results.csv"))
    backtest_parser.add_argument("--cutoff", default="2018-01-01")
    backtest_parser.add_argument("--seed", type=int, default=42)
    backtest_parser.add_argument("--output")

    simulate_parser = subparsers.add_parser("simulate", help="Simulate tournament")
    simulate_parser.add_argument("--tournament", default="2026")
    simulate_parser.add_argument("--config")
    simulate_parser.add_argument("--model", default="artifacts/model.joblib")
    simulate_parser.add_argument("--runs", type=int, default=10000)
    simulate_parser.add_argument("--seed", type=int, default=42)
    simulate_parser.add_argument("--output")
    simulate_parser.add_argument("--csv-dir")
    simulate_parser.add_argument("--scorer-pool", default="data/player_scorer_pool_2026.yaml")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "data" and args.data_command == "fetch":
        paths = fetch_open_data(Path(args.data_dir))
        _write_json(
            {
                "results": str(paths.results),
                "shootouts": str(paths.shootouts),
            },
            None,
        )
        return

    if args.command == "train":
        model = train(args.results, args.output, seed=args.seed, shootouts_path=args.shootouts)
        _write_json({"output": args.output, "metadata": model.metadata}, None)
        return

    if args.command == "backtest":
        report = backtest(args.results, cutoff=args.cutoff, seed=args.seed)
        _write_json(report, args.output)
        return

    if args.command == "simulate":
        config = args.config or f"configs/tournaments/{args.tournament}.yaml"
        model = load_model(args.model)
        report = simulate_tournament(model, config, runs=args.runs, seed=args.seed, scorer_pool_path=args.scorer_pool)
        if args.csv_dir:
            write_csv_summaries(report, args.csv_dir)
        _write_json(report, args.output)
        return

    parser.error("unknown command")
