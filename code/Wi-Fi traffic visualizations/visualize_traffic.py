# This method calls all the scripts to generate the visualization images for traffic analysis

import subprocess
import os
import argparse

# List of the Python scripts
scripts = [
    "freq_all_traffic.py",
    "freq_all_traffic_minus.py",
    "freq_meta_traffic.py",
    "freq_third_party_traffic.py",
    "time_line_all_traffic.py",
    "time_line_all_traffic_minus.py",
    "time_line_filtered_all_traffic.py",
    "time_line_meta_traffic.py",
    "time_line_meta_traffic_minus.py",
    "time_line_filtered_meta_traffic.py",
    "time_line_third_party_traffic.py",
    "time_line_third_party_traffic_minus.py",
    "time_line_filtered_third_party_traffic.py",
    "time_scatter_all_traffic.py",
    "time_scatter_meta_traffic.py",
    "time_scatter_third_party_traffic.py",
    "time_meta_vs_third_party.py"
    #"time_line_trackers_traffic.py",
    #"time_line_trackers_log_traffic.py"
]

# Set up argument parsing
parser = argparse.ArgumentParser(description="Run multiple Python scripts with user-provided arguments.")
parser.add_argument("csv_file", help="Path the CSV file for visual analysis.")
args = parser.parse_args()

# Get the directory and CSV file from arguments
scripts_dir = os.path.dirname(os.path.abspath(__file__))
argument_csv = os.path.expanduser(args.csv_file)

if not os.path.isfile(argument_csv):
    print(f"Error: Argument file '{argument_csv}' does not exist. Please check the file path.")
    exit(1)

# Run each script
for script in scripts:
    script_path = os.path.join(scripts_dir, script)
    if not os.path.isfile(script_path):
        print(f"Error: Script '{script}' not found in directory '{scripts_dir}'. Skipping.")
        continue
    print(f"Running script: {script}")
    try:
        # Execute the script and pass the argument
        subprocess.run(["python3", script_path, argument_csv], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error while running script {script}: {e}")

