# billing_engine.py
# Core billing engine: reads customers.csv, computes bills, applies late fees,
# and writes output reports.

import csv
import os
from datetime import date, datetime
from exceptions import (
    NegativeConsumptionError,
    MissingFieldError,
    InvalidCategoryError,
    InvalidDateError,
)
from consumers import create_consumer

LATE_FEE_RATE      = 0.05          # 5 % late fee
REQUIRED_FIELDS    = {"customer_id", "name", "category",
                      "consumption_kl", "payment_due_date"}
DATE_FORMAT        = "%Y-%m-%d"


# ── Data Loading ───────────────────────────────────────────────────────────────

def load_customers(csv_path: str) -> list[dict]:
    """
    Read customers.csv and return a list of raw row dictionaries.

    Raises
    ------
    FileNotFoundError : If csv_path does not exist.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Customer file '{csv_path}' not found.")

    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


# ── Validation Helpers ─────────────────────────────────────────────────────────

def _validate_row(row: dict) -> None:
    """
    Validate a single CSV row for required fields, numeric consumption,
    and a parseable date.

    Raises
    ------
    MissingFieldError         : Required field absent or blank.
    NegativeConsumptionError  : Consumption < 0.
    InvalidDateError          : Date string is not parseable.
    """
    cid = row.get("customer_id", "UNKNOWN").strip()

    # Check all required fields are present and non-empty
    for field in REQUIRED_FIELDS:
        if field not in row or not str(row[field]).strip():
            raise MissingFieldError(cid, field)

    # Consumption must be a non-negative number
    try:
        consumption = float(row["consumption_kl"])
    except ValueError:
        raise NegativeConsumptionError(cid, row["consumption_kl"])

    if consumption < 0:
        raise NegativeConsumptionError(cid, consumption)

    # Due date must parse correctly
    try:
        datetime.strptime(row["payment_due_date"].strip(), DATE_FORMAT)
    except ValueError:
        raise InvalidDateError(cid, row["payment_due_date"])


# ── Late Fee Logic ─────────────────────────────────────────────────────────────

def _is_overdue(due_date_str: str, reference_date: date = None) -> bool:
    """Return True if due_date_str is before today (or reference_date)."""
    if reference_date is None:
        reference_date = date.today()
    due = datetime.strptime(due_date_str.strip(), DATE_FORMAT).date()
    return due < reference_date


# ── Core Processing ────────────────────────────────────────────────────────────

def process_customers(rows: list[dict], tariff: dict,
                      reference_date: date = None) -> tuple[list[dict], list[dict]]:
    """
    Process each customer row: validate → instantiate consumer → compute bill
    → apply late fee → collect result.

    Parameters
    ----------
    rows           : Raw rows from load_customers().
    tariff         : Tariff dict from tariff_loader.load_tariff().
    reference_date : Date used to check overdue (default: today).

    Returns
    -------
    (results, errors)
        results : List of dicts with billing details for each valid customer.
        errors  : List of dicts describing rows that failed validation.
    """
    results = []
    errors  = []

    for row in rows:
        cid = row.get("customer_id", "UNKNOWN").strip()
        try:
            # ── Validate ──────────────────────────────────────────────────────
            _validate_row(row)

            customer_id   = row["customer_id"].strip()
            name          = row["name"].strip()
            category      = row["category"].strip()
            consumption   = float(row["consumption_kl"])
            due_date_str  = row["payment_due_date"].strip()

            # ── Instantiate correct consumer subclass (may raise InvalidCategoryError)
            consumer = create_consumer(customer_id, name, category, consumption, tariff)

            # ── Compute base bill ─────────────────────────────────────────────
            base_bill = consumer.compute_bill()

            # ── Apply late fee if overdue ─────────────────────────────────────
            late_fee = 0.0
            is_late  = _is_overdue(due_date_str, reference_date)
            if is_late:
                late_fee = round(base_bill * LATE_FEE_RATE, 2)

            total_due = round(base_bill + late_fee, 2)

            results.append({
                "customer_id" : customer_id,
                "name"        : name,
                "category"    : category,
                "consumption" : consumption,
                "base_bill"   : base_bill,
                "late_fee"    : late_fee,
                "total_due"   : total_due,
                "is_late"     : is_late,
                "due_date"    : due_date_str,
            })

        except (MissingFieldError, NegativeConsumptionError,
                InvalidCategoryError, InvalidDateError) as e:
            errors.append({"customer_id": cid, "error": str(e)})

    return results, errors


# ── Report Writers ─────────────────────────────────────────────────────────────

def write_bills_report(results: list[dict], errors: list[dict],
                       output_path: str = "bills_report.txt") -> None:
    """
    Write a formatted per-customer bill report to output_path.
    """
    divider   = "=" * 72
    thin_line = "-" * 72

    with open(output_path, "w", encoding="utf-8") as f:

        f.write(divider + "\n")
        f.write("         SMART WATER BILLING SYSTEM – INDIVIDUAL BILLS\n")
        f.write(f"         Generated on : {date.today().strftime('%d %B %Y')}\n")
        f.write(divider + "\n\n")

        for r in results:
            f.write(f"  Customer ID   : {r['customer_id']}\n")
            f.write(f"  Name          : {r['name']}\n")
            f.write(f"  Category      : {r['category']}\n")
            f.write(f"  Consumption   : {r['consumption']:.2f} kL\n")
            f.write(f"  Payment Due   : {r['due_date']}"
                    f"{'  *** OVERDUE ***' if r['is_late'] else ''}\n")
            f.write(thin_line + "\n")
            f.write(f"  Base Bill     : Rs. {r['base_bill']:>10.2f}\n")
            f.write(f"  Late Fee (5%) : Rs. {r['late_fee']:>10.2f}\n")
            f.write(f"  TOTAL DUE     : Rs. {r['total_due']:>10.2f}\n")
            f.write(divider + "\n\n")

        # Error section
        if errors:
            f.write("\n" + divider + "\n")
            f.write("  SKIPPED RECORDS (Validation Errors)\n")
            f.write(divider + "\n")
            for e in errors:
                f.write(f"  Customer ID: {e['customer_id']}\n")
                f.write(f"  Reason     : {e['error']}\n")
                f.write(thin_line + "\n")


def write_summary_report(results: list[dict],
                         output_path: str = "summary_report.txt") -> None:
    """
    Write a summary report showing revenue per category and overall totals.
    """
    # Aggregate by category
    category_stats: dict[str, dict] = {}
    for r in results:
        cat = r["category"]
        if cat not in category_stats:
            category_stats[cat] = {
                "count"          : 0,
                "total_base"     : 0.0,
                "total_late_fee" : 0.0,
                "total_revenue"  : 0.0,
            }
        s = category_stats[cat]
        s["count"]          += 1
        s["total_base"]     += r["base_bill"]
        s["total_late_fee"] += r["late_fee"]
        s["total_revenue"]  += r["total_due"]

    grand_base    = sum(s["total_base"]     for s in category_stats.values())
    grand_late    = sum(s["total_late_fee"] for s in category_stats.values())
    grand_total   = sum(s["total_revenue"]  for s in category_stats.values())

    divider   = "=" * 72
    thin_line = "-" * 72

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(divider + "\n")
        f.write("         SMART WATER BILLING SYSTEM – SUMMARY REPORT\n")
        f.write(f"         Generated on : {date.today().strftime('%d %B %Y')}\n")
        f.write(divider + "\n\n")

        f.write(f"  {'Category':<18} {'Customers':>9} {'Base Bill (Rs.)':>16}"
                f" {'Late Fees (Rs.)':>15} {'Revenue (Rs.)':>13}\n")
        f.write(thin_line + "\n")

        for cat, s in category_stats.items():
            f.write(
                f"  {cat:<18} {s['count']:>9} {s['total_base']:>16.2f}"
                f" {s['total_late_fee']:>15.2f} {s['total_revenue']:>13.2f}\n"
            )

        f.write(thin_line + "\n")
        f.write(
            f"  {'GRAND TOTAL':<18} {sum(s['count'] for s in category_stats.values()):>9}"
            f" {grand_base:>16.2f} {grand_late:>15.2f} {grand_total:>13.2f}\n"
        )
        f.write(divider + "\n")
