from __future__ import annotations
from typing import Dict, List
import numpy as np

# RMD rules are in a sibling module
from . import rmd, taxes as tax_calc

def _draw_return(mean: float, stdev: float, rng: np.random.Generator) -> float:
    return rng.normal(loc=mean, scale=stdev)

def _contribution_for_age(acct: Dict, age: int) -> float:
    sched = acct.get("contribution_schedule")
    if isinstance(sched, dict):
        return float(sched.get(age, sched.get(str(age), 0.0)))
    return float(acct.get("contribution", 0.0))


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

def _simulate_path_split(plan: dict, rng: np.random.Generator) -> dict:
    curr = int(plan["current_age"])
    end = int(plan["end_age"])
    retire_age = int(plan["retire_age"])

    acc = plan.get("accounts", {})
    pre_tax_401k = acc.get("pre_tax_401k", {}).copy()
    pre_tax_ira = acc.get("pre_tax_ira", {}).copy()
    roth_401k = acc.get("roth_401k", {}).copy()
    roth_ira = acc.get("roth_ira", {}).copy()
    taxable = acc.get("taxable", {}).copy()
    cash = acc.get("cash", {}).copy()
    pre_tax_tax_rate = float(acc.get("pre_tax", {}).get("withdrawal_tax_rate", 0.0))

    roth_income_limit = float(plan.get("income", {}).get("roth_income_limit", float("inf")))

    salary = float(plan.get("income", {}).get("salary", 0.0))
    salary_growth = float(plan.get("income", {}).get("salary_growth", 0.0))
    income_tax_rate = float(plan.get("income", {}).get("tax_rate", 0.0))

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

    strategy = plan.get("withdrawal_strategy", "standard")
    bracket = plan.get("withdrawal_bracket", {}) or {}

    birth_year = int(plan.get("birth_year", 1900))
    rmd_start = rmd.rmd_start_age(birth_year)

    def _pre_tax_balance():
        return pre_tax_401k.get("balance", 0.0) + pre_tax_ira.get("balance", 0.0)

    def _roth_balance():
        return roth_401k.get("balance", 0.0) + roth_ira.get("balance", 0.0)

    def _take_from_pre_tax(gross: float):
        take = min(pre_tax_401k.get("balance", 0.0), gross)
        pre_tax_401k["balance"] -= take
        remaining = gross - take
        if remaining > 0:
            pre_tax_ira["balance"] -= remaining

    def _take_from_roth(amount: float):
        take = min(roth_401k.get("balance", 0.0), amount)
        roth_401k["balance"] -= take
        remaining = amount - take
        if remaining > 0:
            roth_ira["balance"] -= remaining

    ages = list(range(curr, end + 1))
    net_worth: List[float] = []
    ledger = {
        "age": [], "income": [], "expenses": [], "withdrawals": [], "taxes": [],
        "roth_conversion": [], "conversion_tax": [],
        "pre_tax": [], "roth": [], "taxable": [], "cash": [], "net_worth": []
    }
    acct_series = {k: [] for k in ["pre_tax", "roth", "taxable", "cash"]}

    for age in ages:
        prior_pre_tax_balance = _pre_tax_balance()
        if age < retire_age:
            year_income = salary
            salary *= (1.0 + salary_growth)
        else:
            year_income = 0.0

        extra = special_by_age.get(age, 0.0)
        year_expenses = baseline + extra

        year_withdrawals = 0.0
        withdraw_tax = 0.0
        available = year_income - year_expenses

        if age < retire_age and available > 0:
            want = _contribution_for_age(pre_tax_401k, age)
            cap = want if pre_tax_401k.get('contribution_schedule') else 23000.0
            contrib = min(available, want, cap)
            pre_tax_401k['balance'] += contrib
            available -= contrib

            want = _contribution_for_age(roth_401k, age)
            cap = want if roth_401k.get('contribution_schedule') else 23000.0
            contrib = min(available, want, cap)
            roth_401k['balance'] += contrib
            available -= contrib

            want = _contribution_for_age(pre_tax_ira, age)
            cap = want if pre_tax_ira.get('contribution_schedule') else 7000.0
            contrib = min(available, want, cap)
            pre_tax_ira['balance'] += contrib
            available -= contrib

            want = _contribution_for_age(roth_ira, age)
            if year_income <= roth_income_limit:
                cap = want if roth_ira.get('contribution_schedule') else 7000.0
                contrib = min(available, want, cap)
                roth_ira['balance'] += contrib
                available -= contrib

            want = _contribution_for_age(taxable, age)
            contrib = min(available, want)
            taxable['balance'] += contrib
            available -= contrib

        income_tax = year_income * income_tax_rate
        available -= income_tax

        if available < 0:
            need = -available
            take = min(cash.get("balance", 0.0), need)
            cash["balance"] -= take
            need -= take
            year_withdrawals += take

            if need > 0:
                take = min(taxable.get("balance", 0.0), need)
                taxable["balance"] -= take
                need -= take
                year_withdrawals += take

            if need > 0:
                rate = pre_tax_tax_rate
                gross = min(_pre_tax_balance(), need / (1 - rate) if rate < 1 else need)
                net = gross * (1 - rate)
                _take_from_pre_tax(gross)
                need -= net
                year_withdrawals += gross
                withdraw_tax += gross * rate

            if need > 0:
                take = min(_roth_balance(), need)
                _take_from_roth(take)
                need -= take
                year_withdrawals += take

        if available > 0:
            cash['balance'] = cash.get('balance', 0.0) + available
            available = 0.0

        if correlate:
            rdraw = _draw_return(0.06, 0.12, rng)
            def ret(bal, mean, _stdev):
                return bal * (1.0 + rdraw + (mean - 0.06))
        else:
            def ret(bal, mean, stdev):
                return bal * (1.0 + _draw_return(mean, stdev, rng))

        pre_tax_401k["balance"] = ret(pre_tax_401k.get("balance", 0.0), pre_tax_401k.get("mean_return", 0.05), pre_tax_401k.get("stdev_return", 0.10))
        pre_tax_ira["balance"] = ret(pre_tax_ira.get("balance", 0.0), pre_tax_ira.get("mean_return", 0.05), pre_tax_ira.get("stdev_return", 0.10))
        roth_401k["balance"] = ret(roth_401k.get("balance", 0.0), roth_401k.get("mean_return", 0.06), roth_401k.get("stdev_return", 0.12))
        roth_ira["balance"] = ret(roth_ira.get("balance", 0.0), roth_ira.get("mean_return", 0.06), roth_ira.get("stdev_return", 0.12))
        taxable["balance"] = ret(taxable.get("balance", 0.0), taxable.get("mean_return", 0.06), taxable.get("stdev_return", 0.12))

        gross_conv = _decide_conversion(prior_pre_tax_balance, age, rc)
        gross_conv = max(0.0, min(gross_conv, _pre_tax_balance()))
        conv_tax_rate = float(rc.get("tax_rate", 0.0))
        conv_tax = gross_conv * conv_tax_rate

        if gross_conv > 0.0:
            if rc.get("pay_tax_from_taxable", True):
                taxable["balance"] -= conv_tax
                _take_from_pre_tax(gross_conv)
                roth_ira["balance"] += gross_conv
            else:
                net_to_roth = max(0.0, gross_conv - conv_tax)
                _take_from_pre_tax(gross_conv)
                roth_ira["balance"] += net_to_roth

        if age >= retire_age:
            need = max(0.0, year_expenses)
            rate = pre_tax_tax_rate
            rmd_gross = 0.0
            if age >= rmd_start and _pre_tax_balance() > 0.0:
                rmd_gross = rmd.compute_rmd(prior_pre_tax_balance, age)
                rmd_gross = min(rmd_gross, _pre_tax_balance())
                net_rmd = rmd_gross * (1 - rate)
                _take_from_pre_tax(rmd_gross)
                year_withdrawals += rmd_gross
                withdraw_tax += rmd_gross * rate
                if net_rmd >= need:
                    cash["balance"] = cash.get("balance", 0.0) + (net_rmd - need)
                    need = 0.0
                else:
                    need -= net_rmd

            if need > 0:
                if strategy == "proportional":
                    tax_bal = taxable.get("balance", 0.0)
                    pre_bal = _pre_tax_balance()
                    total_net = tax_bal + pre_bal * (1 - rate)
                    if total_net > 0:
                        desired_taxable = need * (tax_bal / total_net)
                        net_from_taxable = min(tax_bal, desired_taxable)
                        taxable["balance"] -= net_from_taxable
                        year_withdrawals += net_from_taxable
                        need -= net_from_taxable

                        net_from_pre = min(pre_bal * (1 - rate), need)
                        gross_pre = net_from_pre / (1 - rate) if rate < 1 else net_from_pre
                        _take_from_pre_tax(gross_pre)
                        year_withdrawals += gross_pre
                        withdraw_tax += gross_pre * rate
                        need -= net_from_pre
                elif strategy == "tax_bracket":
                    limit = float(bracket.get("pre_tax_limit", 0.0))
                    limit = max(0.0, limit - rmd_gross)
                    if limit > 0 and need > 0:
                        gross = min(_pre_tax_balance(), limit, need / (1 - rate) if rate < 1 else need)
                        net = gross * (1 - rate)
                        _take_from_pre_tax(gross)
                        need -= net
                        year_withdrawals += gross
                        withdraw_tax += gross * rate
                    if need > 0:
                        take = min(taxable.get("balance", 0.0), need)
                        taxable["balance"] -= take
                        need -= take
                        year_withdrawals += take
                else:
                    take = min(taxable.get("balance", 0.0), need)
                    taxable["balance"] -= take
                    need -= take
                    year_withdrawals += take
                    if need > 0:
                        gross = min(_pre_tax_balance(), need / (1 - rate) if rate < 1 else need)
                        net = gross * (1 - rate)
                        _take_from_pre_tax(gross)
                        need -= net
                        year_withdrawals += gross
                        withdraw_tax += gross * rate
                if need > 0:
                    take = min(_roth_balance(), need)
                    _take_from_roth(take)
                    need -= take
                    year_withdrawals += take
                if need > 0:
                    take = min(cash.get("balance", 0.0), need)
                    cash["balance"] -= take
                    need -= take
                    year_withdrawals += take

        total_pre = _pre_tax_balance()
        total_roth = _roth_balance()
        total_nw = total_pre + total_roth + taxable.get("balance", 0.0) + cash.get("balance", 0.0)
        net_worth.append(total_nw)

        acct_series["pre_tax"].append(total_pre)
        acct_series["roth"].append(total_roth)
        acct_series["taxable"].append(taxable.get("balance", 0.0))
        acct_series["cash"].append(cash.get("balance", 0.0))

        ledger["age"].append(age)
        ledger["income"].append(year_income)
        ledger["expenses"].append(year_expenses)
        ledger["withdrawals"].append(year_withdrawals)
        ledger["taxes"].append(income_tax + conv_tax + withdraw_tax)
        ledger["roth_conversion"].append(gross_conv)
        ledger["conversion_tax"].append(conv_tax)
        ledger["pre_tax"].append(total_pre)
        ledger["roth"].append(total_roth)
        ledger["taxable"].append(taxable.get("balance", 0.0))
        ledger["cash"].append(cash.get("balance", 0.0))
        ledger["net_worth"].append(total_nw)

    return {
        "ages": ages,
        "net_worth": net_worth,
        "acct_series": {k: np.array(v) for k, v in acct_series.items()},
        "ledger": ledger,
    }

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
    acc = plan.get("accounts", {})
    if any(k in acc for k in ["pre_tax_401k", "pre_tax_ira", "roth_401k", "roth_ira"]):
        return _simulate_path_split(plan, rng)

    curr = int(plan["current_age"])
    end = int(plan["end_age"])
    retire_age = int(plan["retire_age"])

    pre_tax = acc.get("pre_tax", {}).copy()
    roth = acc.get("roth", {}).copy()
    taxable = acc.get("taxable", {}).copy()
    taxable.setdefault("basis", taxable.get("balance", 0.0))
    cash = acc.get("cash", {}).copy()

    pre_tax_tax_rate = float(pre_tax.get("withdrawal_tax_rate", 0.0))
    taxable_tax_rate = float(taxable.get("withdrawal_tax_rate", pre_tax_tax_rate))

    # Roth IRA contribution behaviour
    roth_income_limit = float(plan.get("income", {}).get("roth_income_limit", float("inf")))
    roth_limit = float(roth.get("annual_limit", roth.get("contribution", 0.0)))
    roth_limit_growth = float(roth.get("limit_growth", 0.0))
    roth_max_out = bool(roth.get("max_out", False))

    # Income & salary growth
    salary = float(plan.get("income", {}).get("salary", 0.0))
    salary_growth = float(plan.get("income", {}).get("salary_growth", 0.0))
    income_tax_rate = float(plan.get("income", {}).get("tax_rate", 0.0))

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

    state = plan.get("state")
    filing_status = plan.get("filing_status", "single")

    # Withdrawal strategy controls how retirement expenses are funded
    strategy = plan.get("withdrawal_strategy", "standard")
    bracket = plan.get("withdrawal_bracket", {}) or {}

    # Determine the age RMDs must begin
    birth_year = int(plan.get("birth_year", 1900))
    rmd_start = rmd.rmd_start_age(birth_year)

    ss_info = plan.get("social_security", {}) or {}
    ss_pia = float(ss_info.get("PIA", 0.0))
    ss_claim_age = int(ss_info.get("claim_age", 67))
    ss_annual = 0.0
    if ss_pia > 0.0:
        from . import social_security as ss_calc
        ss_annual = ss_calc.social_security_benefit(PIA=ss_pia, start_age=ss_claim_age)

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
        if age >= ss_claim_age:
            year_income += ss_annual

        # --- expenses (baseline + specials) ---
        extra = special_by_age.get(age, 0.0)
        year_expenses = baseline + extra

        # --- handle contributions / deficits before retirement ---
        year_withdrawals = 0.0
        withdraw_tax = 0.0
        realized_gains = 0.0
        available = year_income - year_expenses

        pending_pre = pending_roth = pending_taxable = 0.0
        if age < retire_age and available > 0:
            want = float(pre_tax.get("contribution", 0.0))
            contrib = min(available, want)
            pending_pre = contrib
            available -= contrib

            roth_contrib_cap = float(roth.get("contribution", 0.0))
            if roth_max_out:
                roth_contrib_cap = roth_limit
            if year_income <= roth_income_limit:
                contrib = min(available, roth_contrib_cap)
                pending_roth = contrib
                available -= contrib

            want = float(taxable.get("contribution", 0.0))
            contrib = min(available, want)
            pending_taxable = contrib
            available -= contrib

        income_tax = year_income * income_tax_rate
        available -= income_tax

        def _cover_need(need: float) -> None:
            nonlocal withdraw_tax, year_withdrawals, realized_gains
            while need > 1e-9:
                take = min(cash.get("balance", 0.0), need)
                if take > 0:
                    cash["balance"] -= take
                    need -= take
                    year_withdrawals += take
                    continue
                bal = taxable.get("balance", 0.0)
                if need > 0 and bal > 0:
                    gross = min(bal, need)
                    basis = taxable.get("basis", bal)
                    basis_ratio = basis / bal if bal > 0 else 0.0
                    basis_used = gross * basis_ratio
                    gain = gross - basis_used
                    taxable["balance"] -= gross
                    taxable["basis"] = basis - basis_used
                    need -= gross
                    year_withdrawals += gross
                    realized_gains += gain
                    cg_tax = tax_calc.compute_capital_gains_tax(gain, filing_status=filing_status)
                    if cg_tax > 0:
                        withdraw_tax += cg_tax
                        need += cg_tax
                    continue
                bal = pre_tax.get("balance", 0.0)
                if need > 0 and bal > 0:
                    rate = pre_tax_tax_rate
                    gross = min(bal, need / (1 - rate) if rate < 1 else need)
                    net = gross * (1 - rate)
                    pre_tax["balance"] -= gross
                    need -= net
                    year_withdrawals += gross
                    withdraw_tax += gross * rate
                    continue
                bal = roth.get("balance", 0.0)
                if need > 0 and bal > 0:
                    take = min(bal, need)
                    roth["balance"] -= take
                    need -= take
                    year_withdrawals += take
                    continue
                break

        # If expenses exceed income or taxes, draw from accounts
        if available < 0:
            _cover_need(-available)

        if available > 0:
            cash["balance"] = cash.get("balance", 0.0) + available
            available = 0.0

        if state:
            state_tax = tax_calc.compute_state_tax(year_income + realized_gains, state=state, filing_status=filing_status)
            if state_tax > 0:
                withdraw_tax += state_tax
                _cover_need(state_tax)

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

        # add contributions at end of year
        pre_tax["balance"] += pending_pre
        roth["balance"]    += pending_roth
        taxable["balance"] += pending_taxable
        taxable["basis"] = taxable.get("basis", 0.0) + pending_taxable
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

            rate = pre_tax_tax_rate
            rmd_gross = 0.0
            if age >= rmd_start and pre_tax.get("balance", 0.0) > 0.0:
                rmd_gross = rmd.compute_rmd(prior_pre_tax_balance, age)
                rmd_gross = min(rmd_gross, pre_tax.get("balance", 0.0))
                net_rmd = rmd_gross * (1 - rate)
                pre_tax["balance"] -= rmd_gross
                year_withdrawals += rmd_gross
                withdraw_tax += rmd_gross * rate
                if net_rmd >= need:
                    cash["balance"] = cash.get("balance", 0.0) + (net_rmd - need)
                    need = 0.0
                else:
                    need -= net_rmd

            if need > 0:
                if strategy == "proportional":
                    tax_bal = taxable.get("balance", 0.0)
                    pre_bal = pre_tax.get("balance", 0.0)
                    total_net = tax_bal * (1 - taxable_tax_rate) + pre_bal * (1 - rate)
                    if total_net > 0:
                        desired_taxable_net = need * (tax_bal * (1 - taxable_tax_rate) / total_net)
                        gross_taxable = min(tax_bal, desired_taxable_net / (1 - taxable_tax_rate) if taxable_tax_rate < 1 else desired_taxable_net)
                        net_from_taxable = gross_taxable * (1 - taxable_tax_rate)
                        taxable["balance"] -= gross_taxable
                        year_withdrawals += gross_taxable
                        withdraw_tax += gross_taxable * taxable_tax_rate
                        need -= net_from_taxable

                        net_from_pre = min(pre_bal * (1 - rate), need)
                        gross_pre = net_from_pre / (1 - rate) if rate < 1 else net_from_pre
                        pre_tax["balance"] -= gross_pre
                        year_withdrawals += gross_pre
                        withdraw_tax += gross_pre * rate
                        need -= net_from_pre

                elif strategy == "tax_bracket":
                    limit = float(bracket.get("pre_tax_limit", 0.0))
                    limit = max(0.0, limit - rmd_gross)
                    if limit > 0 and need > 0:
                        gross = min(pre_tax.get("balance", 0.0), limit, need / (1 - rate) if rate < 1 else need)
                        net = gross * (1 - rate)
                        pre_tax["balance"] -= gross
                        need -= net
                        year_withdrawals += gross
                        withdraw_tax += gross * rate

                    if need > 0:
                        rate_t = taxable_tax_rate
                        gross = min(taxable.get("balance", 0.0), need / (1 - rate_t) if rate_t < 1 else need)
                        net = gross * (1 - rate_t)
                        taxable["balance"] -= gross
                        need -= net
                        year_withdrawals += gross
                        withdraw_tax += gross * rate_t

                else:  # standard taxable-first rule
                    rate_t = taxable_tax_rate
                    gross = min(taxable.get("balance", 0.0), need / (1 - rate_t) if rate_t < 1 else need)
                    net = gross * (1 - rate_t)
                    taxable["balance"] -= gross
                    need -= net
                    year_withdrawals += gross
                    withdraw_tax += gross * rate_t

                    if need > 0:
                        gross = min(pre_tax.get("balance", 0.0), need / (1 - rate) if rate < 1 else need)
                        net = gross * (1 - rate)
                        pre_tax["balance"] -= gross
                        need -= net
                        year_withdrawals += gross
                        withdraw_tax += gross * rate

                # roth is tapped after the chosen strategy above
                if need > 0:
                    take = min(roth.get("balance", 0.0), need)
                    roth["balance"] -= take
                    need -= take
                    year_withdrawals += take

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
        ledger["taxes"].append(income_tax + conv_tax + withdraw_tax)
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
