"""Unit tests for the taxes module.

These tests verify that federal and state tax calculations using the
embedded tax tables produce expected results.  Values use the 2024 IRS
brackets for multiple filing statuses and a mix of flat and progressive
state systems.
"""

import math

from retirement_planner.calculators import taxes as tax_calc


def test_federal_tax_example():
    """Federal tax on $60k of ordinary income for a single filer (2024)."""
    tax = tax_calc.compute_federal_tax(60000, year=2024)
    assert math.isclose(tax, 5216.0, rel_tol=1e-4)


def test_federal_married_joint():
    """Married filing jointly should use the wider brackets."""
    tax = tax_calc.compute_federal_tax(60000, filing_status="married_joint", year=2024)
    assert math.isclose(tax, 3232.0, rel_tol=1e-4)


def test_capital_gains_tax_example():
    """Capital gains tax on $100k of gains for a single filer (2024)."""
    tax = tax_calc.compute_capital_gains_tax(100000, year=2024)
    assert math.isclose(tax, 7946.25, rel_tol=1e-4)


def test_state_tax_flat_rate():
    """State tax should apply a flat rate from the table (4% in Michigan)."""
    tax = tax_calc.compute_state_tax(100000, state="MI", year=2024)
    assert math.isclose(tax, 4000.0, rel_tol=1e-4)


def test_state_tax_progressive():
    """California uses progressive brackets; verify against 2024 table."""
    tax = tax_calc.compute_state_tax(100000, state="CA", filing_status="single", year=2024)
    assert math.isclose(tax, 5813.469, rel_tol=1e-4)
