# WCP Forecast Lab

Reproducible men's World Cup prediction model and dashboard for the 2026 tournament.

The project combines public international match results, dynamic Elo ratings, calibrated match probabilities, official FIFA ranking priors, and tournament-context simulation inputs such as fixtures, venues, travel, rest, and climate.

## What It Includes

- Python package and CLI for fetching data, training, backtesting, and simulating tournaments
- Chronological backtesting with log loss, Brier score, accuracy, and calibration bins
- 2026 tournament config with groups, 72 group-stage fixtures, stadiums, kickoff times, venue coordinates, altitude, and historical June climate features
- Official FIFA ranking rows as an external prior for all 48 teams
- Configurable squad-strength, injury, suspension, and recent-player-minutes adjustments
- Vite/React dashboard generated from committed simulation JSON

## Repository Layout

```text
configs/tournaments/2026.yaml   2026 teams, fixtures, venues, priors, adjustments
data/raw/                       downloaded public match data
outputs/                        backtest and simulation reports
scripts/export_dashboard_data.py dashboard JSON exporter
src/wcprediction/               Python package and CLI implementation
tests/                          pytest test suite
web/                            Vite dashboard
```

## Requirements

- Python 3.10+
- Node.js 20+ for the dashboard
- Git

The core Python model does not require API keys.

## Install

```bash
python -m pip install -e ".[dev]"
npm --prefix web ci
```

## Fetch Data

The training data comes from the public `martj42/international_results` CSV dataset.

```bash
wcp data fetch
```

This downloads `results.csv` and `shootouts.csv` into `data/raw/`.

## Train

```bash
wcp train --output artifacts/model.joblib
```

## Backtest

```bash
wcp backtest --cutoff 2018-01-01 --output outputs/backtest.json
```

The backtest report compares the calibrated feature model against a simple Elo baseline.

## Simulate 2026

```bash
wcp simulate \
  --tournament 2026 \
  --runs 25000 \
  --seed 42 \
  --model artifacts/model.joblib \
  --output outputs/sim_2026.json \
  --csv-dir outputs/sim_csv
```

The simulation reports champion, final, semifinal, quarterfinal, round-of-32, and group advancement probabilities.

## Dashboard

Export the model output into the static dashboard data file:

```bash
python scripts/export_dashboard_data.py \
  --backtest outputs/backtest.json \
  --simulation outputs/sim_2026.json \
  --output web/src/data/dashboard.json
```

Run the dashboard locally:

```bash
npm run dev
```

Build it:

```bash
npm run build
```

## Test

```bash
python -m pytest
npm run build
```

## Deploy

The dashboard is Vercel-ready. This repo is linked to a Vercel project with the app in `web/`.

```bash
cd web
vercel --prod
```

## Data Coverage

Current model inputs:

- Public international match results from `martj42/international_results`
- Match date, teams, scores, tournament, host country, and neutral-site flag
- Dynamic Elo, margin adjustment, home/neutral adjustment, and tournament importance
- Official FIFA ranking rows as an external prior
- Exact 2026 group-stage fixture dates, ET/local kickoff times, stadiums, and host cities
- Venue coordinates, altitude, roof status, travel distance, rest days, and historical June climate features
- Squad-strength, injury, suspension, and recent-player-minutes adjustment fields

Live feeds still needed for maximum accuracy:

- Matchday weather forecasts once fixtures enter a reliable forecast window
- Confirmed injuries, suspensions, lineups, and recent player minutes
- Updated FIFA ranking snapshots after new official releases

## Important Modeling Notes

- Tournament probabilities are not predictions of certainty. They are Monte Carlo estimates under the current inputs.
- The knockout bracket is a deterministic approximation for 32-team progression until the full FIFA third-place matchup table is encoded.
- Weather fields are historical venue-climate features, not matchday forecasts.
- Squad and injury fields currently default to neutral values unless populated in `configs/tournaments/2026.yaml`.
- Any new feature should be validated with chronological backtests to avoid future-data leakage.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, test, and pull request guidelines.
