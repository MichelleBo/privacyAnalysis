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
    print(f"Error: The file '{input_csv}' does not exist.")
    exit(1)

# Load the input CSV
try:
    data = pd.read_csv(input_csv)
    print(f"Successfully loaded the file: {input_csv}")
except Exception as e:
    print(f"Error loading the file: {e}")
    exit(1)

# Parse EasyList File for tracker domains
def parse_easylist(file_path):
    tracker_domains = set()
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('||') and '^' in line:
                domain = line.split('||')[1].split('^')[0]
                tracker_domains.add(domain)
    return list(tracker_domains)

# Expand the file path to handle ~
easylist_file = os.path.expanduser('~/list_easylist.txt')
tracker_domains = parse_easylist(easylist_file)
print(f"Extracted {len(tracker_domains)} tracker domains from EasyList.")

# Compile tracker domain patterns for regex matching
tracker_patterns = [re.escape(domain) for domain in tracker_domains]
tracker_regex = re.compile(r'|'.join(tracker_patterns))

# Reverse DNS Resolution
dns_cache = {}
def resolve_hostname(ip):
    if ip in dns_cache:
        return dns_cache[ip]
    try:
        # Validate if IP is public and not private
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private:
            dns_cache[ip] = ip  # Skip private IPs
            return ip
        # Resolve hostname
        socket.setdefaulttimeout(2)  # Set a 2-second timeout
        hostname = socket.gethostbyaddr(ip)[0]
        dns_cache[ip] = hostname
        return hostname
    except (ValueError, socket.herror, socket.timeout, ipaddress.AddressValueError):
        dns_cache[ip] = ip  # Return the IP if resolution fails
        return ip

# Resolve hostnames and cache results
data['Resolved Destination'] = data['Destination'].map(resolve_hostname)

# Match Against Tracker Domains
def is_tracker(resolved_hostname):
    return resolved_hostname.lower() in tracker_domains
    


data['Is Tracker'] = data['Resolved Destination'].apply(is_tracker)

# Add byte volume analysis
data['Minute'] = (data['Time'] // 60).astype(int)
traffic_volume_stats = data.groupby(['Minute', 'Is Tracker']).agg(Byte_Volume=('Length', 'sum')).unstack(fill_value=0)

# Rename columns for clarity
traffic_volume_stats.columns = [f"{'Tracker' if is_tracker else 'Non-Tracker'} Byte_Volume"for is_tracker, metric in traffic_volume_stats.columns]


# Plot packet counts
traffic_volume_stats.plot(kind='line', figsize=(12, 6))
plt.title('Traffic Volume: Tracker vs Non-Tracker (Byte Volume)')
plt.xlabel('Time (minutes)')
plt.ylabel('Traffic Volume (btyes)')
plt.legend(loc='upper left')
plt.tight_layout()

# Save the image
output_dir = os.path.join(os.path.dirname(input_csv), "images")
os.makedirs(output_dir, exist_ok=True) 
output_file = os.path.join(output_dir, "time_line_tracker_traffic.png")
plt.savefig(output_file)

# Print statistics
total_byte_volume = data['Length'].sum()
tracker_byte_volume = data.loc[data['Is Tracker'], 'Length'].sum()
non_tracker_byte_volume = total_byte_volume - tracker_byte_volume

print(f"Total byte volume: {total_byte_volume} bytes")
print(f"Tracker byte volume: {tracker_byte_volume} bytes")
print(f"Non-tracker byte volume: {non_tracker_byte_volume} bytes")

# Top tracker domains by byte volume
if tracker_byte_volume > 0:
    top_trackers = data.loc[data['Is Tracker']].groupby('Resolved Destination')['Length'].sum().sort_values(ascending=False).head(10)
    print("Top tracker domains by byte volume:")
    for domain, volume in top_trackers.items():
        print(f"{domain}: {volume} bytes")

