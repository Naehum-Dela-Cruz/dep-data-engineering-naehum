import argparse
import subprocess
import sys

def run_step(step_name, command):
    result = subprocess.run(command, shell = True)
    if result.returncode != 0:
        print(f"\n[ERROR] Step `{step_name}` failed with exit code {result.returncode}!")
        sys.exit(result.returncode)
    print(f"[SUCCESS] {step_name} completed successfully\n")

def main():
    parser = argparse.ArgumentParser(description="MassKara Data Engineering Pipeline Runner")
    parser.add_argument(
        "--with-ingest",
        action="store_true",
        help="Run API ingestion (requires SERP_API_KEY and APIFY_API_KEY in .env)"
    )
    args = parser.parse_args()

    # Step 1: ingest
    if arg.with_ingest:
        run_step("1. Data Ingestion (scripts/ingest.py)", f"`{python_exec}` scripts/ingest.py")
    else:
        print("\n[NOTE] Skipping API ingestion (using existing committed raw data in data/raw/).")
        print("To run live ingestion, pass the flag: --with-ingest")

    # Step 2: Transform
    run_step("2. Data Transformation (scripts/transform.py)", f"`{python_exec}` scripts/transform.py")

    # Step 3: SQL Database refresh and analytics
    run_step("SQL Analysis and Reporting (scripts/run_sql_analysis.py)", f"`{python_exec}` scripts/run_sql_analysis.py")

    print("\n============\n[PIPELINE COMPLETE] All steps finished clean\n============")

    if __name__ == "__main":
        main()