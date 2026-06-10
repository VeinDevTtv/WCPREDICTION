from __future__ import annotations

import numpy as np


def clipped_probabilities(probabilities: np.ndarray) -> np.ndarray:
    clipped = np.clip(probabilities, 1e-12, 1.0)
    return clipped / clipped.sum(axis=1, keepdims=True)


def multiclass_log_loss(labels: list[int] | np.ndarray, probabilities: list[list[float]] | np.ndarray) -> float:
    y = np.asarray(labels, dtype=int)
    p = clipped_probabilities(np.asarray(probabilities, dtype=float))
    return float(-np.mean(np.log(p[np.arange(len(y)), y])))


def brier_score(labels: list[int] | np.ndarray, probabilities: list[list[float]] | np.ndarray) -> float:
    y = np.asarray(labels, dtype=int)
    p = clipped_probabilities(np.asarray(probabilities, dtype=float))
    one_hot = np.zeros_like(p)
    one_hot[np.arange(len(y)), y] = 1.0
    return float(np.mean(np.sum((p - one_hot) ** 2, axis=1)))


def accuracy(labels: list[int] | np.ndarray, probabilities: list[list[float]] | np.ndarray) -> float:
    y = np.asarray(labels, dtype=int)
    p = np.asarray(probabilities, dtype=float)
    return float(np.mean(np.argmax(p, axis=1) == y))


def calibration_bins(
    labels: list[int] | np.ndarray,
    probabilities: list[list[float]] | np.ndarray,
    bins: int = 10,
) -> list[dict[str, float]]:
    y = np.asarray(labels, dtype=int)
    p = clipped_probabilities(np.asarray(probabilities, dtype=float))
    confidence = p.max(axis=1)
    predicted = p.argmax(axis=1)
    correct = (predicted == y).astype(float)
    output: list[dict[str, float]] = []
    edges = np.linspace(0.0, 1.0, bins + 1)
    for low, high in zip(edges[:-1], edges[1:]):
        mask = (confidence >= low) & (confidence < high if high < 1.0 else confidence <= high)
        if not mask.any():
            continue
        output.append(
            {
                "low": float(low),
                "high": float(high),
                "count": int(mask.sum()),
                "mean_confidence": float(confidence[mask].mean()),
                "empirical_accuracy": float(correct[mask].mean()),
            }
        )
    return output
