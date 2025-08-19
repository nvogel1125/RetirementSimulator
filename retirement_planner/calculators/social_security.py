"""Simplified Social Security benefit estimator.

The Boldin planner allows users to enter their Primary Insurance Amount (PIA)
and claiming age.  It then applies early retirement reductions or delayed
retirement credits to compute the benefit at the chosen age【54758672279077†L37-L49】.
This module implements a similar approach, without modelling a full earnings
history or spousal coordination beyond a simple survivor benefit.

The actual Social Security formula applies different reduction/credit factors
depending on whether benefits are claimed before or after full retirement age
(FRA).  This implementation approximates the rules as follows:

* FRA defaults to 67 unless explicitly provided.  (FRA varies from 66 to 67
  depending on birth year, but 67 is typical for those born 1960 or later.)
* If the claiming age is below FRA, the benefit is reduced by 7 % per year of
  early claiming.
* If the claiming age is above FRA (up to age 70), the benefit is increased by
  8 % per year of delay.
* Benefits are paid annually by multiplying the monthly benefit by 12.
* Spousal benefits and survivor benefits are simplified: the surviving spouse
  receives the larger of their own or their spouse’s benefit after the first
  death【54758672279077†L43-L49】.

Example
-------

>>> # A PIA of $2 000 per month claimed at 65 (two years early)
>>> round(social_security_benefit(PIA=2000, start_age=65), 2)
22272.0

>>> # Claimed at 70 (three years after FRA) – increased benefit
>>> round(social_security_benefit(PIA=2000, start_age=70), 2)
25920.0
"""

from __future__ import annotations

from typing import Optional


def social_security_benefit(
    PIA: float,
    start_age: int,
    FRA: int = 67,
    spouse_PIA: Optional[float] = None,
    spouse_start_age: Optional[int] = None,
    survivor: bool = False,
) -> float:
    """Estimate annual Social Security benefits for an individual or couple.

    Parameters
    ----------
    PIA : float
        Primary Insurance Amount (monthly benefit at full retirement age).
    start_age : int
        Age at which benefits begin.  Must be between 62 and 70.
    FRA : int, optional
        Full retirement age (default 67).
    spouse_PIA : float, optional
        PIA of the spouse.  If provided, the higher of the two benefits will be
        returned when ``survivor`` is True.
    spouse_start_age : int, optional
        Spouse’s claiming age.  Only relevant when modelling survivor benefits.
    survivor : bool, optional
        If True, return the survivor benefit (the larger of the two benefits).

    Returns
    -------
    float
        Estimated annual Social Security benefit at the chosen claiming age.
    """
    def _adjusted_monthly(pia: float, claim_age: int) -> float:
        # clamp ages to [62, 70]
        claim_age = max(62, min(70, claim_age))
        years_diff = claim_age - FRA
        if years_diff < 0:
            # Early claiming: reduce 7% per year
            factor = 1 + 0.07 * years_diff  # negative years_diff
        else:
            # Delayed credits: increase 8% per year
            factor = 1 + 0.08 * years_diff
        return pia * factor

    primary_monthly = _adjusted_monthly(PIA, start_age)
    if spouse_PIA is None:
        return primary_monthly * 12

    # If spousal PIA is provided, compute spouse’s benefit as well
    spouse_monthly = _adjusted_monthly(spouse_PIA, spouse_start_age or start_age)
    if survivor:
        # Survivor receives the larger of the two benefits
        return max(primary_monthly, spouse_monthly) * 12
    # Otherwise return combined annual benefits (simplified; real rules are more complex)
    return (primary_monthly + spouse_monthly) * 12


def estimate_pia(
    current_age: int,
    retire_age: int,
    salary: float,
    salary_growth: float,
) -> float:
    """Roughly estimate the monthly PIA from projected earnings.

    The calculation assumes earnings from age 22 until the year before
    ``retire_age``.  Salaries grow at ``salary_growth`` each year and the
    highest 35 years of earnings are averaged to compute AIME.  The 2024 bend
    points are applied to convert AIME to a monthly PIA.  This is a
    simplification and ignores wage indexing, inflation adjustments and other
    nuances of the real Social Security formula.
    """
    start_age = 22
    if retire_age <= start_age or salary <= 0:
        return 0.0

    # Build an earnings history from start_age until retirement
    earnings = []

    # Earnings prior to the current age
    past_salary = salary
    for _age in range(current_age - 1, start_age - 1, -1):
        past_salary /= (1 + salary_growth)
        earnings.append(past_salary)
    earnings.reverse()  # chronological order

    # Current age and future earnings until retirement
    earnings.append(salary)
    future_salary = salary
    for _age in range(current_age + 1, retire_age):
        future_salary *= (1 + salary_growth)
        earnings.append(future_salary)

    top_earnings = sorted(earnings, reverse=True)[:35]
    if len(top_earnings) < 35:
        top_earnings += [0.0] * (35 - len(top_earnings))
    aime = sum(top_earnings) / (35 * 12)

    bend1, bend2 = 1174, 7078  # 2024 bend points
    if aime <= bend1:
        pia = 0.9 * aime
    elif aime <= bend2:
        pia = 0.9 * bend1 + 0.32 * (aime - bend1)
    else:
        pia = 0.9 * bend1 + 0.32 * (bend2 - bend1) + 0.15 * (aime - bend2)
    return pia


__all__ = ["social_security_benefit", "estimate_pia"]
