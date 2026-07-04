import streamlit as st
import json
import pandas as pd

st.set_page_config(layout="wide")

st.title("🏛️ Sovereign Allocation Engine")

with open("portfolio_state.json") as f:
    state = json.load(f)

macro = state["macro"]

st.subheader("🧠 Macro Regime")
st.json(macro)

st.subheader("💵 Cash Level")
st.metric("Cash", f"{state['cash']*100:.1f}%")

df = pd.DataFrame(state["assets"])

st.subheader("📊 Allocation Table")
st.dataframe(df)

tier1 = df[df["tier"] == "Tier 1"]

st.subheader("🔥 Tier 1 Opportunities")
st.dataframe(tier1)
