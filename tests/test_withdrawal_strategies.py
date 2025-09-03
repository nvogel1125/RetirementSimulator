import numpy as np
import pytest
from retirement_planner.calculators import monte_carlo, rmd
import numpy as np
import pytest


def _base_plan():
    return {
        "current_age": 65,
        "retire_age": 65,
        "end_age": 65,
        "birth_year": 1960,
        "accounts": {
            "pre_tax": {"balance": 50000.0, "withdrawal_tax_rate": 0.2, "mean_return": 0.0, "stdev_return": 0.0},
            "roth": {"balance": 0.0, "mean_return": 0.0, "stdev_return": 0.0},
            "taxable": {"balance": 50000.0, "mean_return": 0.0, "stdev_return": 0.0},
            "cash": {"balance": 0.0},
        },
        "income": {"salary": 0.0},
        "expenses": {"baseline": 10000.0},
        "assumptions": {"returns_correlated": True},
    }


def test_standard_vs_proportional():
    plan = _base_plan()
    plan["withdrawal_strategy"] = "standard"
    res_std = monte_carlo.simulate_path(plan, np.random.default_rng(0))
    taxable_std = res_std["acct_series"]["taxable"][0]
    pre_std = res_std["acct_series"]["pre_tax"][0]
    assert taxable_std == pytest.approx(27500.0, rel=1e-3)
    assert pre_std == pytest.approx(50000.0, rel=1e-3)

    plan["withdrawal_strategy"] = "proportional"
    res_prop = monte_carlo.simulate_path(plan, np.random.default_rng(0))
    taxable_prop = res_prop["acct_series"]["taxable"][0]
    pre_prop = res_prop["acct_series"]["pre_tax"][0]
    assert taxable_prop == pytest.approx(34444.4444, rel=1e-3)
    assert pre_prop == pytest.approx(43055.5556, rel=1e-3)


def test_tax_bracket_strategy():
    plan = _base_plan()
    plan["expenses"]["baseline"] = 20000.0
    plan["withdrawal_strategy"] = "tax_bracket"
    plan["withdrawal_bracket"] = {"pre_tax_limit": 10000.0}
    res = monte_carlo.simulate_path(plan, np.random.default_rng(0))
    taxable_end = res["acct_series"]["taxable"][0]
    pre_end = res["acct_series"]["pre_tax"][0]
    assert taxable_end == pytest.approx(15000.0, rel=1e-3)
    assert pre_end == pytest.approx(40000.0, rel=1e-3)


def test_rmd_enforced():
    plan = _base_plan()
    plan.update({"current_age": 75, "end_age": 75})
    plan["expenses"]["baseline"] = 0.0
    plan["accounts"]["cash"]["balance"] = 0.0
    res = monte_carlo.simulate_path(plan, np.random.default_rng(0))
    pre_end = res["acct_series"]["pre_tax"][0]
    cash_end = res["acct_series"]["cash"][0]
    gross_rmd = rmd.compute_rmd(50000.0, 75)
    net_rmd = gross_rmd * (1 - 0.2)
    assert pre_end == pytest.approx(50000.0 - gross_rmd, rel=1e-3)
    assert cash_end == pytest.approx(net_rmd, rel=1e-3)
