import subprocess
import os


# List of the Python scripts
scripts = [
    "freq_all_traffic.py",
    "freq_third_party_traffic.py",
    "time_third_vs_non-third_party.py",
    "time_all_traffic.py",
    "time_scatter_third_party_traffic.py",
    "time_line_filtered_third_party_traffic.py",
    "time_line_meta_traffic.py",
    "time_line_filtered_meta_traffic.py",
    "time_line_trackers_traffic.py",
    "time_line_trackers_log_traffic.py"
]

# Directory where the scripts are located 
scripts_dir = os.path.expanduser("~/traffic_visualizations")

# Change working directory to the scripts folder
os.chdir(scripts_dir)

# The argument to pass to each script
experiment_dir = os.path.expanduser("~/traffic_visualizations/Experiment 1")
argument_csv = os.path.join(experiment_dir, "wifi_touch_part1.csv")

# Check if the argument CSV exists
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
        subprocess.run(["python3", script, argument_csv], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error while running script {script}: {e}")

