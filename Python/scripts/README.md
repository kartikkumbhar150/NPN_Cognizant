# Python Operational Scripts

## Purpose

This directory contains scripts for database migrations, schema updates, and endpoint validation outside the main API process.

## Contents

| Item | Description |
| --- | --- |
| `migrate_to_supabase.py` | Migrates local datasets into Supabase. |
| `add_email_column.py` | Applies a targeted schema update for customer email data. |
| `test_new_endpoints.py` | Exercises recently added backend endpoints. |

## Operational Notes

Run these scripts deliberately against the intended environment. Confirm database URLs and credentials before executing migration operations.
