# calculators/roth.py
from typing import Dict


def roth_ira_max_schedule(start_age: int, retire_age: int, base_limit: float = 7000.0, inflation: float = 0.03) -> Dict[int, float]:
    """Return a schedule of Roth IRA contribution limits by age.

    The base limit grows with ``inflation`` each year and is rounded to the nearest
    $500.  Beginning at age 50 an additional $1,000 catch-up contribution is added.
    Contributions stop at ``retire_age`` (exclusive).
    """
    schedule: Dict[int, float] = {}
    for i, age in enumerate(range(start_age, retire_age)):
        limit = base_limit * ((1 + inflation) ** i)
        limit = round(limit / 500.0) * 500.0
        if age >= 50:
            limit += 1000.0
        schedule[age] = limit
    return schedule


def decide_conversion(prior_pre_tax_balance: float, age: int, rc: Dict) -> float:
    """
    Return the gross amount to convert this year based on a simple cap.
    - cap applies to prior-year pre-tax balance
    - only active within [start_age, end_age]
    """
    if not rc:
        return 0.0
    start = int(rc.get("start_age", 0))
    end = int(rc.get("end_age", 0))
    if age < start or age > end:
        return 0.0
    cap = float(rc.get("annual_cap", 0.0))
    cap = max(0.0, min(1.0, cap))
    return prior_pre_tax_balance * cap


def apply_conversion(pre_tax_balance: float, roth_balance: float, amount: float, tax_rate: float, pay_tax_from_taxable: bool = True):
    """Apply a Roth conversion to account balances.

    Parameters
    ----------
    pre_tax_balance : float
        Current balance of the pre‑tax account.
    roth_balance : float
        Current balance of the Roth account.
    amount : float
        Gross amount to convert from pre‑tax to Roth.
    tax_rate : float
        Marginal tax rate applied to the converted amount.
    pay_tax_from_taxable : bool, optional
        If ``True`` taxes are paid from a taxable account and the full
        conversion amount is added to the Roth.  If ``False`` taxes are
        withheld from the conversion, reducing the amount reaching the Roth.

    Returns
    -------
    tuple
        ``(balances, tax_due)`` where ``balances`` is a mapping containing the
        updated ``pre_tax`` and ``roth`` balances.
    """
    amount = max(0.0, min(amount, pre_tax_balance))
    tax_due = amount * max(0.0, tax_rate)
    if pay_tax_from_taxable:
        pre_tax_balance -= amount
        roth_balance += amount
    else:
        net = max(0.0, amount - tax_due)
        pre_tax_balance -= amount
        roth_balance += net
    return {"pre_tax": pre_tax_balance, "roth": roth_balance}, tax_due
