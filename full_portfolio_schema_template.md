# Full Portfolio Schema Template

This schema template translates a layered multi-section portfolio into a machine-readable structure for automated scoring, tier assignment, deployment rules, and cap control. The attached allocation grid shows four major sleeves — Infra, Energy & Commodity, AI/Semis, and EM — each with distinct layers, target weights, permissible assets, and accumulation rules.[cite:86]

## Design principle

A single universal stock-ranking model is too blunt for this portfolio because the grid is organized by role and behavior, not by ticker list alone. Infra, commodity, semis, and EM sleeves each require shared core scoring fields but different weightings, thresholds, and overheat rules.[cite:86]

## Core entity model

Each ticker should be stored as one record with a common schema.

```yaml
portfolio_item:
  ticker: "LIN"
  name: "Linde plc"
  section: "INFRA"
  section_target_weight: 0.15
  layer: "Layer 2: Grid & Utilities"
  layer_target_weight: 0.40
  role: "core_compounder"
  permissible: true
  base_currency: "USD"
  exchange: "NASDAQ"
  country: "US"
  region: "Developed Markets"
  accumulation_protocol: "Capital deployed heavily during broad industrial pullbacks"
  dca_style: "pullback_weighted"
  max_position_cap: 0.09
  monthly_new_capital_cap: 0.03
  scoring_model: "infra_grid_utilities_v1"
  tiering_model: "tier_standard_v1"
  data_confidence_required: "medium"
  sharia_screen_mode: "review"
  hard_fail_rules:
    - "stale_data"
    - "balance_sheet_breach"
    - "guidance_break"
  notes: "High-quality industrial infrastructure compounder"
```

## Section-level schema

Each section should have metadata controlling top-down exposure.

```yaml
portfolio_section:
  name: "INFRA"
  target_weight: 0.15
  objective: "Real-economy infrastructure compounding"
  rebalance_style: "slow"
  scoring_family: "quality_value_setup_heat"
  deployment_bias: "favor_layer_2_on_pullbacks"
  max_section_drift: 0.03
  review_frequency: "monthly"
```

## Layer-level schema

Each layer should define how names are judged within the section.

```yaml
portfolio_layer:
  section: "INFRA"
  name: "Layer 3: Tech-Adjacent"
  target_weight: 0.20
  role_type: "higher_beta_satellite"
  dca_style: "strictly_capped"
  trim_policy: "trim_aggressively_on_euphoria"
  overbought_sensitivity: "high"
  quality_floor: "medium"
  valuation_tolerance: "low"
  setup_sensitivity: "high"
```

## Scoring families

The attached grid implies different portfolio jobs by sleeve, so the scoring model should change by section rather than using one flat formula for all names.[cite:86]

### 1. Infra

```yaml
scoring_model:
  id: "infra_v1"
  weights:
    quality: 40
    valuation: 25
    opportunity: 20
    heat_risk: 15
  notes: "Prioritizes durable compounders and pullback deployment"
```

### 2. Energy & Commodity

```yaml
scoring_model:
  id: "energy_commodity_v1"
  weights:
    quality: 25
    valuation: 25
    opportunity: 30
    heat_risk: 20
  notes: "More cyclical, more setup-sensitive, stronger dip-buy logic"
```

### 3. AI/Semis

```yaml
scoring_model:
  id: "ai_semis_v1"
  weights:
    quality: 35
    valuation: 20
    opportunity: 20
    heat_risk: 25
  notes: "Higher overheat penalty, stronger capex-cycle awareness"
```

### 4. EM

```yaml
scoring_model:
  id: "em_v1"
  weights:
    quality: 30
    valuation: 20
    opportunity: 25
    heat_risk: 25
  notes: "Adds country, liquidity, and governance sensitivity"
```

## Tier rules

A standardized tier engine should map the section-specific score into monthly action buckets.

```yaml
tiering_model:
  id: "tier_standard_v1"
  tier_1:
    min_composite_score: 75
    min_quality_bucket_pct: 0.70
    min_heat_risk_bucket_pct: 0.45
    disallow_if:
      - "hard_fail"
      - "extreme_overbought"
      - "stale_data"
  tier_2:
    min_composite_score: 55
    max_composite_score: 74
    allow_if:
      - "quality_good_but_not_cheap"
      - "mixed_signals"
      - "core_maintenance_dca"
  tier_3:
    max_composite_score: 54
    force_if:
      - "hard_fail"
      - "euphoria"
      - "valuation_extreme"
      - "speculative_breakdown"
```

## Deployment rules

Deployment rules should be explicit and cap-aware so that the dashboard can convert tiers into new-money instructions.

```yaml
deployment_policy:
  tier_1_new_capital_share_range: [0.50, 0.70]
  tier_2_new_capital_share_range: [0.30, 0.50]
  tier_3_new_capital_share_range: [0.00, 0.05]
  block_new_buy_if_at_cap: true
  exceptional_override_allowed: true
  exceptional_override_rule: "only if score > 85 and position remains within section drift limits"
```

## Role taxonomy

A controlled role taxonomy makes the system easier to score and maintain.

```yaml
roles:
  - core_compounder
  - hard_asset_scarcity
  - royalty_monetary_proxy
  - cyclical_deep_value
  - baseload_energy
  - industrial_materials_cyclical
  - physical_monopoly
  - architecture_robotics_enabler
  - velocity_application
  - regional_quality_compounder
  - regional_state_champion
  - optional_satellite
```

## Portfolio translation from the grid

The attached image can be represented in the schema as follows.[cite:86]

```yaml
sections:
  - name: "INFRA"
    target_weight: 0.15
    layers:
      - name: "Layer 1: Hard Assets"
        target_weight: 0.40
        permissible_assets: ["TPL", "ADPORTS", "ICTEY"]
      - name: "Layer 2: Grid & Utilities"
        target_weight: 0.40
        permissible_assets: ["LIN", "ABBN", "SU", "NVT", "CEG", "PWR", "CWCO"]
      - name: "Layer 3: Tech-Adjacent"
        target_weight: 0.20
        permissible_assets: ["VRT", "BE"]

  - name: "ENERGY_COMMODITY"
    target_weight: 0.23
    layers:
      - name: "Monetary Royalties"
        target_weight: 0.40
        permissible_assets: ["FNV", "WPM"]
      - name: "Baseload Energy"
        target_weight: 0.40
        permissible_assets: ["CCJ", "CNQ", "XOM"]
      - name: "Industrial Materials"
        target_weight: 0.20
        permissible_assets: ["FCX", "BHP", "NEM", "COP"]

  - name: "AI_SEMIS"
    target_weight: 0.10
    layers:
      - name: "Layer 1: Physical Monopolies"
        target_weight: 0.60
        permissible_assets: ["TSM", "ASML", "SHECY", "6920.T"]
      - name: "Layer 2: Architecture & Robotics"
        target_weight: 0.30
        permissible_assets: ["AVGO", "CDNS", "QCOM", "FANUY", "8035.T", "SNPS"]
      - name: "Layer 3: Velocity Applications"
        target_weight: 0.10
        permissible_assets: ["NOW", "PANW", "STX"]

  - name: "EM"
    target_weight: 0.07
    layers:
      - name: "INDIA"
        target_weight: 0.40
        permissible_assets: ["ABB", "SIEMENS INDIA", "HITACHI ENERGY", "CG POWER", "PI INDUSTRY", "SUNPHARMA", "HCLTECH"]
      - name: "GCC"
        target_weight: 0.40
        permissible_assets: ["ARAMCO", "ADCONGAS", "ACWA POWER", "STC"]
      - name: "Other Jurisdiction"
        target_weight: 0.20
        permissible_assets: ["HIJP", "TLK", "VALE", "ISDE"]
```

## Operational fields for automation

The automatic layer should store both data outputs and rule outputs for every run.

```yaml
run_output_fields:
  - ticker
  - section
  - layer
  - price_timestamp
  - fundamentals_timestamp
  - composite_score
  - quality_score
  - valuation_score
  - opportunity_score
  - heat_risk_score
  - tier
  - suggested_action
  - suggested_new_capital_share
  - near_cap_flag
  - stale_data_flag
  - hard_fail_flag
  - sharia_status
  - explanation
```

## Why this schema works

This schema preserves the logic visible in the allocation grid: some names are meant for continuous accumulation, some are bought on cyclical pullbacks, and some are tightly capped satellites that must be trimmed on euphoria.[cite:86] Converting that logic into explicit metadata is what allows GitHub Actions, Streamlit, or another automation layer to classify names consistently without relying on a monthly free-form prompt.[cite:86]
