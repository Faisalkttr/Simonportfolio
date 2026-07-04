"""
app.py — Sovereignty Portfolio Operating System dashboard

Reads portfolio_state.json (produced by engine.py, refreshed by GitHub Actions)
and renders it as an interactive Streamlit dashboard. Deploy for free on
Streamlit Community Cloud.
"""

import streamlit as st
import json
import pandas as pd

st.set_page_config(page_title="Sovereignty Engine OS", layout="wide", page_icon="🏛️")

st.title("🏛️ Sovereignty Portfolio Operating System")
st.subheader("Automated Scoring, Tier Allocation, and Deployment Rule Book")

# ---- Load state ----
try:
    with open("portfolio_state.json", "r") as f:
        state = json.load(f)
    df = pd.DataFrame(state["assets"])
    generated_at = state.get("generated_at_utc", "unknown")
except FileNotFoundError:
    st.error(
        "No portfolio_state.json found yet. Run `python engine.py` locally, "
        "or wait for the scheduled GitHub Action to generate it."
    )
    st.stop()

st.caption(f"Last recalculated: {generated_at}")

if df.empty:
    st.warning("portfolio_state.json exists but contains no assets. Check schema.yaml.")
    st.stop()

# ---- Data quality banner ----
stale = df[df["data_quality"] != "ok"]
if not stale.empty:
    st.warning(
        f"⚠️ {len(stale)} ticker(s) fell back to default scores this run "
        f"(data fetch issue): {', '.join(stale['ticker'].tolist())}"
    )

# ---- Top metric cards ----
c1, c2, c3 = st.columns(3)
c1.metric("🔥 Tier 1 — Accumulate Heavy", len(df[df["tier"].str.contains("Tier 1")]))
c2.metric("🟡 Tier 2 — Maintenance DCA", len(df[df["tier"].str.contains("Tier 2")]))
c3.metric("🛑 Tier 3 — Capped / Trim", len(df[df["tier"].str.contains("Tier 3")]))

# ---- Sidebar filters ----
st.sidebar.header("Filters")
section_filter = st.sidebar.multiselect(
    "Sleeve (section)", options=sorted(df["section"].unique()), default=sorted(df["section"].unique())
)
tier_filter = st.sidebar.multiselect(
    "Tier", options=sorted(df["tier"].unique()), default=sorted(df["tier"].unique())
)
sort_by = st.sidebar.selectbox(
    "Sort by", options=["composite_score", "ticker", "opportunity_score", "heat_risk_score"], index=0
)

filtered_df = df[df["section"].isin(section_filter) & df["tier"].isin(tier_filter)]
filtered_df = filtered_df.sort_values(sort_by, ascending=False)

# ---- Main table ----
st.markdown("### 📋 Active Allocation & Capital Execution Rules")
st.dataframe(
    filtered_df,
    column_config={
        "ticker": "Ticker",
        "section": "Sleeve",
        "layer": "Portfolio Layer",
        "price": st.column_config.NumberColumn("Price ($)", format="$%.2f"),
        "quality_score": st.column_config.ProgressColumn("Quality", min_value=0, max_value=100),
        "valuation_score": st.column_config.ProgressColumn("Valuation", min_value=0, max_value=100),
        "opportunity_score": st.column_config.ProgressColumn("Opportunity", min_value=0, max_value=100),
        "heat_risk_score": st.column_config.ProgressColumn("Heat Risk (inverted)", min_value=0, max_value=100),
        "composite_score": st.column_config.NumberColumn("Composite (0-100)", format="%.1f"),
        "tier": "Tier",
        "suggested_action": "Deployment Rule",
        "data_quality": None,  # hide raw column, shown via banner above instead
    },
    hide_index=True,
    use_container_width=True,
)

# ---- Tier 1 spotlight ----
st.markdown("---")
st.markdown("### ⚡ This Month's Deployment Priorities (Tier 1)")
t1_df = filtered_df[filtered_df["tier"].str.contains("Tier 1")]
if not t1_df.empty:
    for _, row in t1_df.iterrows():
        st.success(
            f"**{row['ticker']}** ({row['section']} · {row['layer']}) — "
            f"{row['suggested_action']} | Composite score: **{row['composite_score']}**"
        )
else:
    st.info("No assets currently qualify for Tier 1 this run. Keep accumulating baseline cash reserves.")

st.markdown("### 🛑 Avoid New Capital (Tier 3)")
t3_df = filtered_df[filtered_df["tier"].str.contains("Tier 3")]
if not t3_df.empty:
    st.dataframe(
        t3_df[["ticker", "section", "layer", "composite_score"]],
        hide_index=True,
        use_container_width=True,
    )
else:
    st.info("No assets flagged as overextended this run.")

st.markdown("---")
st.caption(
    "This tool produces a mechanical, rules-based score from free public data. "
    "It is not financial advice — verify fundamentals, valuation, and your own "
    "position caps before deploying capital."
)
