import numpy as np
import pytest

from retirement_planner.calculators import monte_carlo


def test_capital_gains_and_state_tax_applied():
    plan = {
        "current_age": 60,
        "retire_age": 120,
        "end_age": 60,
        "state": "MI",
        "filing_status": "single",
        "accounts": {
            "pre_tax": {"balance": 0.0, "contribution": 0.0, "mean_return": 0.0, "stdev_return": 0.0, "withdrawal_tax_rate": 0.0},
            "roth": {"balance": 0.0, "contribution": 0.0, "mean_return": 0.0, "stdev_return": 0.0},
            "taxable": {"balance": 100000.0, "basis": 0.0, "mean_return": 0.0, "stdev_return": 0.0},
            "cash": {"balance": 0.0},
        },
        "income": {"salary": 0.0, "salary_growth": 0.0, "tax_rate": 0.0},
        "expenses": {"baseline": 50000.0},
    }

    res = monte_carlo.simulate_path(plan, np.random.default_rng(0))
    ledger = res["ledger"]

    # Expected taxes: capital gains tax on $50k gain (446.25) + MI state tax (~2017.85)
    assert ledger["taxes"][0] == pytest.approx(2464.1, rel=1e-3)
    # Remaining taxable balance after covering expenses and taxes
    assert ledger["taxable"][0] == pytest.approx(47535.9, rel=1e-3)

