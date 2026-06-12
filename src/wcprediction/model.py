from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data import DEFAULT_DATA_DIR, load_results, load_shootouts
from .elo import EloSystem, SimpleEloBaseline
from .features import FEATURE_COLUMNS, FeatureBuilder, TeamRollingProfile, outcome_label
from .metrics import accuracy, brier_score, calibration_bins, multiclass_log_loss
from .teams import canonical_team

LABELS = ["home_win", "draw", "away_win"]


def _three_class_probabilities(estimator: Pipeline, features: pd.DataFrame) -> np.ndarray:
    raw = estimator.predict_proba(features)[0]
    classes = list(estimator.named_steps["logistic"].classes_)
    probabilities = np.zeros(3, dtype=float)
    for index, class_id in enumerate(classes):
        probabilities[int(class_id)] = raw[index]
    if probabilities.sum() == 0:
        probabilities[:] = 1.0 / 3.0
    return probabilities / probabilities.sum()


@dataclass
class TrainedModel:
    estimator: Pipeline
    elo: EloSystem
    baseline: SimpleEloBaseline
    metadata: dict[str, Any]
    blend_weight: float = 0.75
    profiles: dict[str, TeamRollingProfile] | None = None
    shootout_strengths: dict[str, float] | None = None

    def predict_match(
        self,
        home: str,
        away: str,
        neutral: bool = True,
        tournament: str = "FIFA World Cup",
        country: str | None = None,
    ) -> dict[str, float]:
        home = canonical_team(home)
        away = canonical_team(away)
        builder = FeatureBuilder(self.elo, profiles=dict(self.profiles or {}))
        features = pd.DataFrame(
            [builder.row_features(home, away, neutral, tournament, country=country)],
            columns=FEATURE_COLUMNS,
        )
        model_probabilities = _three_class_probabilities(self.estimator, features)
        baseline_probabilities = np.asarray(self.baseline.predict(home, away), dtype=float)
        probabilities = self.blend_weight * model_probabilities + (1.0 - self.blend_weight) * baseline_probabilities
        return {label: float(probabilities[i]) for i, label in enumerate(LABELS)}


def make_estimator(seed: int = 42, c_value: float = 0.8) -> Pipeline:
    return Pipeline(
        [
            ("scale", StandardScaler()),
            (
                "logistic",
                LogisticRegression(
                    C=c_value,
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=seed,
                ),
            ),
        ]
    )


def shootout_strengths_from_frame(shootouts: pd.DataFrame | None) -> dict[str, float]:
    if shootouts is None or shootouts.empty:
        return {}
    attempts: dict[str, int] = {}
    wins: dict[str, int] = {}
    for row in shootouts.itertuples(index=False):
        home = canonical_team(row.home_team)
        away = canonical_team(row.away_team)
        winner = canonical_team(row.winner)
        attempts[home] = attempts.get(home, 0) + 1
        attempts[away] = attempts.get(away, 0) + 1
        wins[winner] = wins.get(winner, 0) + 1
    return {
        team: float((wins.get(team, 0) + 1.0) / (attempts[team] + 2.0))
        for team in sorted(attempts)
    }


def _fit_state(matches: pd.DataFrame, seed: int, c_value: float) -> tuple[Pipeline, EloSystem, SimpleEloBaseline, dict[str, TeamRollingProfile]]:
    elo = EloSystem()
    builder = FeatureBuilder(elo)
    features, labels, fitted_elo = builder.build_training_frame(matches)
    estimator = make_estimator(seed, c_value=c_value)
    estimator.fit(features, labels)
    baseline = SimpleEloBaseline()
    for match in matches.itertuples(index=False):
        baseline.update_match(match.home_team, match.away_team, match.home_score, match.away_score)
    return estimator, fitted_elo, baseline, dict(builder.profiles or {})


def _predict_frame(
    matches: pd.DataFrame,
    estimator: Pipeline,
    elo: EloSystem,
    baseline: SimpleEloBaseline,
    profiles: dict[str, TeamRollingProfile],
    blend_weight: float,
) -> tuple[list[int], list[list[float]]]:
    labels: list[int] = []
    probabilities: list[list[float]] = []
    builder = FeatureBuilder(elo, profiles=dict(profiles))
    for match in matches.itertuples(index=False):
        match_date = match.date.date() if hasattr(match.date, "date") else match.date
        row = builder.row_features(
            match.home_team,
            match.away_team,
            match.neutral,
            match.tournament,
            match_date=match_date,
            country=getattr(match, "country", None),
        )
        features = pd.DataFrame([row], columns=FEATURE_COLUMNS)
        model_probabilities = _three_class_probabilities(estimator, features)
        baseline_probabilities = np.asarray(baseline.predict(match.home_team, match.away_team), dtype=float)
        blended = blend_weight * model_probabilities + (1.0 - blend_weight) * baseline_probabilities
        probabilities.append(blended.tolist())
        labels.append(outcome_label(match.home_score, match.away_score))
        elo.update_match(
            match.home_team,
            match.away_team,
            match.home_score,
            match.away_score,
            match.tournament,
            match.neutral,
        )
        baseline.update_match(match.home_team, match.away_team, match.home_score, match.away_score)
        builder.update_profiles(match.home_team, match.away_team, match.home_score, match.away_score, match_date)
    return labels, probabilities


def _select_hyperparameters(matches: pd.DataFrame, seed: int) -> dict[str, Any]:
    if len(matches) < 30:
        return {"c_value": 0.8, "blend_weight": 0.75, "validation": None}

    split = max(int(len(matches) * 0.8), len(matches) - 2500)
    split = min(max(split, 12), len(matches) - 3)
    train_matches = matches.iloc[:split].reset_index(drop=True)
    validation_matches = matches.iloc[split:].reset_index(drop=True)
    candidates: list[dict[str, Any]] = []
    for c_value in [0.35, 0.8, 1.4]:
        estimator, elo, baseline, profiles = _fit_state(train_matches, seed, c_value)
        for blend_weight in [0.55, 0.7, 0.85, 1.0]:
            labels, probs = _predict_frame(
                validation_matches,
                estimator,
                elo=copy.deepcopy(elo),
                baseline=copy.deepcopy(baseline),
                profiles=profiles,
                blend_weight=blend_weight,
            )
            candidates.append(
                {
                    "c_value": c_value,
                    "blend_weight": blend_weight,
                    "log_loss": multiclass_log_loss(labels, probs),
                    "brier_score": brier_score(labels, probs),
                    "accuracy": accuracy(labels, probs),
                }
            )
    best = min(candidates, key=lambda row: (row["log_loss"], row["brier_score"]))
    return {
        "c_value": best["c_value"],
        "blend_weight": best["blend_weight"],
        "validation": {
            "matches": int(len(validation_matches)),
            "candidates": candidates,
            "selected": best,
        },
    }


def train_from_frame(
    matches: pd.DataFrame,
    seed: int = 42,
    shootouts: pd.DataFrame | None = None,
) -> TrainedModel:
    selection = _select_hyperparameters(matches, seed)
    estimator, fitted_elo, baseline, profiles = _fit_state(matches, seed, selection["c_value"])
    blend_weight = float(selection["blend_weight"])
    metadata = {
        "rows": int(len(matches)),
        "first_match": str(matches["date"].min().date()) if len(matches) else None,
        "last_match": str(matches["date"].max().date()) if len(matches) else None,
        "feature_columns": FEATURE_COLUMNS,
        "labels": LABELS,
        "blend_weight": blend_weight,
        "c_value": float(selection["c_value"]),
        "selection": selection["validation"],
        "feature_summary": {
            "historical_results": True,
            "rolling_form": True,
            "rest_days": True,
            "host_country": True,
            "attack_defense_strength": True,
            "shootout_history": shootouts is not None and not shootouts.empty,
        },
    }
    return TrainedModel(
        estimator=estimator,
        elo=fitted_elo,
        baseline=baseline,
        metadata=metadata,
        blend_weight=blend_weight,
        profiles=profiles,
        shootout_strengths=shootout_strengths_from_frame(shootouts),
    )


def train(
    results_path: Path | str,
    output_path: Path | str = "artifacts/model.joblib",
    seed: int = 42,
    shootouts_path: Path | str | None = DEFAULT_DATA_DIR / "shootouts.csv",
) -> TrainedModel:
    matches = load_results(results_path)
    shootouts = None
    if shootouts_path and Path(shootouts_path).exists():
        shootouts = load_shootouts(shootouts_path)
    model = train_from_frame(matches, seed=seed, shootouts=shootouts)
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


def _rolling_windows(
    matches: pd.DataFrame,
    seed: int,
    cutoffs: list[str],
    c_value: float,
    blend_weight: float,
) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for cutoff in cutoffs:
        cutoff_ts = pd.Timestamp(cutoff)
        train_matches = matches[matches["date"] < cutoff_ts].reset_index(drop=True)
        test_matches = matches[matches["date"] >= cutoff_ts].reset_index(drop=True)
        next_cutoff = cutoff_ts + pd.DateOffset(years=2)
        test_matches = test_matches[test_matches["date"] < next_cutoff].reset_index(drop=True)
        if train_matches.empty or test_matches.empty:
            continue
        estimator, elo, baseline, profiles = _fit_state(train_matches, seed, c_value)
        labels, probs = _predict_frame(
            test_matches,
            estimator,
            elo,
            baseline,
            profiles,
            blend_weight,
        )
        windows.append(
            {
                "cutoff": str(cutoff_ts.date()),
                "test_start": str(test_matches["date"].min().date()),
                "test_end": str(test_matches["date"].max().date()),
                "train_matches": int(len(train_matches)),
                "test_matches": int(len(test_matches)),
                "metrics": _metrics(labels, probs),
                "blend_weight": blend_weight,
                "c_value": c_value,
            }
        )
    return windows


def backtest(results_path: Path | str, cutoff: str = "2018-01-01", seed: int = 42) -> dict[str, Any]:
    matches = load_results(results_path)
    cutoff_ts = pd.Timestamp(cutoff)
    train_matches = matches[matches["date"] < cutoff_ts].reset_index(drop=True)
    test_matches = matches[matches["date"] >= cutoff_ts].reset_index(drop=True)
    if train_matches.empty or test_matches.empty:
        raise ValueError("cutoff must leave both training and testing matches")

    improved = train_from_frame(train_matches, seed=seed)
    improved_labels, improved_probs = _predict_frame(
        test_matches,
        improved.estimator,
        improved.elo,
        improved.baseline,
        dict(improved.profiles or {}),
        improved.blend_weight,
    )

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
        "selection": {
            "blend_weight": improved.blend_weight,
            "c_value": improved.metadata.get("c_value"),
            "feature_columns": FEATURE_COLUMNS,
            "validation": improved.metadata.get("selection"),
        },
        "rolling_windows": _rolling_windows(
            matches,
            seed=seed,
            cutoffs=["2014-01-01", "2016-01-01", "2018-01-01", "2020-01-01", "2022-01-01", "2024-01-01"],
            c_value=float(improved.metadata.get("c_value", 0.8)),
            blend_weight=improved.blend_weight,
        ),
    }
