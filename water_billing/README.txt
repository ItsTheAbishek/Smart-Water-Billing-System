========================================================================
  SMART WATER BILLING SYSTEM – README
  CSA08 | CO4 | Assessment Tool 3
========================================================================

OVERVIEW
--------
This project implements a Smart Water Billing System for a municipal
corporation. It supports Residential, Commercial, and Industrial consumer
categories with slab-based tariff pricing, a 5% late fee, and generates
formatted output reports.

------------------------------------------------------------------------
PROJECT FILES
------------------------------------------------------------------------

Source Files (.py):
  main.py            - Entry point; orchestrates the entire pipeline
  consumers.py       - Abstract base class WaterConsumer + 3 subclasses
  tariff_loader.py   - Module to load & validate tariff_config.json
  billing_engine.py  - Core engine: CSV reading, bill computation, reports
  exceptions.py      - Custom exception classes

Input Files:
  tariff_config.json - Slab rates and fixed charges for all 3 categories
  customers.csv      - Customer records (ID, name, category, consumption, due date)

Output Files (generated on run):
  bills_report.txt   - Per-customer itemised bill with late fee details
  summary_report.txt - Revenue summary grouped by category

------------------------------------------------------------------------
HOW TO RUN
------------------------------------------------------------------------

Requirements:
  Python 3.x (standard library only – no third-party packages needed)

Steps:
  1. Place all 7 project files in the same directory.
  2. Open a terminal / command prompt in that directory.
  3. Run:
         python main.py

  Output files (bills_report.txt, summary_report.txt) will be created
  in the same directory.

------------------------------------------------------------------------
SLAB TARIFF STRUCTURE (from tariff_config.json)
------------------------------------------------------------------------

  Residential:
    0 – 20 kL  :  Rs. 20 / kL
    21 – 50 kL :  Rs. 35 / kL
    > 50 kL    :  Rs. 50 / kL
    Fixed charge: Rs. 50 / month

  Commercial:
    0 – 50 kL   :  Rs.  50 / kL
    51 – 150 kL :  Rs.  75 / kL
    > 150 kL    :  Rs. 100 / kL
    Fixed charge : Rs. 200 / month

  Industrial:
    0 – 100 kL  :  Rs.  40 / kL
    101 – 500 kL:  Rs.  65 / kL
    > 500 kL    :  Rs.  90 / kL
    Fixed charge : Rs. 500 / month

  Late fee: 5% of base bill if payment_due_date is before today.

------------------------------------------------------------------------
DESIGN HIGHLIGHTS (Sub-task coverage)
------------------------------------------------------------------------

  (a) OOP Design:
      WaterConsumer (abstract, abc.ABC) in consumers.py
      Subclasses: ResidentialConsumer, CommercialConsumer, IndustrialConsumer
      Each overrides compute_bill() with slab pricing via _apply_slabs().

  (b) Config Loader:
      tariff_loader.py reads and validates tariff_config.json at runtime.
      Returns dict: category -> {slabs, fixed_charge}.

  (c) Core Engine:
      billing_engine.py reads customers.csv, instantiates correct consumer
      via factory function, computes bills, applies late fees, and writes
      both output reports.

  (d) Exception Handling:
      Custom exceptions in exceptions.py:
        InvalidCategoryError, NegativeConsumptionError, MissingFieldError,
        MalformedConfigError, InvalidDateError
      All validated before processing; errors logged to bills_report.txt.

  (e) Output Files:
      bills_report.txt  – per-customer bills with late fee breakdown
      summary_report.txt – revenue per category + grand totals

  (f) Extensibility:
      To add 'Institutional' category: edit tariff_config.json (add slab
      block) and consumers.py (add subclass + register in CATEGORY_MAP).
      Only 2–3 files need changing. Rest of codebase is untouched.

------------------------------------------------------------------------
========================================================================
