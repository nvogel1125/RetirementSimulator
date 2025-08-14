# components/forms.py
import streamlit as st

# Stable widget keys so we can programmatically set values on load
WIDGET_KEYS = {
    "current_age": "in_current_age",
    "retire_age": "in_retire_age",
    "end_age": "in_end_age",
    "state": "in_state",
    "filing": "in_filing",

    "pre_tax_balance": "in_pre_tax_balance",
    "pre_tax_contrib": "in_pre_tax_contrib",
    "pre_tax_mean": "in_pre_tax_mean",
    "pre_tax_stdev": "in_pre_tax_stdev",

    "roth_balance": "in_roth_balance",
    "roth_contrib": "in_roth_contrib",
    "roth_mean": "in_roth_mean",
    "roth_stdev": "in_roth_stdev",

    "taxable_balance": "in_taxable_balance",
    "taxable_contrib": "in_taxable_contrib",
    "taxable_mean": "in_taxable_mean",
    "taxable_stdev": "in_taxable_stdev",

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
}

def _d(key, fallback):
    return st.session_state.get("form_defaults", {}).get(key, fallback)

def plan_form():
    st.sidebar.header("Profile")
    current_age = st.sidebar.number_input(
        "Current age",
        min_value=18, max_value=120,
        value=_d("current_age", 55),
        key=WIDGET_KEYS["current_age"],
        help="Your age today. Drives the start of the projection window."
    )
    retire_age = st.sidebar.number_input(
        "Retire age",
        min_value=18, max_value=120,
        value=_d("retire_age", 65),
        key=WIDGET_KEYS["retire_age"],
        help="When you expect to stop full-time work."
    )
    end_age = st.sidebar.number_input(
        "Plan through age",
        min_value=60, max_value=120,
        value=_d("end_age", 90),
        key=WIDGET_KEYS["end_age"],
        help="Projection horizon used for success probability."
    )
    state = st.sidebar.text_input(
        "State (2-letter)",
        value=_d("state","MI"),
        key=WIDGET_KEYS["state"],
        help="Used for state tax in the simplified tables."
    )
    filing = st.sidebar.selectbox(
        "Filing status", ["single"], index=0,
        key=WIDGET_KEYS["filing"],
        help="Simplified for demo."
    )

    st.sidebar.header("Accounts")
    with st.sidebar.expander("Tax-Deferred (401k/Traditional IRA)", expanded=False):
        pre_tax_balance = st.number_input("Balance", min_value=0.0, value=_d("pre_tax_balance",0.0),
                                          key=WIDGET_KEYS["pre_tax_balance"])
        pre_tax_contrib = st.number_input("Annual contribution", min_value=0.0, value=_d("pre_tax_contrib",0.0),
                                          key=WIDGET_KEYS["pre_tax_contrib"])
        pre_tax_mean    = st.number_input("Assumed mean return", value=_d("pre_tax_mean",0.05), step=0.005,
                                          key=WIDGET_KEYS["pre_tax_mean"])
        pre_tax_stdev   = st.number_input("Return stdev", value=_d("pre_tax_stdev",0.10), step=0.005,
                                          key=WIDGET_KEYS["pre_tax_stdev"])

    with st.sidebar.expander("Roth", expanded=False):
        roth_balance = st.number_input("Balance ", min_value=0.0, value=_d("roth_balance",0.0),
                                       key=WIDGET_KEYS["roth_balance"])
        roth_contrib = st.number_input("Annual contribution ", min_value=0.0, value=_d("roth_contrib",0.0),
                                       key=WIDGET_KEYS["roth_contrib"])
        roth_mean    = st.number_input("Assumed mean return ", value=_d("roth_mean",0.06), step=0.005,
                                       key=WIDGET_KEYS["roth_mean"])
        roth_stdev   = st.number_input("Return stdev ", value=_d("roth_stdev",0.12), step=0.005,
                                       key=WIDGET_KEYS["roth_stdev"])

    with st.sidebar.expander("Taxable / Brokerage", expanded=False):
        taxable_balance = st.number_input("Balance", min_value=0.0, value=_d("taxable_balance",0.0),
                                          key=WIDGET_KEYS["taxable_balance"])
        taxable_contrib = st.number_input("Annual contribution", min_value=0.0, value=_d("taxable_contrib",0.0),
                                          key=WIDGET_KEYS["taxable_contrib"])
        taxable_mean    = st.number_input("Assumed mean return", value=_d("taxable_mean",0.06), step=0.005,
                                          key=WIDGET_KEYS["taxable_mean"])
        taxable_stdev   = st.number_input("Return stdev", value=_d("taxable_stdev",0.12), step=0.005,
                                          key=WIDGET_KEYS["taxable_stdev"])

    with st.sidebar.expander("Cash", expanded=False):
        cash_balance = st.number_input("Balance", min_value=0.0, value=_d("cash_balance",0.0),
                                       key=WIDGET_KEYS["cash_balance"])

    st.sidebar.header("Income")
    salary = st.number_input("Salary (pre-retirement)", min_value=0.0, value=_d("salary",0.0),
                             key=WIDGET_KEYS["salary"])
    salary_growth_pct = st.number_input(
        "Salary annual raise (%)", min_value=0.0, max_value=100.0,
        value=_d("salary_growth", 3.0),
        key=WIDGET_KEYS["salary_growth"],
        help="Average yearly raise before retirement, as a percent."
    )

    st.sidebar.header("Expenses")
    baseline_expenses = st.number_input("Baseline annual expenses", min_value=0.0,
                                        value=_d("baseline_expenses",0.0),
                                        key=WIDGET_KEYS["baseline_expenses"])
    st.sidebar.caption("Use the **Special Expenses Editor** on the main page to add unlimited one-offs.")

    st.sidebar.header("Social Security")
    ss_pia = st.number_input("PIA (monthly at FRA)", min_value=0.0, value=_d("ss_pia",0.0),
                             key=WIDGET_KEYS["ss_pia"])
    ss_claim_age = st.number_input("Claiming age", min_value=62, max_value=70, value=_d("ss_claim_age",67),
                                   key=WIDGET_KEYS["ss_claim_age"])

    st.sidebar.header("Roth Conversion")
    rc_cap = st.number_input("Annual conversion cap", min_value=0.0, value=_d("rc_cap",0.0),
                             key=WIDGET_KEYS["rc_cap"])
    rc_start_age = st.number_input("Start age", min_value=18, max_value=120, value=_d("rc_start_age",55),
                                   key=WIDGET_KEYS["rc_start_age"])
    rc_end_age   = st.number_input("End age",   min_value=18, max_value=120, value=_d("rc_end_age",70),
                                   key=WIDGET_KEYS["rc_end_age"])
    rc_tax_rate = st.number_input("Target tax rate for conversions", min_value=0.0, max_value=1.0, step=0.01,
                                  value=_d("rc_tax_rate",0.22),
                                  key=WIDGET_KEYS["rc_tax_rate"])
    rc_pay_from_taxable = st.checkbox("Pay conversion taxes from taxable?",
                                      value=_d("rc_pay_from_taxable", True),
                                      key=WIDGET_KEYS["rc_pay_from_taxable"])

    st.sidebar.header("Assumptions")
    returns_correlated = st.checkbox("Correlate all accounts 100% (sequence risk)",
                                     value=_d("returns_correlated", True),
                                     key=WIDGET_KEYS["returns_correlated"])
    n_paths = st.sidebar.slider("Monte Carlo paths", min_value=200, max_value=5000,
                                value=int(_d("n_paths", 1000)), step=100,
                                key=WIDGET_KEYS["n_paths"])

    # Return a full plan dict
    plan = {
        "current_age": int(current_age),
        "retire_age": int(retire_age),
        "end_age": int(end_age),
        "state": state,
        "filing_status": filing,
        "accounts": {
            "pre_tax":  {"balance": float(pre_tax_balance), "contribution": float(pre_tax_contrib),
                         "mean_return": float(pre_tax_mean), "stdev_return": float(pre_tax_stdev)},
            "roth":     {"balance": float(roth_balance),    "contribution": float(roth_contrib),
                         "mean_return": float(roth_mean),    "stdev_return": float(roth_stdev)},
            "taxable":  {"balance": float(taxable_balance), "contribution": float(taxable_contrib),
                         "mean_return": float(taxable_mean), "stdev_return": float(taxable_stdev)},
            "cash":     {"balance": float(cash_balance)}
        },
        "income": {
            "salary": float(salary),
            "salary_growth": float(salary_growth_pct) / 100.0
        },
        "expenses": {
            "baseline": float(baseline_expenses),
            # special list is managed on the main page
        },
        "assumptions": {"returns_correlated": bool(returns_correlated)},
        "social_security": {"PIA": float(ss_pia), "claim_age": int(ss_claim_age)},
        "roth_conversion": {
            "annual_cap": float(rc_cap), "start_age": int(rc_start_age), "end_age": int(rc_end_age),
            "tax_rate": float(rc_tax_rate), "pay_tax_from_taxable": bool(rc_pay_from_taxable)
        },
        "_sim": {"n_paths": int(n_paths)}
    }
    return plan
