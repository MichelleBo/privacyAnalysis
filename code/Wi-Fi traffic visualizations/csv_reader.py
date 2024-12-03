import argparse
from csv_processor import process_csv

# Set up argument parsing
parser = argparse.ArgumentParser(description="Process a CSV file to identify tracker domains.")
parser.add_argument("input_csv", help="Path to the input CSV file")
args = parser.parse_args()

# Call the processing function
try:
    output_csv = process_csv(args.input_csv)
    print(f"Processing completed. Output file: {output_csv}")
except Exception as e:
    print(f"Error: {e}")

