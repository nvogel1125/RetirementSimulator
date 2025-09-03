from retirement_planner.calculators import monte_carlo
import numpy as np
import pytest


def test_income_tax_applied_to_salary():
    plan = {
        "current_age": 40,
        "retire_age": 41,
        "end_age": 40,
        "accounts": {
            "pre_tax": {
                "balance": 0.0,
                "contribution": 0.0,
                "mean_return": 0.0,
                "stdev_return": 0.0,
                "withdrawal_tax_rate": 0.20,
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
        "income": {"salary": 100000.0, "salary_growth": 0.0, "tax_rate": 0.20},
        "expenses": {"baseline": 0.0},
    }
    res = monte_carlo.simulate_path(plan, np.random.default_rng(0))
    ledger = res["ledger"]
    assert ledger["taxes"][0] == pytest.approx(20000.0)
    assert ledger["cash"][0] == pytest.approx(80000.0)
