# app.py
import json
from copy import deepcopy
from io import BytesIO
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from retirement_planner.calculators import monte_carlo
from retirement_planner.components.forms import plan_form, WIDGET_KEYS  # keys for sidebar widgets
from retirement_planner.components.charts import fan_chart, account_area_chart, success_gauge


# ---------- Page config ----------
st.set_page_config(
    page_title="Retirement Planner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Enhanced UI polish with MSU theme ----------
st.markdown(
    """
<style>
/* Global layout */
.block-container { 
    padding: 1.5rem 2rem; 
    max-width: 1400px; 
    margin: auto; 
}

/* Sidebar styling */
section[data-testid="stSidebar"] { 
    background-color: #E6ECE9; /* MSU-inspired light gray-green */
    padding: 1.5rem; 
    border-right: 1px solid #D1D9D6; 
}
section[data-testid="stSidebar"] h2, 
section[data-testid="stSidebar"] h3 { 
    color: #18453B; /* MSU green */
    font-weight: 600; 
    margin: 0.5rem 0; 
}

/* Cards for metrics and charts */
div[data-testid="stMetric"] { 
    background: #FFFFFF; 
    border-radius: 12px; 
    padding: 1rem; 
    box-shadow: 0 2px 8px rgba(0,0,0,0.05); 
    border: 1px solid #E6ECE9; 
    transition: transform 0.2s ease, box-shadow 0.2s ease; 
}
div[data-testid="stMetric"]:hover { 
    transform: translateY(-2px); 
    box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
}
div.stPlotlyChart { 
    background: #FFFFFF; 
    border-radius: 12px; 
    padding: 0.75rem; 
    border: 1px solid #E6ECE9; 
    box-shadow: 0 2px 8px rgba(0,0,0,0.05); 
}

/* Buttons */
button[kind="primary"] { 
    background-color: #18453B; /* MSU green */
    color: #FFFFFF; 
    border-radius: 8px; 
    padding: 0.5rem 1.25rem; 
    font-weight: 500; 
    border: none; 
    transition: background-color 0.2s ease; 
}
button[kind="primary"]:hover { 
    background-color: #2E6B5E; /* Lighter MSU green on hover */
}
.stButton>button { 
    border-radius: 8px; 
    border: 1px solid #D1D9D6; 
    color: #1A2521; 
    background-color: #FFFFFF; 
    transition: background-color 0.2s ease, color 0.2s ease; 
}
.stButton>button:hover { 
    background-color: #E6ECE9; 
    color: #18453B; 
}

/* Typography */
h1, h2, h3, h4 { 
    color: #1A2521; 
    font-weight: 600; 
}
.stCaption { 
    color: #4B5E58; /* Softer gray for captions */
}

/* Dividers */
hr { 
    border-top: 1px solid #D1D9D6; 
    margin: 1.5rem 0; 
}

/* Tables */
div[data-testid="stDataFrame"] { 
    border-radius: 12px; 
    overflow: hidden; 
    box-shadow: 0 2px 8px rgba(0,0,0,0.05); 
}

/* Smooth transitions for interactivity */
.stNumberInput, .stTextInput, .stSelectbox, .stSlider { 
    transition: all 0.2s ease; 
}
</style>
""",
    unsafe_allow_html=True,
)

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
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "retirement_planner" / "data"
USERS_PATH = DATA_DIR / "users.json"

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


# ---------- Header bar ----------
def header_bar():
    logo_path = BASE_DIR / "assets" / "logo.png"
    with st.container():
        c1, c2 = st.columns([1, 6])
        with c1:
            if logo_path.exists():
                st.image(str(logo_path), width=140)
            else:
                st.markdown("### 🟩 PlanLab")  # fallback text logo with MSU green emoji
        with c2:
            st.markdown(
                """
                ### **Retirement Planning Dashboard**  
                _Model scenarios, Monte Carlo success, taxes/RMDs, and Roth conversions._
                """
            )

header_bar()


# ====== SIMPLE PER-USER STORAGE (JSON files) ======
def _user_dir(username: str) -> Path:
    d = DATA_DIR / "users" / username
    d.mkdir(parents=True, exist_ok=True)
    return d

def _scenarios_path(username: str) -> Path:
    return _user_dir(username) / "scenarios.json"

def save_user_scenario(username: str, scenario_name: str, plan: dict):
    path = _scenarios_path(username)
    existing = []
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)  # list of {name, plan, ts}
    # put newest first
    existing.insert(0, {"name": scenario_name, "plan": plan, "ts": time.time()})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

def load_user_scenarios(username: str) -> list:
    path = _scenarios_path(username)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ====== SIDEBAR: FORM + CONTROLS ======
st.sidebar.header("Retirement Plan Inputs")
plan = plan_form()

# --- Special expenses editor (main page, not sidebar) ---
st.subheader("Special Expenses Editor")
with st.form("special_expenses_form"):
    # editable table
    specials_df = pd.DataFrame(st.session_state["special_editor_rows"], columns=["Age", "Amount"])
    edited_df = st.data_editor(
        specials_df,
        num_rows="dynamic",
        column_config={
            "Age": st.column_config.NumberColumn(
                min_value=plan["current_age"], max_value=plan["end_age"], step=1
            ),
            "Amount": st.column_config.NumberColumn(min_value=0.0, format="$%.2f")
        },
        hide_index=True,
        key="special_expenses_editor"
    )
    if st.form_submit_button("💾 Save Special Expenses"):
        st.session_state["special_editor_rows"] = edited_df.to_dict("records")
        plan["expenses"]["special"] = [
            {"age": int(row["Age"]), "amount": float(row["Amount"])}
            for row in st.session_state["special_editor_rows"]
            if pd.notna(row["Age"]) and pd.notna(row["Amount"])
        ]

# --- Sidebar: run button and scenario controls ---
st.sidebar.divider()
st.sidebar.header("Run Simulation")
left, right = st.sidebar.columns(2)
with left:
    st.session_state["auto_run"] = st.checkbox("Auto run", value=st.session_state["auto_run"])
with right:
    if st.button("Run", type="primary"):
        st.session_state["run_now"] = True

st.sidebar.header("Save/Load Scenarios")
scenario_name = st.sidebar.text_input("Scenario name")
c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("Save"):
        if scenario_name:
            save_user_scenario(st.session_state["username"], scenario_name, plan)
            st.session_state["scenarios"][scenario_name] = plan
            st.sidebar.success(f"Saved '{scenario_name}'")
        else:
            st.sidebar.error("Enter a scenario name.")
with c2:
    scenarios = load_user_scenarios(st.session_state["username"])
    options = [s["name"] for s in scenarios]
    load_name = st.selectbox("Load scenario", [""] + options)
    if load_name:
        for s in scenarios:
            if s["name"] == load_name:
                st.session_state["form_defaults"] = deepcopy(s["plan"])
                st.session_state["plan"] = deepcopy(s["plan"])
                st.session_state["special_editor_rows"] = s["plan"].get("expenses", {}).get("special", [])
                st.sidebar.success(f"Loaded '{load_name}'")
                st.rerun()

# --- JSON Export ---
st.sidebar.divider()
st.sidebar.header("Export")
if st.sidebar.button("Export JSON"):
    st.session_state["export_json"] = json.dumps(plan, indent=2)
if st.session_state.get("export_json"):
    st.sidebar.download_button(
        "⬇️ Download JSON",
        data=st.session_state["export_json"],
        file_name=f"{scenario_name or 'plan'}.json",
        mime="application/json"
    )

# ====== RUN SIMULATION ======
if st.session_state["run_now"] or st.session_state["auto_run"]:
    st.session_state["run_now"] = False
    n_paths = plan.get("_sim", {}).get("n_paths", 1000)
    with st.spinner(f"Running {n_paths:,} Monte Carlo paths..."):
        results = monte_carlo.simulate(plan, n_paths=n_paths, seed=42)


# ====== DISPLAY: HOME PAGE ======
if "results" not in locals():
    st.info("Run a simulation to see results.")
    st.stop()

st.subheader("Plan Summary")
kcol1, kcol2 = st.columns(2)
with kcol1:
    st.plotly_chart(success_gauge(results["success_prob"]), use_container_width=True)

with kcol2:
    st.metric(label="Median terminal net worth", value=f"${results['median_terminal']:,.0f}")
    st.caption("Median of ending net worth across all Monte Carlo paths.")

with kcol2:
    st.metric(label="Simulation size", value=f"{n_paths:,} paths")
    st.caption("Number of randomized return paths used (seed = 42).")

st.divider()

# --- Main charts: net worth fan + median account mix ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("Net Worth (Percentile Fan)")
    st.plotly_chart(
        fan_chart(
            results["ages"],
            results["networth_p10"],
            results["networth_p50"],
            results["networth_p90"],
        ),
        use_container_width=True,
    )

with c2:
    st.subheader("Account Balances (Median Path)")
    st.plotly_chart(
        account_area_chart(
            results["ages"],
            results["acct_series_median"],
        ),
        use_container_width=True,
    )

# --- Conversions bar chart (makes conversion effects obvious) ---
if "ledger_median" in results and any(r.get("roth_conversion", 0) for r in results["ledger_median"]):
    import plotly.graph_objects as go
    ages_bar = [r["age"] for r in results["ledger_median"]]
    convs = [r.get("roth_conversion", 0.0) for r in results["ledger_median"]]
    fig_conv = go.Figure(go.Bar(x=ages_bar, y=convs, name="Roth conversions"))
    fig_conv.update_layout(
        template="plotly_white", height=260, title="Roth Conversions (Median Path)",
        xaxis_title="Age", yaxis_title="Dollars"
    )
    st.plotly_chart(fig_conv, use_container_width=True)

# --- Roth conversions bar (Median Path) ---
try:
    lm = results.get("ledger_median", [])
    # If items are strings (e.g., serialized rows), try to JSON-decode them.
    if lm and isinstance(lm[0], str):
        import json as _json
        decoded = []
        for s in lm:
            if isinstance(s, str):
                try:
                    decoded.append(_json.loads(s))
                except Exception:
                    # keep the original string if it can't be parsed; we'll filter below
                    decoded.append(s)
            else:
                decoded.append(s)
        lm = decoded

    # Keep only dict rows; skip anything malformed
    lm_rows = [r for r in lm if isinstance(r, dict)]

    if lm_rows:
        ages_bar = [r.get("age") for r in lm_rows]
        convs = [float(r.get("roth_conversion", 0.0) or 0.0) for r in lm_rows]

        # Only draw if any conversion is non-zero
        if any(c != 0 for c in convs):
            import plotly.graph_objects as go
            fig = go.Figure(go.Bar(x=ages_bar, y=convs, name="Roth conversions"))
            fig.update_layout(
                template="plotly_white",
                height=260,
                title="Roth Conversions (Median Path)",
                xaxis_title="Age",
                yaxis_title="Dollars",
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
except Exception as _e:
    # Don't crash the app if something unexpected happens; surface a gentle note instead.
    st.caption("Roth conversion chart unavailable for this run.")

# --- Median ledger ---
st.markdown("### Ledger (Median Path)")
lm = results.get("ledger_median", [])

# If rows are strings, try to decode; otherwise keep as-is
if lm and isinstance(lm[0], str):
    import json as _json
    tmp = []
    for s in lm:
        if isinstance(s, str):
            try:
                tmp.append(_json.loads(s))
            except Exception:
                tmp.append({"row": s})
        else:
            tmp.append(s)
    lm = tmp

# Build a DataFrame from dict-like rows if possible; else fallback
dict_rows = [r for r in lm if isinstance(r, dict)]
df = pd.DataFrame(dict_rows) if dict_rows else pd.DataFrame(lm, columns=["row"])

st.dataframe(df, use_container_width=True, height=350)
st.download_button(
    "⬇️ CSV (median ledger)",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="ledger_median.csv",
    mime="text/csv",
)