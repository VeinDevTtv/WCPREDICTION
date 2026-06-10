from wcprediction.elo import EloSystem, SimpleEloBaseline


def test_elo_update_is_deterministic() -> None:
    first = EloSystem()
    second = EloSystem()
    first.update_match("France", "Brazil", 2, 1, "FIFA World Cup", True)
    second.update_match("France", "Brazil", 2, 1, "FIFA World Cup", True)
    assert first.ratings == second.ratings
    assert first.ratings["France"] > 1500
    assert first.ratings["Brazil"] < 1500


def test_simple_baseline_probabilities_sum_to_one() -> None:
    baseline = SimpleEloBaseline()
    probabilities = baseline.predict("France", "Brazil")
    assert round(sum(probabilities), 12) == 1.0
    assert probabilities[1] == 0.25
