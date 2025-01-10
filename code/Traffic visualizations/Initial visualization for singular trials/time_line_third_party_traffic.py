import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
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

def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

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

relevant_ips = ip_owner_df.loc[ip_owner_df['Is Relevant'], 'IP Address']
data = data[~data['Destination'].isin(relevant_ips)]

# Map IPs to ISP + Service for visualization
ip_labels = []
for ip in ip_owner_df['IP Address']:
    ip_details = ip_owner_df[ip_owner_df['IP Address'] == ip]
    if not ip_details.empty:
        isp = ip_details.iloc[0]['ISP']
        service = ip_details.iloc[0]['Service']
        if service != "Unknown":
            label = f"{ip} ({isp}, {service})"
        else:
            label = f"{ip} ({isp})"
        ip_labels.append(label)
    else:
        ip_labels.append(f"{ip} (Unknown)")
        
# Count packets
packet_counts = data.groupby(['Time', 'Destination']).size()
cumulative_counts = packet_counts.unstack(fill_value=0).cumsum()

# Assign a unique color to each IP address
plt.figure(figsize=(12, 8))
color_map = {ip: color for ip, color in zip(cumulative_counts.columns, cm.rainbow(np.linspace(0, 1, len(cumulative_counts.columns))))}

# Plot each IP with its assigned color
for ip in cumulative_counts.columns:
    ip_details = ip_owner_df[ip_owner_df['IP Address'] == ip]
    final_cumsum = cumulative_counts[ip].iloc[-1]
    if not ip_details.empty:
        isp = ip_details.iloc[0]['ISP']
        service = ip_details.iloc[0]['Service']
        # Format the label to exclude "Unknown" services
        if service != "Unknown":
            label = f"{ip} ({isp}, {service}) - {final_cumsum}"
        else:
            label = f"{ip} ({isp}) - {final_cumsum}"
    else:
        label = f"{ip} (Unknown) - {final_cumsum}"
    plt.plot(cumulative_counts.index, cumulative_counts[ip], label=label, color=color_map[ip], linewidth=2, alpha=0.7)


# Plot
plt.title('Timeline of Third-Party Traffic')
plt.xlabel('Time (seconds)')
plt.ylabel('IP Address')
plt.xticks(rotation=45)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title='IP Addresses', fontsize='small')
plt.tight_layout()

# Save the image
output_dir = os.path.join(os.path.dirname(input_csv), "images")
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "tv_time_line_third_party_traffic.png")
plt.savefig(output_file)
print("Plot saved to ", output_dir, "/tv_time_line_third_party_traffic.png")

