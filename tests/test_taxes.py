"""Unit tests for the taxes module.

These tests verify that federal and state tax calculations using the
simplified tax tables produce expected results.  Values are based on
the 2025 single‑filer brackets from the Tax Foundation article【284892234855781†L236-L243】.
"""

import math

from retirement_planner.calculators import taxes as tax_calc


def test_federal_tax_example():
    """Federal tax on $60k of ordinary income for a single filer should match the example."""
    tax = tax_calc.compute_federal_tax(60000)
    # Example in module docstring shows 6648.0
    assert math.isclose(tax, 6648.0, rel_tol=1e-4)


def test_capital_gains_tax_example():
    """Capital gains tax on $100k of gains should match the example."""
    tax = tax_calc.compute_capital_gains_tax(100000)
    assert math.isclose(tax, 7750.0, rel_tol=1e-4)


def test_state_tax_flat_rate():
    """State tax should apply a flat rate from the table (4% in Michigan)."""
    tax = tax_calc.compute_state_tax(100000, state="MI")
    assert math.isclose(tax, 4000.0, rel_tol=1e-4)
