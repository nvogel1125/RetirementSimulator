import pytest
import numpy as np
from retirement_planner.calculators import monte_carlo


def _fv_plan(acct_key: str):
    accounts = {
        'pre_tax': {'balance':0.0,'contribution':0.0,'mean_return':0.07,'stdev_return':0.0,'withdrawal_tax_rate':0.25},
        'roth':     {'balance':0.0,'contribution':0.0,'mean_return':0.07,'stdev_return':0.0},
        'taxable':  {'balance':0.0,'contribution':0.0,'mean_return':0.07,'stdev_return':0.0},
        'cash':     {'balance':0.0}
    }
    accounts[acct_key]['balance'] = 1000.0
    accounts[acct_key]['contribution'] = 1000.0
    return {
        'current_age':22,
        'retire_age':60,
        'end_age':59,
        'accounts': accounts,
        'income':{'salary':1000.0,'salary_growth':0.0},
        'expenses':{'baseline':0.0},
    }


@pytest.mark.parametrize('acct', ['pre_tax','roth','taxable'])
def test_future_value_returns(acct):
    plan = _fv_plan(acct)
    res = monte_carlo.simulate_path(plan, np.random.default_rng(0))
    assert res['acct_series'][acct][-1] == pytest.approx(185640.2916, abs=1e-2)
