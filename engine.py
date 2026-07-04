"""
engine.py — Sovereignty Portfolio Operating System

Fetches free market data via yfinance, computes a composite score per ticker
using section-specific weighting (quality / valuation / opportunity / heat-risk),
assigns a tier, and writes portfolio_state.json for the Streamlit dashboard to read.

Run manually:
    python engine.py

Run automatically:
    See .github/workflows/run_engine.yml (scheduled via GitHub Actions)
"""

import yaml
import json
import datetime
import yfinance as yf
import pandas as pd
import numpy as np

SCHEMA_PATH = "schema.yaml"
STATE_PATH = "portfolio_state.json"

FAMILY_WEIGHTS = {
    "INFRA": {"quality": 0.40, "valuation": 0.25, "opportunity": 0.20, "heat_risk": 0.15},
    "ENERGY_COMMODITY": {"quality": 0.25, "valuation": 0.25, "opportunity": 0.30, "heat_risk": 0.20},
    "AI_SEMIS": {"quality": 0.35, "valuation": 0.20, "opportunity": 0.20, "heat_risk": 0.25},
    "EM": {"quality": 0.30, "valuation": 0.20, "opportunity": 0.25, "heat_risk": 0.25},
}
DEFAULT_WEIGHTS = {"quality": 0.25, "valuation": 0.25, "opportunity": 0.25, "heat_risk": 0.25}


def load_schema():
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)


def calculate_metrics(ticker_symbol: str) -> dict:
    """Fetch free data from Yahoo Finance and compute the four scoring inputs."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        hist = ticker.history(period="3mo")

        if hist.empty:
            raise ValueError("No price history returned")

        # 1. Valuation score — lower P/E scores higher (naive; refine per-sector later)
        pe = info.get("forwardPE") or info.get("trailingPE") or 25
        val_score = max(0, min(100, 100 - (pe * 2)))

        # 2. Quality score — return on equity as a rough proxy
        roe = info.get("returnOnEquity") or 0.15
        quality_score = max(0, min(100, roe * 400))

        # 3. Heat-risk score — 14-day RSI; high RSI = more "overbought" = lower score
        if len(hist) > 14:
            delta = hist["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs.iloc[-1]))
            if pd.isna(rsi):
                rsi = 50
        else:
            rsi = 50
        heat_risk_score = max(0, min(100, 100 - rsi))

        # 4. Opportunity score — pullback below 50-day mean = higher opportunity
        ma_50 = hist["Close"].mean()
        current_price = hist["Close"].iloc[-1]
        opp_score = max(0, min(100, 50 + ((ma_50 - current_price) / ma_50) * 200))

        return {
            "current_price": float(current_price),
            "quality": int(quality_score),
            "valuation": int(val_score),
            "opportunity": int(opp_score),
            "heat_risk": int(heat_risk_score),
            "data_ok": True,
        }
    except Exception as e:
        print(f"[warn] Could not fully fetch {ticker_symbol}: {e}")
        return {
            "current_price": 0.0,
            "quality": 50,
            "valuation": 50,
            "opportunity": 50,
            "heat_risk": 50,
            "data_ok": False,
        }


def tier_from_score(comp_score: float) -> tuple[str, str]:
    if comp_score >= 75:
        return "Tier 1: Accumulate Heavy", "Deploy 50-70% of that sleeve's new capital"
    elif comp_score >= 55:
        return "Tier 2: Maintenance DCA", "Deploy 30-50% of that sleeve's new capital"
    else:
        return "Tier 3: Strictly Capped / Trim", "Halt new buying this month / consider trim"


def evaluate_portfolio():
    schema = load_schema()
    outputs = []

    for section in schema["sections"]:
        sec_name = section["name"]
        weights = FAMILY_WEIGHTS.get(sec_name, DEFAULT_WEIGHTS)

        for layer in section["layers"]:
            for ticker_symbol in layer["permissible_assets"]:
                metrics = calculate_metrics(ticker_symbol)

                comp_score = (
                    metrics["quality"] * weights["quality"]
                    + metrics["valuation"] * weights["valuation"]
                    + metrics["opportunity"] * weights["opportunity"]
                    + metrics["heat_risk"] * weights["heat_risk"]
                )

                tier, action = tier_from_score(comp_score)

                outputs.append(
                    {
                        "ticker": ticker_symbol,
                        "section": sec_name,
                        "layer": layer["name"],
                        "price": round(metrics["current_price"], 2),
                        "quality_score": metrics["quality"],
                        "valuation_score": metrics["valuation"],
                        "opportunity_score": metrics["opportunity"],
                        "heat_risk_score": metrics["heat_risk"],
                        "composite_score": round(comp_score, 1),
                        "tier": tier,
                        "suggested_action": action,
                        "data_quality": "ok" if metrics["data_ok"] else "fallback_defaults_used",
                    }
                )

    state = {
        "generated_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "assets": outputs,
    }

    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)

    print(f"Wrote {len(outputs)} scored assets to {STATE_PATH}")


if __name__ == "__main__":
    evaluate_portfolio()
