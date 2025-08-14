"""Tests for the RMD calculator functions."""

import math

from retirement_planner.calculators import rmd


def test_rmd_start_age():
    """RMD start age changes based on birth year per SECURE Act rules【990996736051385†L120-L160】."""
    assert rmd.rmd_start_age(1950) == 72
    assert rmd.rmd_start_age(1955) == 73
    assert rmd.rmd_start_age(1965) == 75


def test_compute_rmd():
    """Compute RMD using the 2022 Uniform Lifetime Table (balance / period)."""
    amt = rmd.compute_rmd(100000, 73)  # period 26.5
    assert math.isclose(amt, 100000 / 26.5, rel_tol=1e-6)
