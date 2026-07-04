import yaml
import json
import datetime
import yfinance as yf
import pandas as pd

SCHEMA_PATH = "schema.yaml"
STATE_PATH = "portfolio_state.json"
MACRO_PATH = "macro_state.json"

TIER_WEIGHTS = {
    "Tier 1": 1.0,
    "Tier 2": 0.5,
    "Tier 3": 0.0
}

CLUSTER_MAP = {
    "INFRA": "infra",
    "ENERGY_COMMODITY": "commodity",
    "AI_SEMIS": "ai_infra",
    "EM": "em"
}


# ----------------------------
# LOADERS
# ----------------------------
def load_schema():
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)


def load_macro():
    with open(MACRO_PATH, "r") as f:
        return json.load(f)


# ----------------------------
# SCORING HELPERS
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
# MACRO ADJUSTMENTS
# ----------------------------
def macro_adjust(score, cluster, macro):
    if macro["dxy_trend"] == "rising" and cluster in ["commodity", "em"]:
        score *= 0.7

    if macro["liquidity"] == "contracting" and cluster == "ai_infra":
        score *= 0.75

    if macro["yields"] == "falling" and cluster == "infra":
        score *= 1.1

    return score


def tier(score):
    if score >= 75:
        return "Tier 1"
    elif score >= 55:
        return "Tier 2"
    return "Tier 3"


# ----------------------------
# MAIN ENGINE
# ----------------------------
def run():
    schema = load_schema()
    macro = load_macro()

    assets = []

    for section in schema["sections"]:
        cluster = CLUSTER_MAP[section["name"]]

        for layer in section["layers"]:
            for ticker in layer["permissible_assets"]:

                price, q, v, o, h, s, ok = calculate_metrics(ticker)

                base_score = (
                    q * 0.25 +
                    v * 0.15 +
                    o * 0.20 +
                    h * 0.10 +
                    s * 0.30
                )

                adj_score = macro_adjust(base_score, cluster, macro)
                t = tier(adj_score)

                assets.append({
                    "ticker": ticker,
                    "cluster": cluster,
                    "score": round(adj_score, 1),
                    "tier": t,
                    "data_ok": ok
                })

    # ----------------------------
    # ALLOCATION ENGINE
    # ----------------------------
    weights = [TIER_WEIGHTS[a["tier"]] for a in assets]
    total_weight = sum(weights) or 1

    for i, a in enumerate(assets):
        base_alloc = weights[i] / total_weight
        macro_alloc = base_alloc * macro["deployment_multiplier"]
        a["allocation"] = round(macro_alloc, 4)

    total_alloc = sum(a["allocation"] for a in assets)
    cash = round(1 - total_alloc, 4)

    state = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "macro": macro,
        "cash": cash,
        "assets": assets
    }

    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

    print("✅ Engine complete")


if __name__ == "__main__":
    run()
