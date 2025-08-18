import streamlit as st

# Stable widget keys so we can programmatically set values on load
WIDGET_KEYS = {
    "current_age": "in_current_age",
    "retire_age": "in_retire_age",
    "end_age": "in_end_age",
    "state": "in_state",
    "filing": "in_filing",

    # Traditional / pre-tax accounts
    "pre_tax_401k_balance": "in_pre_tax_401k_balance",
    "pre_tax_401k_contrib": "in_pre_tax_401k_contrib",
    "pre_tax_401k_mean": "in_pre_tax_401k_mean",

    "pre_tax_ira_balance": "in_pre_tax_ira_balance",
    "pre_tax_ira_contrib": "in_pre_tax_ira_contrib",
    "pre_tax_ira_mean": "in_pre_tax_ira_mean",

    # Roth accounts
    "roth_401k_balance": "in_roth_401k_balance",
    "roth_401k_contrib": "in_roth_401k_contrib",
    "roth_401k_mean": "in_roth_401k_mean",

    "roth_ira_balance": "in_roth_ira_balance",
    "roth_ira_contrib": "in_roth_ira_contrib",
    "roth_ira_mean": "in_roth_ira_mean",

    "taxable_balance": "in_taxable_balance",
    "taxable_contrib": "in_taxable_contrib",
    "taxable_mean": "in_taxable_mean",

    "cash_balance": "in_cash_balance",

    "salary": "in_salary",
    "salary_growth": "in_salary_growth_pct",
    "baseline_expenses": "in_baseline_expenses",

    "ss_pia": "in_ss_pia",
    "ss_claim_age": "in_ss_claim_age",

    "rc_cap": "in_rc_cap",
    "rc_start_age": "in_rc_start_age",
    "rc_end_age": "in_rc_end_age",
    "rc_tax_rate": "in_rc_tax_rate",
    "rc_pay_from_taxable": "in_rc_pay_from_taxable",

    "returns_correlated": "in_returns_correlated",
    "n_paths": "in_n_paths",
    "withdrawal_strategy": "in_withdrawal_strategy",
}

def _d(key, fallback):
    return st.session_state.get("form_defaults", {}).get(key, fallback)

def _wavg(vals, weights):
    total = sum(weights)
    return sum(v * w for v, w in zip(vals, weights)) / total if total > 0 else 0.0

def plan_form():
    # -------- Profile --------
    st.sidebar.header("Profile")
    current_age = st.sidebar.number_input(
        "Current age", min_value=18, max_value=120,
        value=_d("current_age", 55), key=WIDGET_KEYS["current_age"],
        help="Your age today. Drives the start of the projection window."
    )
    retire_age = st.sidebar.number_input(
        "Retire age", min_value=18, max_value=120,
        value=_d("retire_age", 65), key=WIDGET_KEYS["retire_age"],
        help="When you expect to stop full-time work."
    )
    end_age = st.sidebar.number_input(
        "Plan through age", min_value=60, max_value=120,
        value=_d("end_age", 90), key=WIDGET_KEYS["end_age"],
        help="Projection horizon used for success probability."
    )
    state = st.sidebar.text_input(
        "State (2-letter)", value=_d("state","MI"),
        key=WIDGET_KEYS["state"], help="Used for (very simplified) state tax."
    )
    filing = st.sidebar.selectbox(
        "Filing status", ["single"], index=0, key=WIDGET_KEYS["filing"],
        help="Simplified for demo."
    )

    # -------- Accounts --------
    st.sidebar.header("Accounts")
    with st.sidebar.expander("Traditional 401k", expanded=False):
        pre_tax_401k_balance = st.number_input(
            "Balance", min_value=0.0,
            value=_d("pre_tax_401k_balance", 0.0), key=WIDGET_KEYS["pre_tax_401k_balance"],
        )
        pre_tax_401k_contrib = st.number_input(
            "Annual contribution", min_value=0.0,
            value=_d("pre_tax_401k_contrib", 0.0), key=WIDGET_KEYS["pre_tax_401k_contrib"],
            help="Maximum $23,000/yr (2024).",
        )
        pre_tax_401k_mean = st.number_input(
            "Assumed mean return", step=0.005,
            value=_d("pre_tax_401k_mean", 0.05), key=WIDGET_KEYS["pre_tax_401k_mean"],
        )

    with st.sidebar.expander("Traditional IRA", expanded=False):
        pre_tax_ira_balance = st.number_input(
            "Balance", min_value=0.0,
            value=_d("pre_tax_ira_balance", 0.0), key=WIDGET_KEYS["pre_tax_ira_balance"],
        )
        pre_tax_ira_contrib = st.number_input(
            "Annual contribution", min_value=0.0,
            value=_d("pre_tax_ira_contrib", 0.0), key=WIDGET_KEYS["pre_tax_ira_contrib"],
            help="Maximum $7,000/yr (2024).",
        )
        pre_tax_ira_mean = st.number_input(
            "Assumed mean return", step=0.005,
            value=_d("pre_tax_ira_mean", 0.05), key=WIDGET_KEYS["pre_tax_ira_mean"],
        )

    with st.sidebar.expander("Roth 401k", expanded=False):
        roth_401k_balance = st.number_input(
            "Balance", min_value=0.0,
            value=_d("roth_401k_balance", 0.0), key=WIDGET_KEYS["roth_401k_balance"],
        )
        roth_401k_contrib = st.number_input(
            "Annual contribution", min_value=0.0,
            value=_d("roth_401k_contrib", 0.0), key=WIDGET_KEYS["roth_401k_contrib"],
            help="Maximum $23,000/yr (2024).",
        )
        roth_401k_mean = st.number_input(
            "Assumed mean return", step=0.005,
            value=_d("roth_401k_mean", 0.06), key=WIDGET_KEYS["roth_401k_mean"],
        )

    with st.sidebar.expander("Roth IRA", expanded=False):
        roth_ira_balance = st.number_input(
            "Balance", min_value=0.0,
            value=_d("roth_ira_balance", 0.0), key=WIDGET_KEYS["roth_ira_balance"],
        )
        roth_ira_contrib = st.number_input(
            "Annual contribution", min_value=0.0,
            value=_d("roth_ira_contrib", 0.0), key=WIDGET_KEYS["roth_ira_contrib"],
            help="Maximum $7,000/yr (2024) and subject to income limits.",
        )
        roth_ira_mean = st.number_input(
            "Assumed mean return", step=0.005,
            value=_d("roth_ira_mean", 0.06), key=WIDGET_KEYS["roth_ira_mean"],
        )

    with st.sidebar.expander("Taxable / Brokerage", expanded=False):
        taxable_balance = st.number_input(
            "Balance", min_value=0.0,
            value=_d("taxable_balance", 0.0), key=WIDGET_KEYS["taxable_balance"],
        )
        taxable_contrib = st.number_input(
            "Annual contribution", min_value=0.0,
            value=_d("taxable_contrib", 0.0), key=WIDGET_KEYS["taxable_contrib"],
        )
        taxable_mean = st.number_input(
            "Assumed mean return", step=0.005,
            value=_d("taxable_mean", 0.06), key=WIDGET_KEYS["taxable_mean"],
        )

    with st.sidebar.expander("Cash", expanded=False):
        cash_balance = st.number_input(
            "Balance", min_value=0.0,
            value=_d("cash_balance", 0.0), key=WIDGET_KEYS["cash_balance"],
            help="Emergency funds or checking accounts.",
        )

    # -------- Income --------
    st.sidebar.header("Income")
    salary = st.sidebar.number_input("Salary (pre-retirement)", min_value=0.0,
                             value=_d("salary",0.0), key=WIDGET_KEYS["salary"])
    salary_growth_pct = st.sidebar.number_input(
        "Salary annual raise (%)", min_value=0.0, max_value=100.0,
        value=_d("salary_growth", 3.0), key=WIDGET_KEYS["salary_growth"],
        help="Average yearly raise before retirement, as a percent."
    )

    # -------- Expenses --------
    st.sidebar.header("Expenses")
    baseline_expenses = st.sidebar.number_input("Baseline annual expenses", min_value=0.0,
                                        value=_d("baseline_expenses",0.0),
                                        key=WIDGET_KEYS["baseline_expenses"])
    st.sidebar.caption("Use the **Special Expenses Editor** on the main page to add unlimited one-offs.")

    # -------- Social Security --------
    st.sidebar.header("Social Security")
    ss_pia = st.sidebar.number_input(
        "PIA (monthly at FRA)", min_value=0.0,
        value=_d("ss_pia", 0.0), key=WIDGET_KEYS["ss_pia"],
        help="Primary Insurance Amount — benefit at full retirement age (67).",
    )
    ss_claim_age = st.sidebar.number_input(
        "Claiming age", min_value=62, max_value=70,
        value=_d("ss_claim_age", 67), key=WIDGET_KEYS["ss_claim_age"],
        help="Earliest claim is 62; waiting until 70 increases the benefit.",
    )

    # -------- Roth Conversion --------
    st.sidebar.header("Roth Conversion")
    st.sidebar.caption(
        "Convert pre-tax assets to Roth before Required Minimum Distribution (RMD) age to manage taxes."
    )
    rc_cap = st.sidebar.number_input(
        "Annual conversion cap (0–1)", min_value=0.0, max_value=1.0, step=0.01,
        value=_d("rc_cap",0.0), key=WIDGET_KEYS["rc_cap"],
        help="Fraction of prior-year pre-tax balance to convert each year while in the window."
    )
    rc_start_age = st.sidebar.number_input("Start age", min_value=18, max_value=120,
                                   value=_d("rc_start_age",55), key=WIDGET_KEYS["rc_start_age"])
    rc_end_age   = st.sidebar.number_input("End age", min_value=18, max_value=120,
                                   value=_d("rc_end_age",70), key=WIDGET_KEYS["rc_end_age"])
    rc_tax_rate = st.sidebar.number_input(
        "Target tax rate for conversions (0–1)", min_value=0.0, max_value=1.0, step=0.01,
        value=_d("rc_tax_rate",0.22), key=WIDGET_KEYS["rc_tax_rate"],
        help="Applied to the converted amount as ordinary income for that year."
    )
    rc_pay_from_taxable = st.sidebar.checkbox(
        "Pay conversion taxes from taxable?", value=_d("rc_pay_from_taxable", True),
        key=WIDGET_KEYS["rc_pay_from_taxable"],
        help="If off, tax is withheld from the conversion (less goes into Roth)."
    )

    # -------- Withdrawal Strategy --------
     # -------- Withdrawal Strategy --------
    st.sidebar.header("Withdrawal Strategy")
    strategy_options = ["standard", "proportional", "tax_bracket"]
    strategy_labels = {
        "standard": "Taxable → Traditional → Roth",
        "proportional": "Proportional taxable/traditional",
        "tax_bracket": "Fill bracket with traditional",
    }
    strategy_help = {
        "standard": "Withdraw from taxable accounts first, then traditional accounts, and leave Roth assets for last.",
        "proportional": "Each year, pull from taxable and traditional accounts in proportion to their balances; tap Roth only when necessary.",
        "tax_bracket": "Use traditional withdrawals to fill the current tax bracket, then withdraw from taxable accounts, saving Roth for last.",
    }
    strategy_default = _d("withdrawal_strategy", "standard")
    strategy = st.sidebar.selectbox(
        "Strategy",
        strategy_options,
        index=strategy_options.index(strategy_default) if strategy_default in strategy_options else 0,
        format_func=lambda s: strategy_labels.get(s, s),
        key=WIDGET_KEYS["withdrawal_strategy"],
        help="Choose how retirement withdrawals are sequenced across accounts.",
    )
    st.sidebar.caption(strategy_help.get(strategy, ""))


    # -------- Assumptions / Sim --------
    st.sidebar.header("Assumptions")
    returns_correlated = st.sidebar.checkbox(
        "Correlate all accounts 100% (sequence risk)",
        value=_d("returns_correlated", True), key=WIDGET_KEYS["returns_correlated"]
    )
    n_paths = st.sidebar.slider(
        "Monte Carlo paths", min_value=200, max_value=5000,
        value=int(_d("n_paths", 1000)), step=100, key=WIDGET_KEYS["n_paths"]
    )

    # Return a full plan dict
        accounts = {
        "pre_tax_401k": {
            "balance": float(pre_tax_401k_balance),
            "contribution": float(pre_tax_401k_contrib),
            "mean_return": float(pre_tax_401k_mean),
            "stdev_return": 0.10,
        },
        "pre_tax_ira": {
            "balance": float(pre_tax_ira_balance),
            "contribution": float(pre_tax_ira_contrib),
            "mean_return": float(pre_tax_ira_mean),
            "stdev_return": 0.10,
        },
        "roth_401k": {
            "balance": float(roth_401k_balance),
            "contribution": float(roth_401k_contrib),
            "mean_return": float(roth_401k_mean),
            "stdev_return": 0.12,
        },
        "roth_ira": {
            "balance": float(roth_ira_balance),
            "contribution": float(roth_ira_contrib),
            "mean_return": float(roth_ira_mean),
            "stdev_return": 0.12,
        },
        "taxable": {
            "balance": float(taxable_balance),
            "contribution": float(taxable_contrib),
            "mean_return": float(taxable_mean),
            "stdev_return": 0.12,
        },
        "cash": {"balance": float(cash_balance)},
    }

    # aggregated totals for backward compatibility
    pre_bal = accounts["pre_tax_401k"]["balance"] + accounts["pre_tax_ira"]["balance"]
    pre_con = accounts["pre_tax_401k"]["contribution"] + accounts["pre_tax_ira"]["contribution"]
    pre_mean = _wavg(
        [accounts["pre_tax_401k"]["mean_return"], accounts["pre_tax_ira"]["mean_return"]],
        [accounts["pre_tax_401k"]["balance"], accounts["pre_tax_ira"]["balance"]],
    )
    pre_stdev = 0.10
    roth_bal = accounts["roth_401k"]["balance"] + accounts["roth_ira"]["balance"]
    roth_con = accounts["roth_401k"]["contribution"] + accounts["roth_ira"]["contribution"]
    roth_mean = _wavg(
        [accounts["roth_401k"]["mean_return"], accounts["roth_ira"]["mean_return"]],
        [accounts["roth_401k"]["balance"], accounts["roth_ira"]["balance"]],
    )
    roth_stdev = 0.12
    accounts["pre_tax"] = {
        "balance": pre_bal,
        "contribution": pre_con,
        "mean_return": pre_mean,
        "stdev_return": pre_stdev,
    }
    accounts["roth"] = {
        "balance": roth_bal,
        "contribution": roth_con,
        "mean_return": roth_mean,
        "stdev_return": roth_stdev,
    }


    plan = {
        "current_age": int(current_age),
        "retire_age": int(retire_age),
        "end_age": int(end_age),
        "state": state,
        "filing_status": filing,
        "accounts": accounts,
        "income": {
            "salary": float(salary),
            "salary_growth": float(salary_growth_pct) / 100.0
        },
        "expenses": {
            "baseline": float(baseline_expenses),
            # "special" list is edited on the main page
        },
        "assumptions": {"returns_correlated": bool(returns_correlated)},
        "social_security": {"PIA": float(ss_pia), "claim_age": int(ss_claim_age)},
        "roth_conversion": {
            "annual_cap": float(rc_cap),
            "start_age": int(rc_start_age),
            "end_age": int(rc_end_age),
            "tax_rate": float(rc_tax_rate),
            "pay_tax_from_taxable": bool(rc_pay_from_taxable),
        },
        "withdrawal_strategy": strategy,
        "_sim": {"n_paths": int(n_paths)}
    }
    return plan
