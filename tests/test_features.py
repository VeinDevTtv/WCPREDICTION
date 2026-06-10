import pandas as pd

from wcprediction.elo import EloSystem
from wcprediction.features import FeatureBuilder


def test_feature_generation_uses_pre_match_ratings() -> None:
    matches = pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2020-01-01"),
                "home_team": "A",
                "away_team": "B",
                "home_score": 3,
                "away_score": 0,
                "tournament": "Friendly",
                "neutral": True,
            }
        ]
    )
    features, labels, elo = FeatureBuilder(EloSystem()).build_training_frame(matches)
    assert features.loc[0, "home_rating"] == 1500
    assert features.loc[0, "away_rating"] == 1500
    assert labels.tolist() == [0]
    assert elo.ratings["A"] > 1500
