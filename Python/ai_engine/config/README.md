# AI Engine Configuration

## Purpose

This directory contains YAML configuration files that tune recommendation ranking, marketing behavior, and decision thresholds without changing Python code.

## Contents

| Item | Description |
| --- | --- |
| `marketing.yaml` | Marketing-related configuration such as message behavior and channel settings. |
| `nbo_weights.yaml` | Weights used by the next-best-offer ranking logic. |
| `thresholds.yaml` | Threshold values used by event detection, financial analysis, and decision gates. |

## Operational Notes

Review these files when changing model behavior. Configuration changes can materially affect recommendation outcomes.
