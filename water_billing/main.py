# main.py
# Entry point for the Smart Water Billing System.
# Run:  python main.py

import sys
import os
from datetime import date

from tariff_loader  import load_tariff
from billing_engine import (
    load_customers,
    process_customers,
    write_bills_report,
    write_summary_report,
)
from exceptions import MalformedConfigError

# ── Configuration ──────────────────────────────────────────────────────────────
TARIFF_CONFIG_PATH  = "tariff_config.json"
CUSTOMERS_CSV_PATH  = "customers.csv"
BILLS_REPORT_PATH   = "bills_report.txt"
SUMMARY_REPORT_PATH = "summary_report.txt"

# Set to a specific date for testing (e.g. date(2025, 6, 5)) or None for today
REFERENCE_DATE      = date(2025, 6, 5)


def banner(text: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def main():
    banner("Smart Water Billing System – Starting")

    # ── Step 1: Load tariff configuration ─────────────────────────────────────
    print(f"\n[1] Loading tariff configuration from '{TARIFF_CONFIG_PATH}' ...")
    try:
        tariff = load_tariff(TARIFF_CONFIG_PATH)
    except MalformedConfigError as e:
        print(f"    ERROR: {e}")
        sys.exit(1)
    print(f"    Loaded categories: {', '.join(tariff.keys())}")

    # ── Step 2: Load customer data ─────────────────────────────────────────────
    print(f"\n[2] Reading customer data from '{CUSTOMERS_CSV_PATH}' ...")
    try:
        rows = load_customers(CUSTOMERS_CSV_PATH)
    except FileNotFoundError as e:
        print(f"    ERROR: {e}")
        sys.exit(1)
    print(f"    Found {len(rows)} customer record(s).")

    # ── Step 3: Process customers ──────────────────────────────────────────────
    print(f"\n[3] Processing bills (reference date: {REFERENCE_DATE}) ...")
    results, errors = process_customers(rows, tariff, reference_date=REFERENCE_DATE)
    print(f"    Processed successfully : {len(results)}")
    print(f"    Skipped (errors)       : {len(errors)}")

    if errors:
        print("\n    Validation Errors:")
        for e in errors:
            print(f"      - [{e['customer_id']}] {e['error']}")

    # ── Step 4: Print summary to console ──────────────────────────────────────
    banner("Billing Results")
    header = f"  {'ID':<6} {'Name':<18} {'Cat':<13} {'kL':>6} " \
             f"{'Base Bill':>10} {'Late Fee':>9} {'Total Due':>10}"
    print(header)
    print("  " + "-" * 74)
    for r in results:
        flag = " *" if r["is_late"] else ""
        print(
            f"  {r['customer_id']:<6} {r['name']:<18} {r['category']:<13} "
            f"{r['consumption']:>6.1f} "
            f"Rs.{r['base_bill']:>8.2f} "
            f"Rs.{r['late_fee']:>6.2f} "
            f"Rs.{r['total_due']:>8.2f}{flag}"
        )
    print("  (* = overdue, 5% late fee applied)")

    # ── Step 5: Write output files ─────────────────────────────────────────────
    print(f"\n[4] Writing '{BILLS_REPORT_PATH}' ...")
    write_bills_report(results, errors, BILLS_REPORT_PATH)
    print(f"    Done.")

    print(f"\n[5] Writing '{SUMMARY_REPORT_PATH}' ...")
    write_summary_report(results, SUMMARY_REPORT_PATH)
    print(f"    Done.")

    # ── Step 6: Extensibility Note ─────────────────────────────────────────────
    banner("Task (f) – Extensibility Evaluation")
    print("""
  To add an 'Institutional' customer category:

  Files to change (3 files):

  1. tariff_config.json
     Add an "Institutional" block with its slabs and fixed_charge.
     No Python code changes needed to load it – tariff_loader is generic.

  2. consumers.py
     Add class InstitutionalConsumer(WaterConsumer) with compute_bill().
     Register it in CATEGORY_MAP: {"Institutional": InstitutionalConsumer}.

  3. (Optional) customers.csv / input data
     Add customer records with category = "Institutional".

  Why only 3 files?
  - billing_engine.py, exceptions.py, tariff_loader.py, and main.py
    require NO changes because they are designed against the abstract
    WaterConsumer interface and the generic factory function.

  Scaling suggestions for 1 million customers:
  1. Replace CSV + in-memory processing with a database (PostgreSQL/SQLite)
     and process records in paginated batches to avoid RAM exhaustion.
  2. Use Python's multiprocessing or concurrent.futures to parallelize
     bill computation across CPU cores, reducing total run time
     proportional to the number of available cores.
""")

    banner("All tasks complete")
    print(f"  Output files: {BILLS_REPORT_PATH}, {SUMMARY_REPORT_PATH}\n")


if __name__ == "__main__":
    main()
