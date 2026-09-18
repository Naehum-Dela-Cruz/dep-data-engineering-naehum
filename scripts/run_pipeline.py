import argparse
import subprocess
import sys


def run_step(step_name, command):
    result = subprocess.run(command)
    if result.returncode != 0:
        print(f"{step_name} failed.")
        sys.exit(result.returncode)

    print(f"{step_name} completed successfully.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-ingest", action="store_true")
    args = parser.parse_args()

    if args.with_ingest:
        run_step(
            "Ingestion",
            [sys.executable, "scripts/ingest.py"],
        )
    else:
        print("Skipping ingestion and using existing raw data.")

    run_step(
        "Transformation",
        [sys.executable, "scripts/transform.py"],
    )

    run_step(
        "Analysis",
        [sys.executable, "scripts/run_sql_analysis.py"],
    )


if __name__ == "__main__":
    main()