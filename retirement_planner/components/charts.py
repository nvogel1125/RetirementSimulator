# components/charts.py
# Plotly chart helpers used across the app.
# All functions return a Plotly Figure that Streamlit can display with st.plotly_chart(...).

from typing import Dict, List, Sequence
import plotly.graph_objects as go

import plotly.io as pio
pio.templates.default = "plotly_white"


# ---------- Net worth "fan" ----------
def fan_chart(ages: Sequence[int],
              p10: Sequence[float],
              p50: Sequence[float],
              p90: Sequence[float],
              title: str = "Net Worth (Percentile Fan)") -> go.Figure:
    """Shaded 10–90 band with a median line."""
    n = len(ages)
    p10 = _fit(p10, n)
    p50 = _fit(p50, n)
    p90 = _fit(p90, n)

    fig = go.Figure()

    # Shaded band 10–90
    fig.add_trace(go.Scatter(
        x=ages, y=p90, mode="lines", line=dict(width=0),
        hoverinfo="skip", showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=ages, y=p10, mode="lines", line=dict(width=0),
        fill="tonexty", name="10–90%",
        hovertemplate="Age %{x}<br>$%{y:,.0f}<extra></extra>"
    ))

    # Median
    fig.add_trace(go.Scatter(
        x=ages, y=p50, mode="lines", name="Median",
        hovertemplate="Age %{x}<br>$%{y:,.0f}<extra></extra>"
    ))

    fig.update_layout(
        title=title,
        template="plotly_white",
        height=380,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="Age",
        yaxis_title="Dollars (nominal)"
    )
    return fig


# ---------- Account balances (stacked) ----------
def _fit(series, n):
    arr = list(series)
    if len(arr) < n: arr += [0.0] * (n - len(arr))
    return arr[:n]

def account_area_chart(ages, series_dict, title="Account Balances (Median Path)"):
    n = len(ages)
    order = ["taxable", "pre_tax", "roth", "cash"]
    fig = go.Figure()
    for k in order:
        if k in series_dict:
            y = _fit(series_dict[k], n)
            fig.add_trace(go.Scatter(
                x=ages, y=y, mode="lines", name=k.replace("_", " ").title(),
                stackgroup="one",
                hovertemplate="Age %{x}<br>$%{y:,.0f}<extra></extra>"
            ))
    fig.update_layout(
        title=title, template="plotly_white", height=380,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="Age", yaxis_title="Dollars (nominal)"
    )
    return fig


# ---------- Success gauge ----------
def success_gauge(success_prob: float) -> go.Figure:
    pct = max(0.0, min(100.0, float(success_prob) * 100.0))  # clamp 0–100
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(pct, 1),
        number={"suffix": "%"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"thickness": 0.35},
            "steps": [
                {"range": [0, 60],  "color": "#ef4444"},  # red-500
                {"range": [60, 80], "color": "#f59e0b"},  # amber-500
                {"range": [80, 100],"color": "#22c55e"},  # green-500
            ],
        }
    ))
    fig.update_layout(template="plotly_white", height=220, margin=dict(l=10, r=10, t=10, b=10))
    return fig


# ---------- Taxes over time (stacked bars) ----------
def tax_chart(ages: Sequence[int],
              taxes_dict: Dict[str, Sequence[float]],
              title: str = "Taxes Over Time") -> go.Figure:
    """
    Stacked bars for taxes.
    Accepts any of: 'ordinary', 'cap_gains', 'niit', 'state' (lists per age).
    Missing keys are treated as zeros. Lists are padded/trimmed to ages length.
    """
    n = len(ages)

    def vec(key: str) -> List[float]:
        arr = list(taxes_dict.get(key, []))
        if len(arr) < n:
            arr = arr + [0.0] * (n - len(arr))
        return arr[:n]

    fig = go.Figure()
    # Add in a consistent order
    fig.add_bar(x=ages, y=vec("ordinary"),  name="Ordinary")
    fig.add_bar(x=ages, y=vec("cap_gains"), name="Cap gains")
    fig.add_bar(x=ages, y=vec("niit"),      name="NIIT")
    fig.add_bar(x=ages, y=vec("state"),     name="State")

    fig.update_layout(
        barmode="stack",
        title=title,
        template="plotly_white",
        height=380,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="Age",
        yaxis_title="Dollars (nominal)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


# ---------- Generic heatmap (Roth Conversion Explorer, etc.) ----------
def heatmap(z_matrix: Sequence[Sequence[float]],
            x_labels: Sequence,
            y_labels: Sequence,
            title: str = "Heatmap",
            colorbar_title: str = "Value") -> go.Figure:
    """
    Render a numeric matrix as a heatmap.
    - z_matrix is 2D (rows align with y_labels; cols align with x_labels)
    - x_labels: column labels (e.g., ages/years/brackets)
    - y_labels: row labels (e.g., conversion rules)
    """
    fig = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=x_labels,
        y=y_labels,
        hoverongaps=False,
        colorbar=dict(title=colorbar_title),
        zauto=True  # let plotly set a reasonable scale from data
    ))
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=420,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_title="",
        yaxis_title=""
    )
    return fig
