import os
import pandas as pd
import matplotlib.pyplot as plt
import get_ip
import ipaddress
import argparse
import filters

# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("input_csv", help="Path to the CSV file for the captured traffic")
args = parser.parse_args()

# Check if the input file exists
input_csv = args.input_csv
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

# Load IP owners mapping csv file
geo_dir = os.path.dirname(os.path.abspath(__file__))
geo_file_path = os.path.join(geo_dir, 'ip_owners_with_geo.csv')

# Resolve missing IPs and update the CSV
unique_ips = pd.concat([data['Source'], data['Destination']]).unique()
unique_ips = [ip for ip in unique_ips if filters.is_valid_ip(ip)]
ip_owner_df = get_ip.update_ip_csv(unique_ips, geo_file_path)


# Exclude traffic irrelevant to the analysis from the traffic data
ip_owner_df['Is Relevant'] = filters.is_relevant_traffic(
    ip_owner_df['IP Address'], ip_owner_df['ISP'], ip_owner_df['Service']
)

data['Is Relevant'] = data['Destination'].map(
    ip_owner_df.set_index('IP Address')['Is Relevant']
)

# Categorize traffic
data['Meta Traffic'] = data['Length'].where(data['Is Relevant'], 0).astype(float)
data['Third Party Traffic'] = data['Length'].where(~data['Is Relevant'], 0).astype(float)


# Group by time intervals
data['Time Interval'] = (data['Time'] // 60).astype(int)
traffic_volume = data.groupby('Time Interval')[['Meta Traffic', 'Third Party Traffic']].sum()

# Plot
ax = traffic_volume.plot(kind='bar', stacked=True, figsize=(12, 6))

ax.set_xticks(range(len(traffic_volume.index))) 
ax.set_xticklabels(range(len(traffic_volume.index)))

plt.title('Traffic Volume: Meta vs Other Traffic')
plt.xlabel('Time (minutes)')
plt.ylabel('Traffic Volume (bytes)')
plt.xticks(rotation=45)
plt.tight_layout()

# Save the image
output_dir = os.path.join(os.path.dirname(input_csv), "images")
os.makedirs(output_dir, exist_ok=True)  
output_file = os.path.join(output_dir, "tv_time_meta_vs_third_party_traffic.png")
plt.savefig(output_file)
print("Plot saved to ", output_dir, "/tv_time_meta_vs_third_party_traffic.png")

