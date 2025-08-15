"""Required Minimum Distribution (RMD) calculator.

This module implements the rules for determining when RMDs must begin and
calculating the annual RMD using the IRS Uniform Lifetime Table.  The SECURE Act
2.0 increased the RMD start age from 72 to 73 beginning in 2023, and to 75
beginning in 2033.  According to Boldin’s summary of the changes【990996736051385†L120-L160】:

* Individuals born between 1951 and 1959 must start RMDs at age 73.
* Individuals born in 1960 or later will start at age 75.

The Uniform Lifetime Table provides distribution periods used to compute RMDs.
This implementation includes the 2022 table effective for distributions after
2021.

Example
-------

>>> # Person born in 1955 (between 1951–1959) starts RMD at age 73
>>> rmd_start_age(1955)
73

>>> # Compute RMD for a 73‑year‑old with $100k in a traditional IRA at the end of the prior year
>>> round(compute_rmd(balance=100000, age=73), 2)
3773.58
"""

from __future__ import annotations

from typing import Dict


def rmd_start_age(birth_year: int) -> int:
    """Determine the age at which RMDs must begin based on year of birth.

    Parameters
    ----------
    birth_year : int
        Birth year of the account owner.

    Returns
    -------
    int
        The age when RMDs must commence.
    """
    # According to SECURE Act 2.0 rules【990996736051385†L120-L160】
    if birth_year <= 1950:
        # Individuals born before 1951 have already begun RMDs under earlier rules.
        return 72
    elif 1951 <= birth_year <= 1959:
        return 73
    else:
        return 75


def _uniform_lifetime_table() -> Dict[int, float]:
    """Return the IRS Uniform Lifetime Table (distribution periods).

    The table is based on the 2022 update effective for distributions after
    January 1 2022.  For each age from 72–120 the table provides the
    distribution period (life expectancy factor).  Source: IRS Publication 590‑B
    (2024) and summarised values used widely in financial planning tools.

    Returns
    -------
    dict
        Mapping from age to distribution period.
    """
    return {
        72: 27.4,
        73: 26.5,
        74: 25.5,
        75: 24.6,
        76: 23.7,
        77: 22.9,
        78: 22.0,
        79: 21.1,
        80: 20.2,
        81: 19.4,
        82: 18.5,
        83: 17.7,
        84: 16.8,
        85: 16.0,
        86: 15.2,
        87: 14.4,
        88: 13.7,
        89: 12.9,
        90: 12.2,
        91: 11.5,
        92: 10.8,
        93: 10.1,
        94: 9.5,
        95: 8.9,
        96: 8.4,
        97: 7.8,
        98: 7.3,
        99: 6.8,
        100: 6.4,
        101: 6.0,
        102: 5.6,
        103: 5.2,
        104: 4.9,
        105: 4.6,
        106: 4.3,
        107: 4.1,
        108: 3.9,
        109: 3.7,
        110: 3.5,
        111: 3.4,
        112: 3.3,
        113: 3.1,
        114: 3.0,
        115: 2.9,
        116: 2.8,
        117: 2.7,
        118: 2.5,
        119: 2.3,
        120: 2.0,
    }


def compute_rmd(balance: float, age: int) -> float:
    """Compute the Required Minimum Distribution for a given age and balance.

    Parameters
    ----------
    balance : float
        The retirement account balance on December 31 of the prior year.
    age : int
        Age of the account owner in the distribution year.

    Returns
    -------
    float
        The RMD amount.  Returns zero if the age is below the first age in
        the table or the balance is non‑positive.
    """
    if balance <= 0:
        return 0.0
    table = _uniform_lifetime_table()
    if age not in table:
        return 0.0
    period = table[age]
    return balance / period


__all__ = ["rmd_start_age", "compute_rmd"]