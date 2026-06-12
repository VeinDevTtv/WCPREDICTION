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


def test_rolling_features_do_not_use_current_match_result() -> None:
    matches = pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2020-01-01"),
                "home_team": "A",
                "away_team": "B",
                "home_score": 3,
                "away_score": 0,
                "tournament": "Friendly",
                "country": "A",
                "neutral": False,
            },
            {
                "date": pd.Timestamp("2020-01-10"),
                "home_team": "A",
                "away_team": "C",
                "home_score": 0,
                "away_score": 1,
                "tournament": "Friendly",
                "country": "D",
                "neutral": True,
            },
        ]
    )
    features, _, _ = FeatureBuilder(EloSystem()).build_training_frame(matches)
    assert features.loc[0, "home_recent_points"] == 0
    assert features.loc[1, "home_recent_points"] == 3
    assert features.loc[1, "home_recent_gd"] == 3
    assert features.loc[1, "home_days_since_match"] == 9
    assert features.loc[0, "home_country_match"] == 1
    assert features.loc[1, "neutral_country_match"] == 1
