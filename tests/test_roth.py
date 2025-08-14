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
