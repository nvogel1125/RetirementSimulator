"""Tests for the simplified Social Security benefit estimator."""

import math

from retirement_planner.calculators import social_security as ss
from retirement_planner.calculators import monte_carlo
import numpy as np


def test_early_claiming_reduction():
    """Claiming before FRA reduces benefits by approximately 7% per year."""
    # PIA is $2000/month, FRA is 67, claim at 65 (two years early)
    benefit = ss.social_security_benefit(PIA=2000, start_age=65)
    # Our implementation reduces 7% per year: 2000*0.86*12 = 20640
    assert math.isclose(benefit, 2000 * 0.86 * 12, rel_tol=1e-4)


def test_delayed_claiming_credit():
    """Claiming after FRA increases benefits by 8% per year up to age 70."""
    benefit = ss.social_security_benefit(PIA=2000, start_age=70)
    # 3 years after FRA: 2000 * 1.24 * 12
    assert math.isclose(benefit, 2000 * 1.24 * 12, rel_tol=1e-4)


def test_survivor_benefit():
    """Survivor benefit returns the larger of two benefits."""
    # Spouse A: PIA 1500, start age 67; Spouse B: PIA 1000, start age 67
    # The survivor should receive 1500*12
    survivor = ss.social_security_benefit(PIA=1500, start_age=67, spouse_PIA=1000, spouse_start_age=67, survivor=True)
    assert math.isclose(survivor, 1500 * 12, rel_tol=1e-4)


def test_estimate_pia_constant_salary():
    """Estimating PIA from a flat salary reproduces the formula."""
    pia = ss.estimate_pia(current_age=30, retire_age=67, salary=60000, salary_growth=0.0)
    assert math.isclose(pia, 2280.92, rel_tol=1e-4)


def test_benefit_flow_in_monte_carlo():
    plan = {
        'current_age':60,
        'retire_age':65,
        'end_age':66,
        'accounts': {
            'pre_tax': {'balance':0.0,'contribution':0.0,'mean_return':0.0,'stdev_return':0.0,'withdrawal_tax_rate':0.0},
            'roth': {'balance':0.0,'contribution':0.0,'mean_return':0.0,'stdev_return':0.0},
            'taxable': {'balance':0.0,'contribution':0.0,'mean_return':0.0,'stdev_return':0.0},
            'cash': {'balance':0.0}
        },
        'income': {'salary':0.0,'salary_growth':0.0},
        'expenses': {'baseline':0.0},
        'social_security': {'PIA':2000.0,'claim_age':62}
    }
    res = monte_carlo.simulate_path(plan, np.random.default_rng(0))
    idx = res['ages'].index(62)
    expected = ss.social_security_benefit(PIA=2000.0, start_age=62)
    assert res['ledger']['income'][idx] == expected
