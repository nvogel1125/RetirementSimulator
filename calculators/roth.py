"""Roth conversion helper functions.

Roth conversions involve moving money from a tax‑deferred account (such as a
traditional IRA or 401(k)) to a Roth account.  The amount converted becomes
ordinary income in the year of conversion and is subject to income tax.  This
module implements basic mechanics for a conversion and a simple conversion
strategy.

Example
-------

>>> # Convert $10k from a pre‑tax account with $100k and pay taxes from taxable funds
>>> apply_conversion(100_000, 0, amount=10_000, tax_rate=0.22)
({'pre_tax': 90000.0, 'roth': 10000.0}, 2200.0)
"""

from __future__ import annotations

from typing import Dict, Tuple


def apply_conversion(
    pre_tax_balance: float,
    roth_balance: float,
    amount: float,
    tax_rate: float,
    pay_tax_from_taxable: bool = True,
) -> Tuple[Dict[str, float], float]:
    """Execute a single Roth conversion.

    Parameters
    ----------
    pre_tax_balance : float
        Current balance of the tax‑deferred account from which funds are converted.
    roth_balance : float
        Current Roth balance.
    amount : float
        Amount to convert.  If greater than the pre‑tax balance, the entire
        pre‑tax balance is converted.
    tax_rate : float
        Effective marginal tax rate applied to the converted amount.
    pay_tax_from_taxable : bool, optional
        If True (default), the tax due is assumed to be paid from separate
        taxable savings and does not reduce the converted amount.  If False,
        taxes are withheld from the conversion itself.

    Returns
    -------
    tuple
        A tuple ``(balances, tax_due)`` where ``balances`` is a dict with
        updated ``pre_tax`` and ``roth`` balances and ``tax_due`` is the tax
        liability created by the conversion.
    """
    if amount <= 0 or pre_tax_balance <= 0:
        return {"pre_tax": pre_tax_balance, "roth": roth_balance}, 0.0
    conv_amount = min(amount, pre_tax_balance)
    tax_due = conv_amount * tax_rate
    if not pay_tax_from_taxable:
        # Reduce the converted amount by tax withheld
        net_amount = conv_amount - tax_due
    else:
        net_amount = conv_amount
    # Update balances
    new_pre_tax = pre_tax_balance - conv_amount
    new_roth = roth_balance + max(net_amount, 0.0)
    return {"pre_tax": new_pre_tax, "roth": new_roth}, tax_due


def simple_roth_strategy(
    pre_tax_balance: float,
    roth_balance: float,
    annual_cap: float,
    years: int,
    tax_rate: float,
    pay_tax_from_taxable: bool = True,
) -> Tuple[Dict[str, float], float]:
    """Apply a naive Roth conversion strategy over several years.

    Converts up to ``annual_cap`` each year until ``years`` is exhausted or
    there is no remaining pre‑tax balance.  The function assumes the same
    marginal tax rate every year and does not consider bracket ceilings.  It is
    intended as a demonstration and not as an optimiser.

    Parameters
    ----------
    pre_tax_balance : float
        Starting tax‑deferred balance.
    roth_balance : float
        Starting Roth balance.
    annual_cap : float
        Maximum amount to convert each year.
    years : int
        Number of years to apply conversions.
    tax_rate : float
        Effective marginal tax rate applied to the converted amount.
    pay_tax_from_taxable : bool, optional
        Whether taxes are paid from a separate taxable account.

    Returns
    -------
    tuple
        (``balances``, ``total_tax``) after all conversions.
    """
    total_tax = 0.0
    pre = pre_tax_balance
    roth = roth_balance
    for _ in range(max(0, years)):
        if pre <= 0:
            break
        balances, tax_due = apply_conversion(
            pre, roth, amount=annual_cap, tax_rate=tax_rate, pay_tax_from_taxable=pay_tax_from_taxable
        )
        pre, roth = balances["pre_tax"], balances["roth"]
        total_tax += tax_due
    return {"pre_tax": pre, "roth": roth}, total_tax


__all__ = ["apply_conversion", "simple_roth_strategy"]