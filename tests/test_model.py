import pandas as pd

from wcprediction.model import train_from_frame


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
