import os
import pandas as pd
import argparse

# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("category", help="Name of the directory of which contains the csv that would be merged")
args = parser.parse_args()

# Combine multiple experiment CSVs into one file.
def combine_experiments(experiment_dir):
    csv_files = [os.path.join(experiment_dir, f) for f in os.listdir(experiment_dir) if f.endswith(".csv")]
    
    if not csv_files:
        print(f"No CSV files found in directory: {experiment_dir}")
        return

    # Combine all experiments into one DataFrame
    dataframes = []
    for file in csv_files:
        print(f"Loading {file}...")
        exp_name = os.path.splitext(os.path.basename(file))[0]
        experiment_name = exp_name[-1]
        df = pd.read_csv(file)
        df['ExperimentTrial'] = experiment_name
        dataframes.append(df)

    # Combine into a single DataFrame
    combined_data = pd.concat(dataframes, ignore_index=True)
    
    # Save the combined DataFrame
    output_file = os.path.join(experiment_dir, "merged_csv.csv")
    combined_data.to_csv(output_file, index=False)
    print(f"Combined data saved to {output_file}")

if __name__ == "__main__":
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    category = args.category
    experiment_path = os.path.join(cur_dir, category)

    # Run the combine_experiments function
    combine_experiments(experiment_path)


