# calculators/monte_carlo.py
from __future__ import annotations
import numpy as np

def _draw_return(mean: float, stdev: float, rng: np.random.Generator) -> float:
    return rng.normal(loc=mean, scale=stdev)

def simulate(plan: dict, n_paths: int = 1000, seed: int | None = None) -> dict:
    rng = np.random.default_rng(seed)
    ages = list(range(plan["current_age"], plan["end_age"] + 1))

    terminal = []
    paths_networth = []
    acct_series_paths = []
    ledgers = []

    for _ in range(n_paths):
        res = simulate_path(plan, rng)
        terminal.append(res["net_worth"][-1])
        paths_networth.append(np.array(res["net_worth"]))
        acct_series_paths.append(res["acct_series"])
        ledgers.append(res["ledger"])

    stacked = np.vstack(paths_networth)  # n_paths x years
    p10 = np.percentile(stacked, 10, axis=0)
    p50 = np.percentile(stacked, 50, axis=0)
    p90 = np.percentile(stacked, 90, axis=0)

    median_idx = int(np.argmin(np.abs(stacked[:, -1] - np.median(stacked[:, -1]))))
    ledger_median = ledgers[median_idx]

    acct_keys = ["pre_tax", "roth", "taxable", "cash"]
    acct_series_median = {
        k: np.median(np.vstack([ap[k] for ap in acct_series_paths]), axis=0).tolist()
        for k in acct_keys
    }

    success_prob = float(np.mean(stacked[:, -1] >= 0.0))

    return {
        "ages": ages,
        "success_prob": success_prob,
        "median_terminal": float(np.median(stacked[:, -1])),
        "networth_p10": p10.tolist(),
        "networth_p50": p50.tolist(),
        "networth_p90": p90.tolist(),
        "acct_series_median": acct_series_median,
        "ledger_median": ledger_median,
    }

def simulate_path(plan: dict, rng: np.random.Generator) -> dict:
    curr = plan["current_age"]
    end = plan["end_age"]
    retire_age = plan["retire_age"]

    acc = plan.get("accounts", {})
    pre_tax = acc.get("pre_tax", {}).copy()
    roth = acc.get("roth", {}).copy()
    taxable = acc.get("taxable", {}).copy()
    cash = acc.get("cash", {}).copy()

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

    # Return correlation switch
    correlate = bool(plan.get("assumptions", {}).get("returns_correlated", True))

    ages = list(range(curr, end + 1))
    net_worth = []
    ledger = {
        "age": [], "income": [], "expenses": [], "withdrawals": [], "taxes": [],
        "pre_tax": [], "roth": [], "taxable": [], "cash": [], "net_worth": []
    }

    acct_series = {k: [] for k in ["pre_tax", "roth", "taxable", "cash"]}

    for age in ages:
        # --- income before retirement, then grow for next year ---
        if age < retire_age:
            year_income = salary
            salary = salary * (1.0 + salary_growth)
        else:
            year_income = 0.0

        # --- expenses (baseline + specials) ---
        extra = special_by_age.get(age, 0.0)
        year_expenses = baseline + extra

        # --- contributions before retirement ---
        if age < retire_age:
            pre_tax["balance"] = pre_tax.get("balance", 0.0) + pre_tax.get("contribution", 0.0)
            roth["balance"] = roth.get("balance", 0.0) + roth.get("contribution", 0.0)
            taxable["balance"] = taxable.get("balance", 0.0) + taxable.get("contribution", 0.0)

        # --- returns ---
        if correlate:
            rdraw = _draw_return(roth.get("mean_return", 0.06), roth.get("stdev_return", 0.12), rng)
            def ret(bal, mean, _stdev):
                # approximate correlation by anchoring on roth draw + mean shift
                return bal * (1.0 + rdraw + (mean - roth.get("mean_return", 0.06)))
        else:
            def ret(bal, mean, stdev):
                return bal * (1.0 + _draw_return(mean, stdev, rng))

        pre_tax["balance"] = ret(pre_tax.get("balance", 0.0), pre_tax.get("mean_return", 0.05), pre_tax.get("stdev_return", 0.10))
        roth["balance"]    = ret(roth.get("balance", 0.0),    roth.get("mean_return", 0.06),    roth.get("stdev_return", 0.12))
        taxable["balance"] = ret(taxable.get("balance", 0.0), taxable.get("mean_return", 0.06), taxable.get("stdev_return", 0.12))
        cash["balance"]    = cash.get("balance", 0.0)  # ignoring cash yield for simplicity

        # --- withdrawals to cover retirement expenses ---
        year_withdrawals = 0.0
        if age >= retire_age:
            need = max(0.0, year_expenses)
            for acct in (taxable, pre_tax, roth, cash):
                take = min(acct.get("balance", 0.0), need)
                acct["balance"] -= take
                need -= take
                year_withdrawals += take
                if need <= 0:
                    break

        # --- bookkeeping ---
        total_nw = sum([
            pre_tax.get("balance", 0.0),
            roth.get("balance", 0.0),
            taxable.get("balance", 0.0),
            cash.get("balance", 0.0),
        ])
        net_worth.append(total_nw)

        acct_series["pre_tax"].append(pre_tax.get("balance", 0.0))
        acct_series["roth"].append(roth.get("balance", 0.0))
        acct_series["taxable"].append(taxable.get("balance", 0.0))
        acct_series["cash"].append(cash.get("balance", 0.0))

        ledger["age"].append(age)
        ledger["income"].append(year_income)
        ledger["expenses"].append(year_expenses)
        ledger["withdrawals"].append(year_withdrawals)
        ledger["taxes"].append(0.0)  # simplified; plug in taxes module later
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
