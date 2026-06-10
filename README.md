# Improved World Cup Prediction Model

This repository contains a reproducible Python package and CLI for men's World Cup prediction. It improves on a simple one-script Elo simulator by using a broad public international results dataset, no API keys, chronological backtesting, richer Elo features, probabilistic match modeling, and Poisson scoreline simulation for tournament tiebreakers.

## Install

```bash
python -m pip install -e ".[dev]"
```

## Data

The core model uses open CSV data from `martj42/international_results`.

```bash
wcp data fetch
```

This downloads:

- `results.csv`
- `shootouts.csv`

into `data/raw/`.

## Train

```bash
wcp train --output artifacts/model.joblib
```

## Backtest

```bash
wcp backtest --cutoff 2018-01-01 --output outputs/backtest.json
```

The report includes log loss, Brier score, accuracy, and calibration bins for both the improved model and a simple Elo baseline.

## Simulate 2026

```bash
wcp simulate --tournament 2026 --runs 100000 --seed 42 --model artifacts/model.joblib --output outputs/2026_simulation.json
```

The simulation reports champion, final, semifinal, quarterfinal, round-of-32, and group advancement probabilities. It also writes optional CSV summaries when `--csv-dir` is provided.

## Web Dashboard

The Vercel-ready dashboard lives in `web/` and is built from committed JSON data exported from the Python model.

```bash
python scripts/export_dashboard_data.py --backtest outputs/backtest.json --simulation outputs/sim_2026.json
npm run build
npm run dev
```

The current dashboard data uses a 25,000-run 2026 simulation and the default 75/25 calibrated ensemble.

## Deployment

Deploy from the Vite app directory.

```bash
cd web
vercel --prod
```

## Notes

- Tournament configuration lives in `configs/tournaments/2026.yaml`.
- Current 2026 groups and format are encoded as public configuration, not hidden code.
- Core functionality does not require API keys.

## Data Coverage

Current model inputs:

- Public international match results from `martj42/international_results`
- Match date, teams, scores, tournament, host country, and neutral-site flag
- Derived dynamic Elo ratings, margin adjustment, home/neutral adjustment, and tournament importance
- 2026 group configuration and 48-team tournament format

Not yet included:

- Official FIFA ranking snapshots as an external prior
- Exact fixture date, kickoff time, stadium, altitude, and travel-distance features
- Matchday weather or historical climate-normal features by venue
- Squad strength, injuries, suspensions, player minutes, rest days, and club-form signals

Those features can improve accuracy, but they should be added only with chronological backtests that prevent future-data leakage.
