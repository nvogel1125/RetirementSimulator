# app.py
import json
from copy import deepcopy
from io import BytesIO
import os, time

import pandas as pd
import streamlit as st

from calculators import monte_carlo
from components.forms import plan_form, WIDGET_KEYS  # keys for sidebar widgets
from components.charts import fan_chart, account_area_chart, success_gauge

# ---------- Page config ----------
st.set_page_config(
    page_title="Retirement Planner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Light UI polish ----------
st.markdown("""
<style>
/* padding */
.block-container { padding-top: 1.0rem; }

/* soft cards for metrics and charts */
div[data-testid="stMetric"] { background:#f8fafc; border-radius:16px; padding:12px; }
div.stPlotlyChart { background:#ffffff; border-radius:14px; padding:6px; }

/* thin separators */
hr { border-top: 1px solid #e5e7eb; }

/* primary button a bit pill-y */
button[kind="primary"] { border-radius:9999px; padding:0.5rem 1rem; }
</style>
""", unsafe_allow_html=True)

# ---------- Session boot ----------
st.session_state.setdefault("plan", {})
st.session_state.setdefault("form_defaults", {})
st.session_state.setdefault("scenarios", {})            # name -> plan dict
st.session_state.setdefault("export_json", None)
st.session_state.setdefault("special_editor_rows", [])  # main-page specials table
st.session_state.setdefault("auto_run", False)
st.session_state.setdefault("run_now", False)
st.session_state.setdefault("username", None)           # ensure key exists

# ====== SIMPLE LOGIN (plaintext users file) ======
USERS_PATH = os.path.join("data", "users.json")

def _read_users():
    try:
        with open(USERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)  # {username: password}
    except FileNotFoundError:
        return {}

def _check_login(u: str, p: str) -> bool:
    users = _read_users()
    return bool(u) and users.get(u) == p

# ====== LOGIN GATE ======
if st.session_state["username"] is None:
    st.title("🔐 Sign in")
    u = st.text_input("Username", key="login_user")
    p = st.text_input("Password", type="password", key="login_pass")
    left, _ = st.columns([1, 4])
    with left:
        if st.button("Log in"):
            if _check_login(u, p):
                st.session_state["username"] = u
                st.success(f"Welcome, {u}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
    st.caption("Lightweight login using a local file (not for sensitive data).")
    st.stop()

# Show who is logged in + a logout
with st.sidebar:
    st.caption(f"Signed in as **{st.session_state['username']}**")
    if st.button("Logout"):
        st.session_state["username"] = None
        st.rerun()

# ====== SIMPLE PER-USER STORAGE (JSON files) ======
def _user_dir(username: str) -> str:
    d = os.path.join("data", "users", username)
    os.makedirs(d, exist_ok=True)
    return d

def _scenarios_path(username: str) -> str:
    return os.path.join(_user_dir(username), "scenarios.json")

def save_user_scenario(username: str, scenario_name: str, plan: dict):
    path = _scenarios_path(username)
    existing = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)  # list of {name, plan, ts}
    # put newest first
    existing.insert(0, {"name": scenario_name, "plan": plan, "ts": int(time.time())})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

def load_user_scenarios(username: str):
    path = _scenarios_path(username)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)  # list of {name, plan, ts}

# ---------- Helpers ----------
def save_json_button(label: str, data: dict, filename: str):
    buf = BytesIO(json.dumps(data, indent=2).encode("utf-8"))
    st.download_button(label, data=buf, file_name=filename, mime="application/json")

def _seed_widget_state_from_defaults(d: dict):
    """
    Push defaults into the actual widget keys so Streamlit updates what you see.
    """
    # profile
    st.session_state[WIDGET_KEYS["current_age"]] = d.get("current_age", 55)
    st.session_state[WIDGET_KEYS["retire_age"]] = d.get("retire_age", 65)
    st.session_state[WIDGET_KEYS["end_age"]] = d.get("end_age", 90)
    st.session_state[WIDGET_KEYS["state"]] = d.get("state", "MI")
    st.session_state[WIDGET_KEYS["filing"]] = d.get("filing_status", "single")

    # accounts
    st.session_state[WIDGET_KEYS["pre_tax_balance"]] = d.get("pre_tax_balance", 0.0)
    st.session_state[WIDGET_KEYS["pre_tax_contrib"]] = d.get("pre_tax_contrib", 0.0)
    st.session_state[WIDGET_KEYS["pre_tax_mean"]] = d.get("pre_tax_mean", 0.05)
    st.session_state[WIDGET_KEYS["pre_tax_stdev"]] = d.get("pre_tax_stdev", 0.10)

    st.session_state[WIDGET_KEYS["roth_balance"]] = d.get("roth_balance", 0.0)
    st.session_state[WIDGET_KEYS["roth_contrib"]] = d.get("roth_contrib", 0.0)
    st.session_state[WIDGET_KEYS["roth_mean"]] = d.get("roth_mean", 0.06)
    st.session_state[WIDGET_KEYS["roth_stdev"]] = d.get("roth_stdev", 0.12)

    st.session_state[WIDGET_KEYS["taxable_balance"]] = d.get("taxable_balance", 0.0)
    st.session_state[WIDGET_KEYS["taxable_contrib"]] = d.get("taxable_contrib", 0.0)
    st.session_state[WIDGET_KEYS["taxable_mean"]] = d.get("taxable_mean", 0.06)
    st.session_state[WIDGET_KEYS["taxable_stdev"]] = d.get("taxable_stdev", 0.12)

    st.session_state[WIDGET_KEYS["cash_balance"]] = d.get("cash_balance", 0.0)

    # income & expenses
    st.session_state[WIDGET_KEYS["salary"]] = d.get("salary", 0.0)
    st.session_state[WIDGET_KEYS["salary_growth"]] = round(d.get("salary_growth", 3.0), 3)  # percent
    st.session_state[WIDGET_KEYS["baseline_expenses"]] = d.get("baseline_expenses", 0.0)

    # SS
    st.session_state[WIDGET_KEYS["ss_pia"]] = d.get("ss_pia", 0.0)
    st.session_state[WIDGET_KEYS["ss_claim_age"]] = d.get("ss_claim_age", 67)

    # Roth conversions
    st.session_state[WIDGET_KEYS["rc_cap"]] = d.get("rc_cap", 0.0)
    st.session_state[WIDGET_KEYS["rc_start_age"]] = d.get("rc_start_age", 55)
    st.session_state[WIDGET_KEYS["rc_end_age"]] = d.get("rc_end_age", 70)
    st.session_state[WIDGET_KEYS["rc_tax_rate"]] = d.get("rc_tax_rate", 0.22)
    st.session_state[WIDGET_KEYS["rc_pay_from_taxable"]] = d.get("rc_pay_from_taxable", True)

    # assumptions & sim
    st.session_state[WIDGET_KEYS["returns_correlated"]] = d.get("returns_correlated", True)
    st.session_state[WIDGET_KEYS["n_paths"]] = int(d.get("n_paths", 1000))

def load_plan_into_state(plan_dict: dict):
    """Load a JSON plan, seed defaults + widget keys, and rerun UI."""
    st.session_state["plan"] = plan_dict

    acc = plan_dict.get("accounts", {})
    income = plan_dict.get("income", {})
    expenses = plan_dict.get("expenses", {})
    ss = plan_dict.get("social_security", {})
    rc = plan_dict.get("roth_conversion", {})
    asm = plan_dict.get("assumptions", {})

    defaults = {
        # profile
        "current_age": plan_dict.get("current_age", 55),
        "retire_age": plan_dict.get("retire_age", 65),
        "end_age": plan_dict.get("end_age", 90),
        "state": plan_dict.get("state", "MI"),
        "filing_status": plan_dict.get("filing_status", "single"),
        # accounts
        "pre_tax_balance": acc.get("pre_tax", {}).get("balance", 0.0),
        "pre_tax_contrib": acc.get("pre_tax", {}).get("contribution", 0.0),
        "pre_tax_mean": acc.get("pre_tax", {}).get("mean_return", 0.05),
        "pre_tax_stdev": acc.get("pre_tax", {}).get("stdev_return", 0.10),
        "roth_balance": acc.get("roth", {}).get("balance", 0.0),
        "roth_contrib": acc.get("roth", {}).get("contribution", 0.0),
        "roth_mean": acc.get("roth", {}).get("mean_return", 0.06),
        "roth_stdev": acc.get("roth", {}).get("stdev_return", 0.12),
        "taxable_balance": acc.get("taxable", {}).get("balance", 0.0),
        "taxable_contrib": acc.get("taxable", {}).get("contribution", 0.0),
        "taxable_mean": acc.get("taxable", {}).get("mean_return", 0.06),
        "taxable_stdev": acc.get("taxable", {}).get("stdev_return", 0.12),
        "cash_balance": acc.get("cash", {}).get("balance", 0.0),
        # income & expenses
        "salary": income.get("salary", 0.0),
        "salary_growth": round(income.get("salary_growth", 0.03) * 100.0, 3),
        "baseline_expenses": expenses.get("baseline", 0.0),
        "special_list": expenses.get("special", []),   # for main-page editor
        # SS
        "ss_pia": ss.get("PIA", 0.0),
        "ss_claim_age": ss.get("claim_age", 67),
        # Roth conversions
        "rc_cap": rc.get("annual_cap", 0.0),
        "rc_start_age": rc.get("start_age", 55),
        "rc_end_age": rc.get("end_age", 70),
        "rc_tax_rate": rc.get("tax_rate", 0.22),
        "rc_pay_from_taxable": rc.get("pay_tax_from_taxable", True),
        # assumptions
        "returns_correlated": asm.get("returns_correlated", True),
        # sim settings
        "n_paths": plan_dict.get("_sim", {}).get("n_paths", 1000),
    }

    st.session_state["form_defaults"] = defaults
    st.session_state["special_editor_rows"] = list(defaults.get("special_list", []))

    # CRITICAL: write directly into the widget keys so values update on-screen
    _seed_widget_state_from_defaults(defaults)

    st.rerun()

def add_scenario(name: str, base_plan: dict, mutate_fn=None):
    """Clone a plan, optionally mutate it, and store as a named scenario."""
    p = deepcopy(base_plan)
    if mutate_fn:
        mutate_fn(p)
    st.session_state["scenarios"][name] = p

def scenario_kpis(name: str, results: dict) -> dict:
    return {
        "Scenario": name,
        "Success %": f"{results['success_prob']*100:.1f}%",
        "Median Terminal NW": f"${results['median_terminal']:,.0f}",
    }

# ---------- Sidebar: Save / Load ----------
with st.sidebar:
    st.markdown("### Save / Load Plan")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Save current"):
            st.session_state["export_json"] = json.dumps(st.session_state.get("plan", {}), indent=2)
    with c2:
        uploaded = st.file_uploader("Load Plan (JSON)", type=["json"], label_visibility="collapsed")
    if uploaded:
        try:
            plan_dict = json.load(uploaded)
            load_plan_into_state(plan_dict)
        except Exception as e:
            st.error(f"Failed to load plan: {e}")

    if st.session_state.get("export_json"):
        st.download_button("⬇️ Download JSON",
                           data=st.session_state["export_json"].encode("utf-8"),
                           file_name="plan.json",
                           mime="application/json")

# --- Per-user Save / Load (account) ---
with st.sidebar.expander("💾 My Account (Save/Load)", expanded=False):
    new_name = st.text_input("Scenario name", value="My Plan", key="acct_scn_name")
    if st.button("Save current to my account"):
        save_user_scenario(st.session_state["username"], new_name, st.session_state.get("plan", {}))
        st.success(f"Saved as '{new_name}'")
        st.rerun()

    mine = load_user_scenarios(st.session_state["username"])
    if mine:
        labels = [f"{i+1}. {row['name']}" for i, row in enumerate(mine)]
        idx = st.selectbox("Load one of your saved plans", options=list(range(len(mine))),
                           format_func=lambda i: labels[i])
        if st.button("Load selected"):
            load_plan_into_state(mine[idx]["plan"])
    else:
        st.caption("You haven't saved any plans yet.")

# ---------- Sidebar: Inputs + Auto-run toggle ----------
with st.sidebar:
    st.markdown("---")
    st.markdown("### Inputs")
    st.session_state["auto_run"] = st.checkbox(
        "Auto-run when inputs change", value=False,
        help="When off, use the Run button on the main page."
    )

# Build plan from the sidebar form (the form writes to the SIDEBAR)
plan_from_form = plan_form()
if plan_from_form:
    # merge in specials from main-page editor
    edited_specials = st.session_state.get("special_editor_rows", [])
    plan_from_form.setdefault("expenses", {})
    plan_from_form["expenses"]["special"] = edited_specials
    st.session_state["plan"] = plan_from_form

plan = st.session_state.get("plan", {})

# ---------- Main UI ----------
st.title("📈 Retirement Planning Dashboard")

# Quick guide for the user
with st.container():
    st.markdown("""
    ### What am I editing?
    - **Profile & Accounts** → in the **sidebar** (left).
    - **Social Security** → set **claiming age** and PIA in the sidebar.
    - **Roth Conversion Controls** → choose **annual cap**, **start/end ages**, and **target tax rate** in the sidebar.
    - **Special Expenses** → add unlimited one-offs **below** on this page.
    """)

# Special Expenses Editor (main page)
st.subheader("Special Expenses Editor")
st.caption("Add unlimited one-off expenses. These are included in simulations.")
specials = st.session_state.get("special_editor_rows", [])
col_add, col_clear = st.columns([1,1])
with col_add:
    if st.button("➕ Add row"):
        specials.append({"label": "", "age": 30, "amount": 0.0})
with col_clear:
    if st.button("🧹 Clear all"):
        specials = []
new_rows = []
for i, row in enumerate(specials):
    with st.expander(f"Item {i+1}" if row.get("label","") == "" else f"{i+1} • {row.get('label','')}", expanded=False):
        lbl = st.text_input(f"Label {i+1}", value=row.get("label",""), key=f"se_lbl_{i}")
        age = st.number_input(f"Age {i+1}", min_value=18, max_value=120, value=int(row.get("age", 30)), key=f"se_age_{i}")
        amt = st.number_input(f"Amount {i+1} ($)", min_value=0.0, value=float(row.get("amount", 0.0)), key=f"se_amt_{i}", step=100.0)
        new_rows.append({"label": lbl, "age": int(age), "amount": float(amt)})
st.session_state["special_editor_rows"] = new_rows

st.markdown("---")

# Quick scenario buttons
st.subheader("Quick Scenarios")
c1, c2, c3 = st.columns([1,1,6])
with c1:
    if st.button("Roth ladder → 22% bracket"):
        def _ladder(p):
            p.setdefault("roth_conversion", {})
            p["roth_conversion"]["annual_cap"] = 10_000_000.0  # effectively unlimited
            p["roth_conversion"]["tax_rate"] = 0.22
        add_scenario("Roth ladder to 22%", plan, _ladder)
with c2:
    if st.button("Claim Social Security at 70"):
        def _ss70(p):
            p.setdefault("social_security", {})
            p["social_security"]["claim_age"] = 70
        add_scenario("SS at 70", plan, _ss70)

if st.session_state["scenarios"]:
    st.success(f"Saved scenarios: {', '.join(st.session_state['scenarios'].keys())}")

# Need a plan to run
if not plan:
    st.info("Load a plan or fill in the sidebar, then rerun.")
    st.stop()

# --- Run control ---
st.markdown("### Run")
run_clicked = st.button("▶ Run simulation", type="primary", help="Click to run the Monte Carlo with current inputs.")
if run_clicked:
    st.session_state["run_now"] = True
    st.rerun()

should_run = st.session_state.get("auto_run", False) or st.session_state.get("run_now", False)

if not should_run:
    st.info("Simulation is paused. Adjust inputs in the sidebar, then click **Run simulation** (or enable **Auto-run**).")
    st.stop()

# Clear the one-shot flag for next render
st.session_state["run_now"] = False

# --- Simulation ---
n_paths = plan.get("_sim", {}).get("n_paths", 1000)
with st.spinner("Running Monte Carlo..."):
    results = monte_carlo.simulate(plan, n_paths=n_paths, seed=42)

# KPI + Charts
k1, k2, k3 = st.columns([1, 2, 2], vertical_alignment="center")
with k1:
    st.subheader("Success Probability")
    st.plotly_chart(success_gauge(results["success_prob"]), use_container_width=True)
    st.metric("Median terminal net worth", f"${results['median_terminal']:,.0f}")
with k2:
    st.subheader("Net Worth (Percentile Fan)")
    st.plotly_chart(
        fan_chart(results["ages"], results["networth_p10"], results["networth_p50"], results["networth_p90"]),
        use_container_width=True,
    )
with k3:
    st.subheader("Account Balances (Median Path)")
    st.plotly_chart(
        account_area_chart(results["ages"], results["acct_series_median"]),
        use_container_width=True,
    )

# Median ledger
st.markdown("### Ledger (Median Path)")
df = pd.DataFrame(results["ledger_median"])
st.dataframe(df, use_container_width=True, height=350)
st.download_button("⬇️ CSV (median ledger)", data=df.to_csv(index=False).encode("utf-8"),
                   file_name="ledger_median.csv", mime="text/csv")

# Scenario compare
if st.session_state["scenarios"]:
    st.markdown("### Scenario Compare")
    rows = []
    for name, sc_plan in st.session_state["scenarios"].items():
        sc_res = monte_carlo.simulate(sc_plan, n_paths=n_paths, seed=123)
        rows.append(scenario_kpis(name, sc_res))
    sc_df = pd.DataFrame(rows)
    st.dataframe(sc_df, use_container_width=True)
    st.download_button("⬇️ Scenario KPIs (CSV)",
                       data=sc_df.to_csv(index=False).encode("utf-8"),
                       file_name="scenario_kpis.csv", mime="text/csv")
