"""Tests for the Roth conversion mechanics."""

import math

from retirement_planner.calculators import roth


def test_apply_conversion_taxable():
    """Converting from a pre‑tax account increases the Roth by the full amount when taxes are paid from taxable funds."""
    balances, tax_due = roth.apply_conversion(pre_tax_balance=100000, roth_balance=0, amount=10000, tax_rate=0.22, pay_tax_from_taxable=True)
    assert math.isclose(balances["pre_tax"], 90000.0, rel_tol=1e-6)
    assert math.isclose(balances["roth"], 10000.0, rel_tol=1e-6)
    assert math.isclose(tax_due, 2200.0, rel_tol=1e-6)


def test_apply_conversion_withheld():
    """When taxes are withheld from the conversion, the Roth receives the net amount."""
    balances, tax_due = roth.apply_conversion(pre_tax_balance=50000, roth_balance=0, amount=10000, tax_rate=0.20, pay_tax_from_taxable=False)
    # 20% withheld; net converted 8000
    assert math.isclose(balances["pre_tax"], 40000.0, rel_tol=1e-6)
    assert math.isclose(balances["roth"], 8000.0, rel_tol=1e-6)
    assert math.isclose(tax_due, 2000.0, rel_tol=1e-6)


import numpy as np
from retirement_planner.calculators import monte_carlo

def test_roth_ira_max_schedule():
    sched = roth.roth_ira_max_schedule(49, 52)
    assert sched[49] == 7000.0
    assert sched[50] == 8000.0
    assert sched[51] == 8500.0

def test_roth_ira_schedule_used_in_simulation():
    schedule = roth.roth_ira_max_schedule(49, 52)
    plan = {
        "current_age": 49,
        "retire_age": 52,
        "end_age": 52,
        "accounts": {
            "pre_tax_401k": {"balance": 0.0, "contribution": 0.0, "mean_return": 0.0, "stdev_return": 0.0},
            "pre_tax_ira": {"balance": 0.0, "contribution": 0.0, "mean_return": 0.0, "stdev_return": 0.0},
            "roth_401k": {"balance": 0.0, "contribution": 0.0, "mean_return": 0.0, "stdev_return": 0.0},
            "roth_ira": {"balance": 0.0, "contribution": 0.0, "contribution_schedule": schedule, "mean_return": 0.0, "stdev_return": 0.0},
            "taxable": {"balance": 0.0, "contribution": 0.0, "mean_return": 0.0, "stdev_return": 0.0},
            "cash": {"balance": 0.0},
        },
        "income": {"salary": 100000.0, "salary_growth": 0.0, "roth_income_limit": float('inf')},
        "expenses": {"baseline": 0.0},
        "assumptions": {"returns_correlated": False},
        "roth_conversion": {},
        "withdrawal_strategy": "standard",
        "birth_year": 1975,
    }
    res = monte_carlo.simulate_path(plan, np.random.default_rng(0))
    accts = res["acct_series"]["roth"]
    assert accts[0] == schedule[49]
    assert accts[1] == schedule[49] + schedule[50]
    assert accts[2] == schedule[49] + schedule[50] + schedule[51]
