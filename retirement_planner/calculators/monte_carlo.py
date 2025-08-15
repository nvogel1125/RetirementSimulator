from __future__ import annotations
from typing import Dict, List
import numpy as np

def _draw_return(mean: float, stdev: float, rng: np.random.Generator) -> float:
    return rng.normal(loc=mean, scale=stdev)

def _decide_conversion(prior_pre_tax_balance: float, age: int, rc: Dict) -> float:
    """Gross amount to convert this year: cap * prior pre-tax balance within [start_age, end_age]."""
    if not rc:
        return 0.0
    start = int(rc.get("start_age", 0))
    end = int(rc.get("end_age", 0))
    if age < start or age > end:
        return 0.0
    cap = max(0.0, min(1.0, float(rc.get("annual_cap", 0.0))))
    return prior_pre_tax_balance * cap

def simulate(plan: dict, n_paths: int = 1000, seed: int | None = None) -> dict:
    rng = np.random.default_rng(seed)
    ages = list(range(plan["current_age"], plan["end_age"] + 1))

    paths_networth: List[np.ndarray] = []
    acct_series_paths: List[Dict[str, np.ndarray]] = []
    ledgers: List[dict] = []

    for _ in range(n_paths):
        res = simulate_path(plan, rng)
        paths_networth.append(np.array(res["net_worth"]))
        acct_series_paths.append(res["acct_series"])
        ledgers.append(res["ledger"])

    stacked = np.vstack(paths_networth)  # n_paths x years
    p10 = np.percentile(stacked, 10, axis=0)
    p50 = np.percentile(stacked, 50, axis=0)
    p90 = np.percentile(stacked, 90, axis=0)

    # median path by terminal NW
    terminal = stacked[:, -1]
    median_idx = int(np.argmin(np.abs(terminal - np.median(terminal))))
    ledger_median = ledgers[median_idx]

    acct_keys = ["pre_tax", "roth", "taxable", "cash"]
    acct_series_median = {
        k: np.median(np.vstack([ap[k] for ap in acct_series_paths]), axis=0).tolist()
        for k in acct_keys
    }

    success_prob = float(np.mean(terminal >= 0.0))

    return {
        "ages": ages,
        "success_probability": success_prob,
        "percentiles": {
            "p10": p10.tolist(),
            "p50": p50.tolist(),
            "p90": p90.tolist(),
        },
        "median_terminal": float(np.median(terminal)),
        "acct_series_median": acct_series_median,
        "ledger_median": ledger_median,
    }

def simulate_path(plan: dict, rng: np.random.Generator) -> dict:
    curr = int(plan["current_age"])
    end = int(plan["end_age"])
    retire_age = int(plan["retire_age"])

    acc = plan.get("accounts", {})
    pre_tax = acc.get("pre_tax", {}).copy()
    roth = acc.get("roth", {}).copy()
    taxable = acc.get("taxable", {}).copy()
    cash = acc.get("cash", {}).copy()

    # Pre- and post-tax withdrawal tax rate (used when tapping 401k/IRA)
    pre_tax_tax_rate = float(pre_tax.get("withdrawal_tax_rate", 0.0))

    # Roth IRA contribution behaviour
    roth_income_limit = float(plan.get("income", {}).get("roth_income_limit", float("inf")))
    roth_limit = float(roth.get("annual_limit", roth.get("contribution", 0.0)))
    roth_limit_growth = float(roth.get("limit_growth", 0.0))
    roth_max_out = bool(roth.get("max_out", False))

    # Income & salary growth
    salary = float(plan.get("income", {}).get("salary", 0.0))
    salary_growth = float(plan.get("income", {}).get("salary_growth", 0.0))

    # Expenses
    baseline = float(plan.get("expenses", {}).get("baseline", 0.0))
    special_list = plan.get("expenses", {}).get("special", [])
    special_by_age = {}
    for it in special_list:
        try:
            special_by_age[int(it.get("age", -1))] = float(it.get("amount", 0.0))
        except Exception:
            pass

    correlate = bool(plan.get("assumptions", {}).get("returns_correlated", True))
    rc = plan.get("roth_conversion", {}) or {}

    ages = list(range(curr, end + 1))
    net_worth: List[float] = []

    ledger = {
        "age": [], "income": [], "expenses": [], "withdrawals": [], "taxes": [],
        "roth_conversion": [], "conversion_tax": [],
        "pre_tax": [], "roth": [], "taxable": [], "cash": [], "net_worth": []
    }
    acct_series = {k: [] for k in ["pre_tax", "roth", "taxable", "cash"]}

    # loop state balance at the start of each year is "prior-year end"
    for age in ages:
        prior_pre_tax_balance = pre_tax.get("balance", 0.0)

        # --- income before retirement, then grow base for next year ---
        if age < retire_age:
            year_income = salary
            salary = salary * (1.0 + salary_growth)
        else:
            year_income = 0.0

        # --- expenses (baseline + specials) ---
        extra = special_by_age.get(age, 0.0)
        year_expenses = baseline + extra

        # --- handle contributions / deficits before retirement ---
        year_withdrawals = 0.0
        withdraw_tax = 0.0
        available = year_income - year_expenses

        if age < retire_age and available > 0:
            # 401k/pre-tax contributions first
            want = float(pre_tax.get("contribution", 0.0))
            contrib = min(available, want)
            pre_tax["balance"] = pre_tax.get("balance", 0.0) + contrib
            available -= contrib

            # Roth IRA (respect income limit)
            roth_contrib_cap = float(roth.get("contribution", 0.0))
            if roth_max_out:
                roth_contrib_cap = roth_limit
            if year_income <= roth_income_limit:
                contrib = min(available, roth_contrib_cap)
                roth["balance"] = roth.get("balance", 0.0) + contrib
                available -= contrib

            # Taxable/brokerage
            want = float(taxable.get("contribution", 0.0))
            contrib = min(available, want)
            taxable["balance"] = taxable.get("balance", 0.0) + contrib
            available -= contrib

            # Whatever remains sits in cash
            if available > 0:
                cash["balance"] = cash.get("balance", 0.0) + available
                available = 0.0

        # If expenses exceed income, draw from accounts
        if available < 0:
            need = -available
            # cash first
            take = min(cash.get("balance", 0.0), need)
            cash["balance"] -= take
            need -= take
            year_withdrawals += take

            # taxable next
            if need > 0:
                take = min(taxable.get("balance", 0.0), need)
                taxable["balance"] -= take
                need -= take
                year_withdrawals += take

            # pre-tax with tax impact
            if need > 0:
                rate = pre_tax_tax_rate
                gross = min(pre_tax.get("balance", 0.0), need / (1 - rate) if rate < 1 else need)
                net = gross * (1 - rate)
                pre_tax["balance"] -= gross
                need -= net
                year_withdrawals += gross
                withdraw_tax += gross * rate

            # roth last resort
            if need > 0:
                take = min(roth.get("balance", 0.0), need)
                roth["balance"] -= take
                need -= take
                year_withdrawals += take

        # update Roth limit for "max out" option
        if roth_max_out:
            roth_limit *= (1.0 + roth_limit_growth)
        # --- returns (correlated or independent) ---
        if correlate:
            rdraw = _draw_return(roth.get("mean_return", 0.06), roth.get("stdev_return", 0.12), rng)
            def ret(bal, mean, _stdev):
                return bal * (1.0 + rdraw + (mean - roth.get("mean_return", 0.06)))
        else:
            def ret(bal, mean, stdev):
                return bal * (1.0 + _draw_return(mean, stdev, rng))

        pre_tax["balance"] = ret(pre_tax.get("balance", 0.0), pre_tax.get("mean_return", 0.05), pre_tax.get("stdev_return", 0.10))
        roth["balance"]    = ret(roth.get("balance", 0.0),  roth.get("mean_return", 0.06),  roth.get("stdev_return", 0.12))
        taxable["balance"] = ret(taxable.get("balance", 0.0), taxable.get("mean_return", 0.06), taxable.get("stdev_return", 0.12))
        # cash balance kept flat in this simple model

        # --- Roth conversions (apply using prior pre-tax balance base) ---
        gross_conv = _decide_conversion(prior_pre_tax_balance, age, rc)
        gross_conv = max(0.0, min(gross_conv, pre_tax.get("balance", 0.0)))

        conv_tax_rate = float(rc.get("tax_rate", 0.0))
        conv_tax = gross_conv * conv_tax_rate

        if gross_conv > 0.0:
            if rc.get("pay_tax_from_taxable", True):
                taxable["balance"] -= conv_tax
                pre_tax["balance"] -= gross_conv
                roth["balance"]    += gross_conv
            else:
                net_to_roth = max(0.0, gross_conv - conv_tax)
                pre_tax["balance"] -= gross_conv
                roth["balance"]    += net_to_roth
                # taxable unchanged in this branch

        # --- withdrawals to cover retirement expenses ---
        if age >= retire_age:
            need = max(0.0, year_expenses)

            # taxable first
            take = min(taxable.get("balance", 0.0), need)
            taxable["balance"] -= take
            need -= take
            year_withdrawals += take

            # pre-tax with tax hit
            if need > 0:
                rate = pre_tax_tax_rate
                gross = min(pre_tax.get("balance", 0.0), need / (1 - rate) if rate < 1 else need)
                net = gross * (1 - rate)
                pre_tax["balance"] -= gross
                need -= net
                year_withdrawals += gross
                withdraw_tax += gross * rate

            # roth next
            if need > 0:
                take = min(roth.get("balance", 0.0), need)
                roth["balance"] -= take
                need -= take
                year_withdrawals += take

            # cash last
            if need > 0:
                take = min(cash.get("balance", 0.0), need)
                cash["balance"] -= take
                need -= take
                year_withdrawals += take

        # --- bookkeeping ---
        total_nw = sum([
            pre_tax.get("balance", 0.0),
            roth.get("balance", 0.0),
            taxable.get("balance", 0.0),
            cash.get("balance", 0.0),
        ])
        net_worth.append(total_nw)

        for k, v in (("pre_tax", pre_tax), ("roth", roth), ("taxable", taxable), ("cash", cash)):
            acct_series[k].append(v.get("balance", 0.0))

        ledger["age"].append(age)
        ledger["income"].append(year_income)
        ledger["expenses"].append(year_expenses)
        ledger["withdrawals"].append(year_withdrawals)
        ledger["taxes"].append(conv_tax + withdraw_tax)
        ledger["roth_conversion"].append(gross_conv)     # visibility
        ledger["conversion_tax"].append(conv_tax)
        ledger["pre_tax"].append(pre_tax.get("balance", 0.0))
        ledger["roth"].append(roth.get("balance", 0.0))
        ledger["taxable"].append(taxable.get("balance", 0.0))
        ledger["cash"].append(cash.get("balance", 0.0))
        ledger["net_worth"].append(total_nw)

    return {
        "ages": ages,
        "net_worth": net_worth,
        "acct_series": {k: np.array(v) for k, v in acct_series.items()},
        "ledger": ledger,
    }
