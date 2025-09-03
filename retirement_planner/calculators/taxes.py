"""Tax calculation utilities.

This module implements simplified U.S. federal and state tax calculations.  The
defaults embed IRS data for 2024 with historical tables for 2023.  Federal tables
cover the major filing statuses (single, married filing jointly, married filing
separately and head of household) and include long‑term capital gains brackets.
State tables support both flat and progressive rates and can vary by filing
status.  The logic applies the standard deduction before progressive rates and
omits less common provisions such as the Alternative Minimum Tax or specific
credits.

Example
-------

>>> # Federal tax on $60 000 of ordinary income for a single filer in 2024
>>> round(compute_federal_tax(60000, year=2024), 2)
5216.0

>>> # Capital gains tax on $100 000 of gains for the same filer
>>> round(compute_capital_gains_tax(100000, year=2024), 2)
7946.25

The underlying brackets can be customised by passing a dictionary matching the
schema in ``data/tax_tables.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

_DEFAULT_TAX_TABLE_PATH = Path(__file__).resolve().parent.parent / "data" / "tax_tables.json"


def _load_tax_tables(path: Optional[Path] = None) -> Dict[str, Dict]:
    """Load tax tables from JSON.  If ``path`` is not provided, load the
    default file shipped with the package.

    Parameters
    ----------
    path : Path, optional
        Path to a JSON file containing the tax tables.

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
    year: int = 2024,
    tax_tables: Optional[Dict[str, Dict]] = None,
) -> float:
    """Compute federal income tax due on ordinary income.

    The tax is calculated progressively using the brackets defined under the
    chosen year and filing status.  Income is reduced by the standard deduction
    before applying the rates.
    """
    tables = tax_tables or _load_tax_tables()
    year_tables = tables[str(year)]["federal"]
    brackets = year_tables[filing_status]["brackets"]
    std_ded = year_tables[filing_status].get("standard_deduction", 0)

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
    year: int = 2024,
    tax_tables: Optional[Dict[str, Dict]] = None,
) -> float:
    """Compute long‑term capital gains tax on a given amount."""
    if gain <= 0:
        return 0.0
    tables = tax_tables or _load_tax_tables()
    cg_brackets = tables[str(year)]["federal"][filing_status].get("cap_gains")
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
    filing_status: str = "single",
    year: int = 2024,
    tax_tables: Optional[Dict[str, Dict]] = None,
) -> float:
    """Compute state income tax on ``taxable_income``.

    ``taxable_income`` should already include any federal deductions.  A
    state‑specific standard deduction is applied if present.  The state rules
    may define either a flat rate or progressive brackets.
    """
    tables = tax_tables or _load_tax_tables()
    state_tables = tables[str(year)].get("state", {})
    state_info = state_tables.get(state)
    if not state_info:
        return 0.0

    status_info = state_info.get(filing_status, state_info)
    std_ded = status_info.get("standard_deduction", 0.0)
    taxable = max(0.0, taxable_income - std_ded)

    if "brackets" in status_info:
        tax = 0.0
        remaining = taxable
        for bracket in status_info["brackets"]:
            rate = bracket["rate"]
            start = bracket["start"]
            end = bracket["end"] if bracket["end"] is not None else float("inf")
            width = end - start
            if remaining <= 0:
                break
            if taxable > start:
                amount = min(remaining, width)
                tax += amount * rate
                remaining -= amount
            else:
                break
        return tax

    rate = status_info.get("rate")
    if rate is None:
        return 0.0
    return taxable * rate


def combined_tax(
    ordinary_income: float,
    capital_gains: float,
    filing_status: str = "single",
    state: str = "MI",
    year: int = 2024,
    tax_tables: Optional[Dict[str, Dict]] = None,
) -> float:
    """Compute combined federal and state taxes on income.

    The function applies federal tax to ordinary income, capital gains tax to
    gains and then state tax to the combined taxable income.
    """
    tables = tax_tables or _load_tax_tables()
    federal_tax = compute_federal_tax(ordinary_income, filing_status, year, tables)
    cg_tax = compute_capital_gains_tax(capital_gains, filing_status, year, tables)
    std_ded = tables[str(year)]["federal"][filing_status].get("standard_deduction", 0.0)
    state_taxable = max(0.0, ordinary_income + capital_gains - std_ded)
    state_tax_val = compute_state_tax(state_taxable, state, filing_status, year, tables)
    return federal_tax + cg_tax + state_tax_val


__all__ = [
    "compute_federal_tax",
    "compute_capital_gains_tax",
    "compute_state_tax",
    "combined_tax",
    "_load_tax_tables",
]
