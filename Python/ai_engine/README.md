# AI Engine

## Purpose

This directory contains the deterministic intelligence pipeline that transforms banking data into eligible, explainable, compliant next-best-offer recommendations.

## Contents

| Item | Description |
| --- | --- |
| `data_loader.py` | Loads customers, transactions, catalogues, holdings, and customer 360 data from Supabase or CSV fallbacks. |
| `feature_engine.py` | Builds normalized feature sets and rolling-window transaction aggregates. |
| `behavior_engine.py` | Analyzes spending behavior, income patterns, and category trends. |
| `event_engine.py` | Detects trigger events such as travel, salary, medical, and milestone activity. |
| `financial_analyst.py` | Calculates financial health and identifies gaps such as low investments, insurance gaps, or overspending. |
| `eligibility_engine.py` | Applies hard product constraints including income, age, credit, KYC, and existing holdings. |
| `product_fit_engine.py` | Scores behavioral and contextual fit between customers and products. |
| `nbo_engine.py` | Ranks recommendations using weighted next-best-offer logic. |
| `explainability_engine.py` | Creates human-readable reasons and evidence for recommendations. |
| `marketing_guard.py` | Applies consent, do-not-disturb, channel, and fatigue protections. |
| `genai_service.py` | Generates personalized campaign copy with deterministic fallback behavior. |
| `segmentation.py and clustering_engine.py` | Group customers into useful lifecycle or behavioral segments. |
| `config/` | YAML configuration for weights, thresholds, and marketing settings. |
| `run_pipeline.py` | Command-line entry point for exercising the end-to-end pipeline. |

## Operational Notes

These modules should remain importable from `Python/api_server.py` and the chatbot adapter. Avoid introducing side effects at import time.
