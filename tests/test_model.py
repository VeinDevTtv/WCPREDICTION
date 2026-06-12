import pandas as pd

from wcprediction.model import backtest, shootout_strengths_from_frame, train_from_frame


def test_trained_model_blends_match_probabilities() -> None:
    matches = pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2020-01-01"),
                "home_team": "A",
                "away_team": "B",
                "home_score": 2,
                "away_score": 0,
                "tournament": "Friendly",
                "neutral": True,
            },
            {
                "date": pd.Timestamp("2020-01-02"),
                "home_team": "C",
                "away_team": "D",
                "home_score": 0,
                "away_score": 0,
                "tournament": "Friendly",
                "neutral": True,
            },
            {
                "date": pd.Timestamp("2020-01-03"),
                "home_team": "B",
                "away_team": "C",
                "home_score": 0,
                "away_score": 1,
                "tournament": "Friendly",
                "neutral": True,
            },
            {
                "date": pd.Timestamp("2020-01-04"),
                "home_team": "D",
                "away_team": "A",
                "home_score": 3,
                "away_score": 1,
                "tournament": "Friendly",
                "neutral": True,
            },
        ]
    )
    model = train_from_frame(matches)
    probabilities = model.predict_match("A", "C")
    assert set(probabilities) == {"home_win", "draw", "away_win"}
    assert round(sum(probabilities.values()), 12) == 1.0


def test_shootout_strengths_are_smoothed() -> None:
    shootouts = pd.DataFrame(
        [
            {"date": pd.Timestamp("2020-01-01"), "home_team": "A", "away_team": "B", "winner": "A"},
            {"date": pd.Timestamp("2020-01-02"), "home_team": "A", "away_team": "C", "winner": "C"},
        ]
    )
    strengths = shootout_strengths_from_frame(shootouts)
    assert strengths["A"] == 0.5
    assert strengths["B"] == 1 / 3
    assert strengths["C"] == 2 / 3


def test_backtest_reports_selection_metadata(tmp_path) -> None:
    rows = []
    teams = ["A", "B", "C", "D"]
    for index in range(40):
        home = teams[index % 4]
        away = teams[(index + 1) % 4]
        rows.append(
            {
                "date": f"2020-01-{(index % 28) + 1:02d}" if index < 20 else f"2021-01-{(index % 28) + 1:02d}",
                "home_team": home,
                "away_team": away,
                "home_score": 2 if index % 3 == 0 else 0,
                "away_score": 0 if index % 3 == 0 else 1,
                "tournament": "Friendly",
                "country": "Neutral",
                "neutral": True,
            }
        )
    path = tmp_path / "results.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    report = backtest(path, cutoff="2021-01-01")
    assert "selection" in report
    assert "feature_columns" in report["selection"]
    assert "rolling_windows" in report
