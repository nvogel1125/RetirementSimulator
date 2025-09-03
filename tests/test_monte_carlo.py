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


def test_success_probability_requires_positive_terminal():
    """A plan ending with zero net worth should count as failure."""
    plan = _build_simple_plan()
    # remove all starting assets so every path ends at 0
    plan["accounts"]["pre_tax"]["balance"] = 0.0
    result = monte_carlo.simulate(plan, n_paths=5, seed=1)
    assert result["success_probability"] == 0.0


def test_max_spending_restores_plan_and_finds_cap():
    """Binary search should find the max sustainable baseline expense."""
    plan = _build_simple_plan()
    max_spend = monte_carlo.max_spending(plan, target_success=1.0, n_paths=1, seed=1, tol=1.0)
    # With expenses withdrawn twice in retirement years, the sustainable
    # spending level is roughly 100k / 17 ≈ 5882.
    assert abs(max_spend - 5882.0) <= 100.0
    assert plan["expenses"]["baseline"] == 0.0
