# Contributing

Thanks for improving WCP Forecast Lab. Keep changes reproducible, tested, and explicit about data sources.

## Local Setup

```bash
python -m pip install -e ".[dev]"
npm --prefix web ci
```

Fetch data if you need to retrain or backtest:

```bash
wcp data fetch
```

## Development Workflow

1. Create a branch from the current working branch.
2. Keep changes scoped to one model, data, dashboard, or documentation improvement.
3. Update tests when behavior changes.
4. Regenerate committed outputs only when the underlying model inputs or dashboard data change.
5. Document any new data source in the README or tournament config source notes.

## Tests

Run Python tests:

```bash
python -m pytest
```

Build the dashboard:

```bash
npm run build
```

For model changes, also run a smoke simulation:

```bash
wcp simulate --tournament 2026 --runs 2000 --seed 42 --model artifacts/model.joblib --output outputs/sim_2026_smoke.json
```

## Data Source Rules

- Prefer public, stable, sourceable data.
- Record the source, pull date, and assumptions in config notes or documentation.
- Do not train on future data for historical backtests.
- Do not silently mix live or unofficial data with official snapshots.
- For injuries, suspensions, squads, and player minutes, include the timestamp and provider when adding non-neutral adjustments.

## Pull Request Checklist

- Tests pass with `python -m pytest`.
- Dashboard builds with `npm run build` when web data or UI changes.
- README or config notes explain new inputs or assumptions.
- Generated files are updated only when necessary.
- Probability changes are summarized with before/after numbers when model behavior changes.

## Code Style

- Keep Python code typed and simple.
- Prefer small, testable functions over hidden constants.
- Keep model feature changes leakage-safe.
- Keep dashboard copy factual and avoid overstating probability precision.
