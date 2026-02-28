import sys
import argparse
import json
import os

from profiler import Profiler
from GPT_Advisor import GPT_Advisor
from Executor import Executor
from pdf_report import generate_pdf_report
from impact_calculator import ImpactCalculator


def main(data_path: str, review: bool = False) -> int:
    print("[1/5] Profiling dataset...")
    profiler = Profiler(data_path)
    # ensure output directory exists
    import os
    os.makedirs("output", exist_ok=True)
    try:
        profiler.load()
    except Exception as exc:
        print(f"Error loading data: {exc}")
        return 1

    profiler.analyze()
    if not profiler.profile:
        print("Profiling produced no results, aborting.")
        return 1

    try:
        profiler.save_profile()
    except Exception as exc:
        print(f"Failed to save profile: {exc}")
        return 1
    print(f"Profile written to profiles.json (columns: {len(profiler.profile)})")

    print("[2/5] Asking GPT advisor for cleaning rules...")
    advisor = GPT_Advisor(profile_path="output/data_profile.json", output_path="output/proposed_rules.json")
    try:
        advisor.load_profile()
    except Exception as exc:
        print(f"Could not load profile for advisor: {exc}")
        return 1

    advisor.generate_rules()
    if not advisor.proposals:
        print("Advisor returned no proposals, nothing to do.")
        return 1

    try:
        advisor.save_proposals()
    except Exception as exc:
        print(f"Failed to write proposals: {exc}")
        return 1
    print(f"Proposals saved ({len(advisor.proposals)} rules)")

    print("[3/6] Running executor to apply rules...")
    executor = Executor(data_path, rules_path="output/proposed_rules.json")
    try:
        executor.load()
    except Exception as exc:
        print(f"Executor failed to load data: {exc}")
        return 1

    if not executor.rules:
        print("No rules loaded, aborting.")
        return 1

    # preserve original for impact calculation
    original_df = executor.df.copy()

    try:
        executor.apply_rules(dry_run=review)
    except Exception as exc:
        print(f"Error during rule application: {exc}")
        return 1

    # compute impact metrics
    print("[4/6] Calculating impact metrics...")
    impact_calc = ImpactCalculator(original_df, executor.df, executor.logs)
    impact_metrics = impact_calc.calculate()

    # create a simple cleaning summary from logs
    cleaning_summary = {
        "rules_applied": len(executor.logs),
        "total_rows_affected": sum(log.get("rows_affected", 0) for log in executor.logs)
    }

    # save outputs if not review
    if not review:
        try:
            executor.save_outputs(cleaned_path="output/cleaned_data.csv", log_path="output/execution_logs.json")
        except Exception as exc:
            print(f"Failed to save executor outputs: {exc}")
            return 1
        print("[5/6] Cleaned data and logs saved successfully.")
    else:
        # still save logs for review
        with open("output/execution_logs.json", "w") as f:
            json.dump(executor.logs, f, indent=4)
        print("[5/6] Review logs written to output/execution_logs.json")

    # generate enhanced report with metrics
    try:
        generate_pdf_report(
            profile=profiler.profile,
            proposals=advisor.proposals,
            output_path="output/data_cleaning_report.pdf",
            input_file=data_path,
            cleaning_summary=cleaning_summary,
            impact_metrics=impact_metrics,
            review=review
        )
        print("[6/6] Report generated at output/data_cleaning_report.pdf")
    except Exception as exc:
        print(f"Failed to generate report: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the data repair pipeline.")
    parser.add_argument("data_path", nargs="?", default="sample_data/test.csv", help="Path to input CSV/XLSX file")
    parser.add_argument("--review", action="store_true", help="Perform a dry run and review transformations without modifying data")
    args = parser.parse_args()
    sys.exit(main(args.data_path, review=args.review))
