# calculators/roth.py
from typing import Dict

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
