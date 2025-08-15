"""Tests covering contribution and withdrawal logic revisions."""

from retirement_planner.calculators import monte_carlo
import numpy as np
from retirement_planner.components import charts


def _base_plan():
    return {
        "current_age": 30,
        "retire_age": 65,
        "end_age": 30,
        "accounts": {
            "pre_tax": {
                "balance": 0.0,
                "contribution": 20000.0,
                "mean_return": 0.0,
                "stdev_return": 0.0,
                "withdrawal_tax_rate": 0.25,
            },
            "roth": {
                "balance": 0.0,
                "contribution": 6000.0,
                "mean_return": 0.0,
                "stdev_return": 0.0,
            },
            "taxable": {
                "balance": 0.0,
                "contribution": 5000.0,
                "mean_return": 0.0,
                "stdev_return": 0.0,
            },
            "cash": {"balance": 0.0},
        },
        "income": {"salary": 50000.0, "salary_growth": 0.0, "roth_income_limit": 100000.0},
        "expenses": {"baseline": 30000.0},
    }


def test_contributions_capped_by_income():
    plan = _base_plan()
    res = monte_carlo.simulate_path(plan, np.random.default_rng(0))
    accts = res["acct_series"]
    assert accts["pre_tax"][0] == 20000.0
    assert accts["roth"][0] == 0.0
    assert accts["taxable"][0] == 0.0


def test_partial_contribution_when_insufficient_income():
    plan = _base_plan()
    plan["income"]["salary"] = 40000.0
    res = monte_carlo.simulate_path(plan, np.random.default_rng(0))
    accts = res["acct_series"]
    assert accts["pre_tax"][0] == 10000.0
    assert accts["roth"][0] == 0.0


def test_roth_income_limit_blocks_contribution():
    plan = _base_plan()
    plan["income"]["salary"] = 60000.0
    plan["income"]["roth_income_limit"] = 55000.0
    res = monte_carlo.simulate_path(plan, np.random.default_rng(0))
    accts = res["acct_series"]
    # 20k to pre_tax, 5k to taxable, remainder cash
    assert accts["pre_tax"][0] == 20000.0
    assert accts["roth"][0] == 0.0
    assert accts["taxable"][0] == 5000.0
    assert res["ledger"]["cash"][0] == 5000.0


def test_max_out_roth_with_growing_limit():
    plan = _base_plan()
    plan.update({"end_age": 31})
    plan["accounts"]["pre_tax"]["contribution"] = 0.0
    plan["accounts"]["roth"].update({
        "contribution": 0.0,
        "max_out": True,
        "annual_limit": 6000.0,
        "limit_growth": 0.10,
    })
    plan["accounts"]["taxable"]["contribution"] = 0.0
    res = monte_carlo.simulate_path(plan, np.random.default_rng(0))
    accts = res["acct_series"]["roth"].tolist()
    assert accts[0] == 6000.0
    assert accts[1] == 12600.0  # 6000 + 6600


def test_deficit_draws_from_taxable_then_pretax_with_tax():
    plan = _base_plan()
    plan["income"]["salary"] = 20000.0
    plan["accounts"]["taxable"]["balance"] = 7000.0
    plan["accounts"]["pre_tax"]["balance"] = 5000.0
    plan["accounts"]["pre_tax"]["contribution"] = 0.0
    plan["accounts"]["roth"]["contribution"] = 0.0
    plan["accounts"]["taxable"]["contribution"] = 0.0
    res = monte_carlo.simulate_path(plan, np.random.default_rng(0))
    ledger = res["ledger"]
    # Withdrawals: 7000 taxable + 4000 gross from pre_tax (1000 tax)
    assert ledger["withdrawals"][0] == 11000.0
    assert ledger["taxes"][0] == 1000.0
    accts = res["acct_series"]
    assert accts["pre_tax"][0] == 1000.0
    assert accts["taxable"][0] == 0.0


def test_fan_chart_handles_short_sequences():
    ages = [30, 31, 32]
    fig = charts.fan_chart(ages, [1, 2], [1, 2, 3], [3, 4])
    assert len(fig.data) == 3
    for trace in fig.data:
        assert len(trace.x) == 3

