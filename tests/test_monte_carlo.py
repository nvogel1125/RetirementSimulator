"""Tests for the Monte Carlo simulation engine."""

from retirement_planner.calculators import monte_carlo


def _build_simple_plan() -> dict:
    return {
        "current_age": 60,
        "retire_age": 65,
        "end_age": 70,
        "birth_year": 1965,
        "accounts": {
            "pre_tax": {
                "balance": 100000.0,
                "contribution": 0.0,
                "mean_return": 0.0,
                "stdev_return": 0.0,
            },
            "roth": {
                "balance": 0.0,
                "contribution": 0.0,
                "mean_return": 0.0,
                "stdev_return": 0.0,
            },
            "taxable": {
                "balance": 0.0,
                "contribution": 0.0,
                "mean_return": 0.0,
                "stdev_return": 0.0,
            },
            "cash": {"balance": 0.0},
        },
        "income": {
            "salary": 0.0,
            "part_time": 0.0,
            "rental": 0.0,
            "pensions": [],
        },
        "expenses": {"baseline": 0.0},
        "assumptions": {"returns_correlated": True},
        "social_security": {"PIA": 0.0, "claim_age": 67},
        "roth_conversion": {"annual_cap": 0.0, "start_age": 60, "end_age": 60, "tax_rate": 0.0, "pay_tax_from_taxable": True},
        "state": "MI",
        "filing_status": "single",
    }


def test_repeatability_with_seed():
    """Simulations should be repeatable when the same seed is provided."""
    plan = _build_simple_plan()
    result1 = monte_carlo.simulate(plan, n_paths=10, seed=12345)
    result2 = monte_carlo.simulate(plan, n_paths=10, seed=12345)
    assert result1["success_probability"] == result2["success_probability"]
    assert result1["percentiles"] == result2["percentiles"]
