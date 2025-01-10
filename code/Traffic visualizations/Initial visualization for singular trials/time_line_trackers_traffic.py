import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import socket
import re
from collections import Counter
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

# Get EasyList File
def parse_easylist(file_path):
    tracker_domains = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('||') and '^' in line:
                domain = line.split('||')[1].split('^')[0]
                tracker_domains.append(domain)
    return tracker_domains

# Expand the file path to handle ~
easylist_file = os.path.expanduser('~/list_easylist.txt')
tracker_domains = parse_easylist(easylist_file)
print(f"Extracted {len(tracker_domains)} tracker domains from EasyList.")

# Compile tracker domain patterns for regex matching
tracker_patterns = [re.escape(domain) for domain in tracker_domains]
tracker_regex = re.compile(r'|'.join(tracker_patterns))

# Reverse DNS Resolution
def resolve_hostname(ip):
    try:
        socket.setdefaulttimeout(2)  # Set a 2-second timeout for DNS resolution
        return socket.gethostbyaddr(ip)[0]
    except (socket.herror, socket.timeout):
        return ip  # Return the IP if resolution fails

# Resolve each IP
unique_destinations = data['Destination'].unique()
unique_destinations = [ip for ip in unique_destinations if filters.is_valid_ip(ip)]
resolved_hosts = {}

for ip in unique_destinations:
    resolved_hosts[ip] = resolve_hostname(ip)

data['Resolved Destination'] = data['Destination'].map(resolved_hosts)

# Match Against Tracker Domains
def is_tracker(destination, resolved_hostname):
    """Check if the destination or resolved hostname matches tracker domains."""
    destination = str(destination)  # Ensure destination is a string
    if isinstance(resolved_hostname, str):
        resolved_hostname = str(resolved_hostname) 
    else:
        resolved_hostname = ""
    return bool(tracker_regex.search(destination)) or bool(tracker_regex.search(resolved_hostname))


data['Is Tracker'] = data.apply(lambda row: is_tracker(row['Destination'], row['Resolved Destination']), axis=1)

# Create a new column for minute intervals
data['Minute'] = (data['Time'] // 60).astype(int)

#data['Time'] = pd.to_numeric(data['Time'], errors='coerce')
traffic_by_tracker = data.groupby(['Minute', 'Is Tracker'])['Length'].size().unstack(fill_value=0)

# Rename columns 
if traffic_by_tracker.shape[1] == 2:
    traffic_by_tracker.columns = ['Non-Tracker', 'Tracker']
elif True in traffic_by_tracker.columns:
    traffic_by_tracker.rename(columns={True: 'Tracker'}, inplace=True)
elif False in traffic_by_tracker.columns:
    traffic_by_tracker.rename(columns={False: 'Non-Tracker'}, inplace=True)

# Plot
traffic_by_tracker.plot(kind='line', figsize=(12, 6))
plt.title('Traffic Volume: Tracker vs Non-Tracker')
plt.xlabel('Time (minutes)')
plt.ylabel('Traffic Counts')
plt.legend(traffic_by_tracker.columns.tolist(), loc='upper left')
plt.tight_layout()

# Save the image
output_dir = os.path.join(os.path.dirname(input_csv), "images")
os.makedirs(output_dir, exist_ok=True) 
output_file = os.path.join(output_dir, "tv_time_line_tracker_traffic.png")
plt.savefig(output_file)

# Print Tracker data
print(f"Total packets: {len(data)}")
print(f"Tracker packets: {data['Is Tracker'].sum()}")
print(f"Non-tracker packets: {len(data) - data['Is Tracker'].sum()}")

if data['Is Tracker'].any():
    tracker_counts = Counter(data['Resolved Destination'][data['Is Tracker']])
    print("Traffic includes:")
    for domain, count in tracker_counts.most_common(10):
        print(f"{domain}: {count} packets")

