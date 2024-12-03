import os
import pandas as pd
import matplotlib.pyplot as plt
import get_ip
import ipaddress
import argparse
import filters

# Set up argument parsing
parser = argparse.ArgumentParser(description="Process a CSV file to identify tracker domains.")
parser.add_argument("input_csv", help="Path to the input CSV file")
args = parser.parse_args()

# Get the input file path from the arguments
input_csv = args.input_csv

# Check if the input file exists
if not os.path.isfile(input_csv):
    print(f"Error: The file '{input_csv}' does not exist. Please check the file path and try again.")
    exit(1)

# Load the input CSV
try:
    data = pd.read_csv(input_csv)
    print(f"Successfully loaded the file: {input_csv}")
except Exception as e:
    print(f"Error loading the file: {e}")
    exit(1)

# Load or create IP owner mapping file
geo_file_path = os.path.expanduser('~/ip_owners_with_geo.csv')

# Resolve missing IPs and update the CSV
unique_ips = pd.concat([data['Source'], data['Destination']]).unique()
unique_ips = [ip for ip in unique_ips if filters.is_valid_ip(ip)]
ip_owner_df = get_ip.update_ip_csv(unique_ips, geo_file_path)

# Apply all filters to the data
data['Is Private IP'] = data['Destination'].apply(lambda x: filters.is_private_ip(x, ip_owner_df))

# Exclude packets based on filters
data['Is Third Party'] = ~data['Is Private IP']

data['Third Party Volume'] = data['Length'].where(data['Is Third Party'], 0).astype(float)
data['Non-Third Party Volume'] = data['Length'].where(~data['Is Third Party'], 0).astype(float)

# Group by time intervals
data['Time Interval'] = (data['Time'] // 60).astype(int)
traffic_volume = data.groupby('Time Interval')[['Third Party Volume', 'Non-Third Party Volume']].sum()

# Plot
ax = traffic_volume.plot(kind='bar', stacked=True, figsize=(12, 6))

ax.set_xticks(range(len(traffic_volume.index)))  # Set x-tick positions
ax.set_xticklabels(range(len(traffic_volume.index)))

plt.title('Traffic Volume: Third-Party vs Non-Third-Party')
plt.xlabel('Time (minutes)')
plt.ylabel('Traffic Volume (bytes)')
plt.xticks(rotation=45)
plt.tight_layout()

# Determine the directory of the input argument and create an 'images' subdirectory
output_dir = os.path.join(os.path.dirname(input_csv), "images")
os.makedirs(output_dir, exist_ok=True)  

# Save the image 
output_file = os.path.join(output_dir, "tv_time_third_vs_non_third_party_traffic.png")
plt.savefig(output_file)
print("Plot saved to tv_time_third_vs_non_third_party_traffic.png")

