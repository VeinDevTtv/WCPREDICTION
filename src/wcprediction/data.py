from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

from .teams import canonical_team

DEFAULT_DATA_DIR = Path("data/raw")
RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
SHOOTOUTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/shootouts.csv"


@dataclass(frozen=True)
class DataPaths:
    data_dir: Path = DEFAULT_DATA_DIR

    @property
    def results(self) -> Path:
        return self.data_dir / "results.csv"

    @property
    def shootouts(self) -> Path:
        return self.data_dir / "shootouts.csv"


def fetch_open_data(data_dir: Path = DEFAULT_DATA_DIR) -> DataPaths:
    """Download public international results CSV files."""
    paths = DataPaths(Path(data_dir))
    paths.data_dir.mkdir(parents=True, exist_ok=True)
    urlretrieve(RESULTS_URL, paths.results)
    urlretrieve(SHOOTOUTS_URL, paths.shootouts)
    return paths


def load_results(path: Path | str = DEFAULT_DATA_DIR / "results.csv") -> pd.DataFrame:
    """Load and normalize historical match results."""
    df = pd.read_csv(path)
    expected = {
        "date",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "tournament",
        "country",
        "neutral",
    }
    missing = expected.difference(df.columns)
    if missing:
        raise ValueError(f"results data missing required columns: {sorted(missing)}")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "home_team", "away_team", "home_score", "away_score"])
    df["home_team"] = df["home_team"].map(canonical_team)
    df["away_team"] = df["away_team"].map(canonical_team)
    df["home_score"] = df["home_score"].astype(int)
    df["away_score"] = df["away_score"].astype(int)
    df["neutral"] = df["neutral"].astype(bool)
    return df.sort_values("date").reset_index(drop=True)
