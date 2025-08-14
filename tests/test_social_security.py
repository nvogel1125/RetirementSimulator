"""Tests for the simplified Social Security benefit estimator."""

import math

from retirement_planner.calculators import social_security as ss


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
