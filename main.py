import sys
import argparse
import json
import os

from profiler import Profiler

def main(data_path: str) -> int:
    print("[1/2] Profiling dataset...")
    profiler = Profiler(data_path)
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
        profiler.save_outputs(
            json_path="output/client_data_profile.json",
            pdf_path="output/profile_report.pdf"
        )
    except Exception as exc:
        print(f"Failed to save profile outputs: {exc}")
        return 1
    
    print(f"[2/2] Profile generated successfully!")
    print(f"\nOutputs:")
    print(f"  ✓ output/client_data_profile.json (structured diagnostics)")
    print(f"  ✓ output/profile_report.pdf (human-readable analysis)")
    print(f"\nDataset Summary:")
    print(f"  • Rows: {len(profiler.df)}")
    print(f"  • Columns: {len(profiler.profile)}")
    print(f"  • Analysis complete")
    
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Profile a dataset and generate diagnostics.")
    parser.add_argument("data_path", nargs="?", default="sample_data/test.csv", help="Path to input CSV/XLSX file")
    args = parser.parse_args()
    sys.exit(main(args.data_path))
