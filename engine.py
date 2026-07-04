
import yaml
import json
import datetime
import yfinance as yf
import pandas as pd

# 🔴 IMPORT YOUR MACRO ENGINE
from Execution_Engine_fixed_Claude import (
    macro_score,
    macro_phase_v2,
    governed_target,
    tilted_grid
)

SCHEMA_PATH = "schema.yaml"
STATE_PATH = "portfolio_state.json"

TIER_WEIGHTS = {
    "Tier 1": 1.0,
    "Tier 2": 0.5,
    "Tier 3": 0.0
}

CLUSTER_MAP = {
    "INFRA": "INFRA",
    "ENERGY_COMMODITY": "ENERGY_COMMODITY",
    "AI_SEMIS": "AI_SEMIS",
    "EM": "EM"
}


# ----------------------------
# LOAD WATCHLIST
# ----------------------------
def load_schema():
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)


# ----------------------------
# METRIC CALCULATION
# ----------------------------
def survivability_score(info):
    dte = info.get("debtToEquity", None)

    if dte is None:
        return 50
    if dte < 50:
        return 90
    elif dte < 100:
        return 70
    else:
        return 40


def calculate_metrics(symbol):
    try:
        t = yf.Ticker(symbol)
        info = t.info
        hist = t.history(period="3mo")

        price = hist["Close"].iloc[-1]

        pe = info.get("forwardPE") or info.get("trailingPE") or 25
        valuation = max(0, min(100, 100 - (pe * 2)))

        roe = info.get("returnOnEquity") or 0.15
        quality = max(0, min(100, roe * 400))

        ma = hist["Close"].mean()
        opportunity = max(0, min(100, 50 + ((ma - price) / ma) * 200))

        delta = hist["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs.iloc[-1]))
        heat = 100 - rsi if not pd.isna(rsi) else 50

        surv = survivability_score(info)

        return price, quality, valuation, opportunity, heat, surv, True

    except:
        return 0, 50, 50, 50, 50, 50, False


# ----------------------------
# BASE SCORING
# ----------------------------
def composite_score(q, v, o, h, s):
    return (
        q * 0.25 +
        v * 0.15 +
        o * 0.20 +
        h * 0.10 +
        s * 0.30
    )


# ----------------------------
# MACRO TIER DISTORTION
# ----------------------------
def adjust_score_for_macro(score):
    # 🔴 Contraction → suppress scores
    if macro_score < -20:
        score *= 0.85

    # 🔴 Expansion → boost top names
    elif macro_score > 40:
        score *= 1.10

    return score


def determine_tier(score):
    if score >= 75:
        return "Tier 1"
    elif score >= 55:
        return "Tier 2"
    else:
        return "Tier 3"


# ----------------------------
# MAIN ENGINE
# ----------------------------
def run():

    schema = load_schema()

    rows = []

    # ----------------------------
    # STEP 1: SCORE ALL TICKERS
    # ----------------------------
    for section in schema["sections"]:
        section_name = section["name"]

        for layer in section["layers"]:
            for ticker in layer["permissible_assets"]:

                price, q, v, o, h, s, ok = calculate_metrics(ticker)

                base = composite_score(q, v, o, h, s)
                adj = adjust_score_for_macro(base)

                tier = determine_tier(adj)

                rows.append({
                    "ticker": ticker,
                    "section": section_name,
                    "score": round(adj, 1),
                    "tier": tier,
                    "data_ok": ok
                })

    df = pd.DataFrame(rows)

    # ----------------------------
    # STEP 2: ALLOCATE WITHIN EACH SECTOR
    # ----------------------------
    allocations = []

    for section_name, group in df.groupby("section"):

        sector_weight = tilted_grid.get(section_name, 0)

        # Tier weights inside sector
        weights = group["tier"].map(TIER_WEIGHTS)
        total_weight = weights.sum()

        if total_weight == 0:
            group["final_alloc"] = 0
        else:
            normalized = weights / total_weight
            group["final_alloc"] = normalized * sector_weight

        allocations.append(group)

    df = pd.concat(allocations)

    # ----------------------------
    # STEP 3: APPLY GLOBAL RISK BUDGET
    # ----------------------------
    df["final_alloc"] = df["final_alloc"] * governed_target

    total_alloc = df["final_alloc"].sum()
    cash = round(1 - total_alloc, 4)

    # ----------------------------
    # FINAL OUTPUT
    # ----------------------------
    state = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "macro": {
            "score": macro_score,
            "phase": macro_phase_v2,
            "risk_budget": governed_target
        },
        "cash": cash,
        "assets": df.to_dict(orient="records")
    }

    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

    print("✅ Fully integrated macro allocation complete")


if __name__ == "__main__":
    run()
