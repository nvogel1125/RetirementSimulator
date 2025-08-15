from retirement_planner.components.insights import generate_insights


def test_insights_rule_based():
    results = {
        "success_probability": 0.9,
        "median_terminal": 1000000,
        "ages": [65, 90],
    }
    text = generate_insights(results).lower()
    assert "high chance of success" in text

    results_low = {
        "success_probability": 0.5,
        "median_terminal": 0,
        "ages": [65, 90],
    }
    text_low = generate_insights(results_low).lower()
    assert "plan may be at risk" in text_low
