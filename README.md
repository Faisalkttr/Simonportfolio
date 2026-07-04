# Sovereignty Portfolio Operating System

A free, serverless portfolio scoring and tiering dashboard for a DCA-style
infrastructure/AI-power/EM watchlist. Runs entirely on free tiers:

- **GitHub** — stores the schema (`schema.yaml`) and computed state (`portfolio_state.json`)
- **GitHub Actions** — free scheduled compute (cron) to refresh scores
- **Streamlit Community Cloud** — free hosting for the dashboard UI
- **yfinance** — free market data, no API key required

## Repository structure

```
├── .github/
│   └── workflows/
│       └── run_engine.yml      # Scheduled scoring job (weekdays, midnight UTC)
├── app.py                      # Streamlit dashboard
├── engine.py                   # Scoring + tier assignment logic
├── schema.yaml                 # Your watchlist, sections, layers, deployment rules
├── portfolio_state.json        # Generated output (auto-committed by Actions)
├── requirements.txt            # Python dependencies
├── .gitignore
└── README.md
```

## 1. Create the GitHub repository

1. Go to [github.com/new](https://github.com/new) and create a new repository
   (private or public — private is fine, everything here still runs free).
   Suggested name: `sovereignty-engine`.
2. Do **not** initialize with a README (you already have one in this zip).
3. On your machine, unzip this archive, then from inside the folder run:

```bash
git init
git add .
git commit -m "Initial commit: Sovereignty Portfolio Operating System"
git branch -M main
git remote add origin https://github.com/<your-username>/sovereignty-engine.git
git push -u origin main
```

## 2. Customize your watchlist

Edit `schema.yaml`:
- Add/remove tickers under `permissible_assets` in each layer.
- Adjust `position_caps.overrides` with your actual long-term max position
  sizes per ticker (as a % of total portfolio) once you're ready to wire in
  cap-awareness.
- The four sections (`INFRA`, `ENERGY_COMMODITY`, `AI_SEMIS`, `EM`) each map
  to a distinct scoring-weight profile inside `engine.py`'s `FAMILY_WEIGHTS`
  dict — tune those weights to match how much you personally weight quality
  vs. valuation vs. pullback opportunity vs. overbought risk for each sleeve.

## 3. Run the engine locally (optional, to test before automating)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python engine.py
```

This writes/overwrites `portfolio_state.json` with fresh scores.

## 4. Turn on the automated GitHub Actions schedule

Nothing extra to configure — `.github/workflows/run_engine.yml` is already
wired to your default `GITHUB_TOKEN` permissions (`contents: write`) so it
can commit the refreshed `portfolio_state.json` back to the repo.

- It runs automatically every weekday at midnight UTC.
- You can also trigger it manually: go to your repo → **Actions** tab →
  **Run Portfolio Calculation Engine** → **Run workflow**.

## 5. Deploy the dashboard to Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
2. Click **New app**.
3. Select your repo, branch `main`, and main file path `app.py`.
4. Click **Deploy**.

Your dashboard will be live at a `*.streamlit.app` URL within a couple of
minutes. Every time the GitHub Action commits a new `portfolio_state.json`,
the next page load (or Streamlit's periodic re-clone) picks up the fresh data
— no server, no database, no cost.

## How the scoring works

Each ticker gets four sub-scores (0–100), fetched from free Yahoo Finance data:

| Score | What it approximates | Data source |
|---|---|---|
| Quality | Return on equity proxy | `yfinance` `.info["returnOnEquity"]` |
| Valuation | Inverse of P/E (lower P/E → higher score) | `yfinance` forward/trailing P/E |
| Opportunity | How far below its 3-month average price it's trading | 3-month price history |
| Heat Risk (inverted) | Inverse of 14-day RSI (overbought → lower score) | 3-month price history |

These four are blended per-sleeve using the weights in `FAMILY_WEIGHTS`
(e.g. `INFRA` weights quality heaviest; `ENERGY_COMMODITY` weights
opportunity/pullback heaviest) into a single **composite score**, which maps
to a tier:

- **≥ 75 → Tier 1 (Accumulate Heavy)** — deploy the largest share of new capital
- **55–74 → Tier 2 (Maintenance DCA)** — steady, smaller allocation
- **< 55 → Tier 3 (Strictly Capped / Trim)** — zero/near-zero new capital

## Important limitations — read before relying on this

- **This is a mechanical heuristic, not equity research.** The formulas here
  (P/E inversion, ROE proxy, RSI, distance-from-moving-average) are simple
  placeholders. They do not capture debt levels, guidance changes, analyst
  revisions, competitive moats, regulatory risk, or anything qualitative —
  all of which matter a great deal for the names on an infra/AI-power
  watchlist (data-center hardware names in particular can look statistically
  "cheap" on a pulled-back RSI while still being fundamentally overextended).
- **`yfinance` is unofficial and can silently return stale, missing, or
  incorrect fields** (P/E, ROE) for some tickers, especially non-U.S. listings
  (e.g. `ABBN`, `ADPORTS`, `ICTEY`). The engine falls back to neutral default
  scores when a field is missing and flags this in the dashboard — check the
  data-quality banner before trusting a given score.
- **Position caps are not yet enforced.** `schema.yaml` has a
  `position_caps` section for you to fill in, but `engine.py` does not yet
  read your actual current holdings anywhere — so it cannot tell you whether
  a suggested allocation would push you over a cap. Wire in a
  `holdings.yaml` (or a Supabase/Postgres table) with your live position
  sizes if you want that enforced automatically.
- **No transaction execution.** This tool only scores and displays; it does
  not place trades. You still need a brokerage to act on it.
- This is not financial advice — it's an organizational/automation tool for
  your own decision-making process.

## Extending it

- **True database instead of flat JSON:** swap `portfolio_state.json` for a
  free-tier [Supabase](https://supabase.com/) or [Neon](https://neon.tech/)
  Postgres table if you want historical score tracking over time instead of
  only the latest snapshot.
- **Macro overlay:** add a FRED API pull (`pandas_datareader`) for rates,
  oil prices, or credit spreads and fold it into the `opportunity` or
  `heat_risk` scores per sleeve.
- **Sharia screen automation:** add a `sharia_screen` field per ticker in
  `schema.yaml` (populated manually or via a paid screening API) and surface
  it as a column in `app.py` alongside the tier.
