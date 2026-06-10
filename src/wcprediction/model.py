from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data import load_results
from .elo import EloSystem, SimpleEloBaseline
from .features import FEATURE_COLUMNS, FeatureBuilder, outcome_label
from .metrics import accuracy, brier_score, calibration_bins, multiclass_log_loss
from .teams import canonical_team

LABELS = ["home_win", "draw", "away_win"]


@dataclass
class TrainedModel:
    estimator: Pipeline
    elo: EloSystem
    baseline: SimpleEloBaseline
    metadata: dict[str, Any]
    blend_weight: float = 0.75

    def predict_match(self, home: str, away: str, neutral: bool = True, tournament: str = "FIFA World Cup") -> dict[str, float]:
        home = canonical_team(home)
        away = canonical_team(away)
        builder = FeatureBuilder(self.elo)
        features = pd.DataFrame([builder.row_features(home, away, neutral, tournament)], columns=FEATURE_COLUMNS)
        model_probabilities = self.estimator.predict_proba(features)[0]
        baseline_probabilities = np.asarray(self.baseline.predict(home, away), dtype=float)
        probabilities = self.blend_weight * model_probabilities + (1.0 - self.blend_weight) * baseline_probabilities
        return {label: float(probabilities[i]) for i, label in enumerate(LABELS)}


def make_estimator(seed: int = 42) -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "logistic",
                LogisticRegression(
                    C=0.8,
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=seed,
                ),
            ),
        ]
    )


def train_from_frame(matches: pd.DataFrame, seed: int = 42) -> TrainedModel:
    elo = EloSystem()
    features, labels, fitted_elo = FeatureBuilder(elo).build_training_frame(matches)
    estimator = make_estimator(seed)
    estimator.fit(features, labels)
    baseline = SimpleEloBaseline()
    for match in matches.itertuples(index=False):
        baseline.update_match(match.home_team, match.away_team, match.home_score, match.away_score)
    metadata = {
        "rows": int(len(matches)),
        "first_match": str(matches["date"].min().date()) if len(matches) else None,
        "last_match": str(matches["date"].max().date()) if len(matches) else None,
        "feature_columns": FEATURE_COLUMNS,
        "labels": LABELS,
        "blend_weight": 0.75,
    }
    return TrainedModel(estimator=estimator, elo=fitted_elo, baseline=baseline, metadata=metadata)


def train(results_path: Path | str, output_path: Path | str = "artifacts/model.joblib", seed: int = 42) -> TrainedModel:
    matches = load_results(results_path)
    model = train_from_frame(matches, seed=seed)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, output)
    return model


def load_model(path: Path | str) -> TrainedModel:
    loaded = joblib.load(path)
    if not isinstance(loaded, TrainedModel):
        raise TypeError(f"{path} does not contain a TrainedModel")
    return loaded


def _metrics(labels: list[int], probabilities: list[list[float]]) -> dict[str, Any]:
    return {
        "matches": len(labels),
        "log_loss": multiclass_log_loss(labels, probabilities),
        "brier_score": brier_score(labels, probabilities),
        "accuracy": accuracy(labels, probabilities),
        "calibration": calibration_bins(labels, probabilities),
    }


def backtest(results_path: Path | str, cutoff: str = "2018-01-01", seed: int = 42) -> dict[str, Any]:
    matches = load_results(results_path)
    cutoff_ts = pd.Timestamp(cutoff)
    train_matches = matches[matches["date"] < cutoff_ts].reset_index(drop=True)
    test_matches = matches[matches["date"] >= cutoff_ts].reset_index(drop=True)
    if train_matches.empty or test_matches.empty:
        raise ValueError("cutoff must leave both training and testing matches")

    improved = train_from_frame(train_matches, seed=seed)
    improved_labels: list[int] = []
    improved_probs: list[list[float]] = []
    improved_elo = improved.elo
    improved_baseline = improved.baseline
    for match in test_matches.itertuples(index=False):
        builder = FeatureBuilder(improved_elo)
        features = pd.DataFrame(
            [builder.row_features(match.home_team, match.away_team, match.neutral, match.tournament)],
            columns=FEATURE_COLUMNS,
        )
        model_probabilities = improved.estimator.predict_proba(features)[0]
        baseline_probabilities = np.asarray(improved_baseline.predict(match.home_team, match.away_team), dtype=float)
        blended = improved.blend_weight * model_probabilities + (1.0 - improved.blend_weight) * baseline_probabilities
        improved_probs.append(blended.tolist())
        improved_labels.append(outcome_label(match.home_score, match.away_score))
        improved_elo.update_match(
            match.home_team,
            match.away_team,
            match.home_score,
            match.away_score,
            match.tournament,
            match.neutral,
        )
        improved_baseline.update_match(match.home_team, match.away_team, match.home_score, match.away_score)

    baseline = SimpleEloBaseline()
    for match in train_matches.itertuples(index=False):
        baseline.update_match(match.home_team, match.away_team, match.home_score, match.away_score)

    baseline_labels: list[int] = []
    baseline_probs: list[list[float]] = []
    for match in test_matches.itertuples(index=False):
        baseline_probs.append(baseline.predict(match.home_team, match.away_team))
        baseline_labels.append(outcome_label(match.home_score, match.away_score))
        baseline.update_match(match.home_team, match.away_team, match.home_score, match.away_score)

    return {
        "cutoff": str(cutoff_ts.date()),
        "train_matches": int(len(train_matches)),
        "test_matches": int(len(test_matches)),
        "improved": _metrics(improved_labels, improved_probs),
        "baseline": _metrics(baseline_labels, baseline_probs),
    }
