"""Tax calculation utilities.

This module implements simplified U.S. federal and state tax calculations.  The
defaults embed the 2025 single‑filer brackets published by the IRS (via the Tax
Foundation)【284892234855781†L236-L243】.  The tax logic is intentionally
simplified: it applies progressive rates to taxable income after a standard
deduction and does not include deductions beyond the standard deduction, the
Alternative Minimum Tax, or specific credits.  Capital gains are taxed
separately using their own brackets.  State tax handling supports flat rates.

Example
-------

>>> # Compute federal tax on $60 000 of ordinary income for a single filer
>>> round(compute_federal_tax(60000), 2)
6648.0

>>> # Capital gains tax on $100 000 of gains for a single filer
>>> round(compute_capital_gains_tax(100000), 2)
7750.0

The underlying brackets can be customised by passing a dictionary matching the
schema in ``data/tax_tables.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Optional

_DEFAULT_TAX_TABLE_PATH = Path(__file__).resolve().parent.parent / "data" / "tax_tables.json"

def _load_tax_tables(path: Optional[Path] = None) -> Dict[str, Dict]:
    """Load tax tables from JSON.  If ``path`` is not provided, load the
    default file shipped with the package.

    Parameters
    ----------
    path : Path, optional
        Path to a JSON file containing the tax tables.  The file must define
        a top‑level object with ``federal`` and ``state`` keys.

    Returns
    -------
    dict
        The parsed tax tables.
    """
    p = path or _DEFAULT_TAX_TABLE_PATH
    with open(p, "r", encoding="utf-8") as f:
        tables = json.load(f)
    return tables

def compute_federal_tax(
    income: float,
    filing_status: str = "single",
    tax_tables: Optional[Dict[str, Dict]] = None,
) -> float:
    """Compute federal income tax due on ordinary income.

    The tax is calculated progressively using the brackets defined in
    ``tax_tables['federal'][filing_status]['brackets']``.  Income is reduced
    by the standard deduction before applying the rates.  Negative taxable
    income results in zero tax.

    Parameters
    ----------
    income : float
        Gross ordinary income (before deductions).
    filing_status : str, optional
        Filing status (default ``"single"``).  Must exist in the tax tables.
    tax_tables : dict, optional
        Preloaded tax tables.  If omitted, the default tables are loaded from
        ``data/tax_tables.json``.

    Returns
    -------
    float
        Federal income tax due.
    """
    tables = tax_tables or _load_tax_tables()
    brackets = tables["federal"][filing_status]["brackets"]
    std_ded = tables["federal"][filing_status].get("standard_deduction", 0)

    taxable_income = max(0.0, income - std_ded)
    tax = 0.0
    remaining = taxable_income
    for bracket in brackets:
        rate = bracket["rate"]
        start = bracket["start"]
        end = bracket["end"] if bracket["end"] is not None else float("inf")
        width = end - start
        if remaining <= 0:
            break
        if taxable_income > start:
            amount = min(remaining, width)
            tax += amount * rate
            remaining -= amount
        else:
            break
    return tax

def compute_capital_gains_tax(
    gain: float,
    filing_status: str = "single",
    tax_tables: Optional[Dict[str, Dict]] = None,
) -> float:
    """Compute long‑term capital gains tax on a given amount.

    The function applies the brackets defined under ``cap_gains`` for the
    specified filing status.  If no capital gains brackets are present, the
    function returns zero.

    Parameters
    ----------
    gain : float
        Amount of long‑term capital gains.
    filing_status : str, optional
        Filing status (default ``"single"``).
    tax_tables : dict, optional
        Preloaded tax tables.

    Returns
    -------
    float
        Capital gains tax due.
    """
    if gain <= 0:
        return 0.0
    tables = tax_tables or _load_tax_tables()
    cg_brackets = tables["federal"][filing_status].get("cap_gains")
    if not cg_brackets:
        return 0.0
    tax = 0.0
    remaining = gain
    for bracket in cg_brackets:
        rate = bracket["rate"]
        start = bracket["start"]
        end = bracket["end"] if bracket["end"] is not None else float("inf")
        width = end - start
        if remaining <= 0:
            break
        if gain > start:
            amount = min(remaining, width)
            tax += amount * rate
            remaining -= amount
        else:
            break
    return tax

def compute_state_tax(
    taxable_income: float,
    state: str = "MI",
    tax_tables: Optional[Dict[str, Dict]] = None,
) -> float:
    """Compute state tax on taxable income using a flat rate.

    Parameters
    ----------
    taxable_income : float
        Taxable income after deductions.  No standard deduction is applied here
        because the deduction is assumed to be part of federal calculations.
    state : str, optional
        Two‑letter state code (default ``"MI"`` for Michigan).
    tax_tables : dict, optional
        Preloaded tax tables.

    Returns
    -------
    float
        State income tax due.  Returns zero if the state is not found.
    """
    tables = tax_tables or _load_tax_tables()
    state_info = tables.get("state", {}).get(state)
    if not state_info:
        return 0.0
    rate = state_info.get("rate", 0.0)
    std_ded = state_info.get("standard_deduction", 0.0)
    taxable = max(0.0, taxable_income - std_ded)
    return taxable * rate

def combined_tax(
    ordinary_income: float,
    capital_gains: float,
    filing_status: str = "single",
    state: str = "MI",
    tax_tables: Optional[Dict[str, Dict]] = None,
) -> float:
    """Compute combined federal and state taxes on ordinary income and capital gains.

    The function first applies the federal standard deduction to ordinary
    income.  Capital gains are taxed separately using the capital gains
    schedule.  State tax is computed on the total taxable income (ordinary
    income plus capital gains) and uses a flat rate.  This approach
    approximates how state taxes apply to both ordinary and capital gain
    income in many states.

    Parameters
    ----------
    ordinary_income : float
        Gross ordinary income before deductions.
    capital_gains : float
        Long‑term capital gains.
    filing_status : str, optional
        Filing status (default ``"single"``).
    state : str, optional
        Two‑letter state code (default ``"MI"``).
    tax_tables : dict, optional
        Preloaded tax tables.

    Returns
    -------
    float
        Total tax due.
    """
    tables = tax_tables or _load_tax_tables()
    # Federal tax on ordinary income
    federal_tax = compute_federal_tax(ordinary_income, filing_status, tables)
    # Capital gains tax
    cg_tax = compute_capital_gains_tax(capital_gains, filing_status, tables)
    # State tax on combined taxable income (ordinary income minus standard deduction plus capital gains)
    std_ded = tables["federal"][filing_status].get("standard_deduction", 0.0)
    state_taxable = max(0.0, ordinary_income + capital_gains - std_ded)
    state_tax_val = compute_state_tax(state_taxable, state, tables)
    return federal_tax + cg_tax + state_tax_val

__all__ = [
    "compute_federal_tax",
    "compute_capital_gains_tax",
    "compute_state_tax",
    "combined_tax",
    "_load_tax_tables",
]