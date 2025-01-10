import os
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import numpy as np



#####################     Loading the csv files     #####################
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
    
data = data[data['Time'] >= 1]
data['Time Interval'] = (data['Time'] // 5) * 5

data['Merged_Info'] = data['Info'].str.replace(r'\[Malformed.*\]', '', regex=True)

min_t = int(data['Time Interval'].min())
max_t = (int(data['Time Interval'].max()) + 1)
x_positions = range(min_t, max_t, 60)

output_dir = os.path.join(os.path.dirname(input_csv), "images")
os.makedirs(output_dir, exist_ok=True) 

phone_mac = "24:4b:03:98:02:66"
phone_mac2 = "SamsungElect_98:02:66"
glasses_mac = "5f:64:8e:90:8d:44"



#####################     Shows traffic volume     #####################

### Line plot for different Info ###
info_data = data[
    (data['Source'] == phone_mac) | 
    (data['Destination'] == phone_mac) |
    (data['Source'] == phone_mac2) | 
    (data['Destination'] == phone_mac2) |
    (data['Source'] == glasses_mac) | 
    (data['Destination'] == glasses_mac)
]

time_pattern_counts = info_data.groupby(['Time Interval', 'Merged_Info']).size().unstack(fill_value=0)

ax = time_pattern_counts.plot(figsize=(12, 8), title="BLE Patterns Over Time", xlabel="Time (minutes)", ylabel="Count")

for i in range (0, 5):
    place = i * 60 + 30
    plt.axvline(x=place, color='cyan', linestyle='--', linewidth=1)
    
    
ax.set_xticks(x_positions, labels=[f"{x // 60 :.1f}" for x in x_positions], rotation=45)
plt.legend(loc='upper left', title='Info', fontsize='small')
plt.tight_layout()

output_file = os.path.join(output_dir, "info_patterns_traffic.png")
plt.savefig(output_file)
print(f"Line plot for all ble traffic saved to {output_file}")
plt.close()



### Line plot for glasses vs phone ###
plt.figure(figsize=(12, 8))
phone_traffic = data[
    (data['Source'] == phone_mac) |
    (data['Destination'] == phone_mac) |
    (data['Source'] == phone_mac2) | 
    (data['Destination'] == phone_mac2)
]
glasses_traffic = data[(data['Source'] == glasses_mac) | (data['Destination'] == glasses_mac)]

phone_time_counts = phone_traffic.groupby('Time Interval').size()
glasses_time_counts = glasses_traffic.groupby('Time Interval').size()

for i in range (0, 5):
    place = i * 60 + 30
    plt.axvline(x=place, color='cyan', linestyle='--', linewidth=1)
    
phone_time_counts.plot(label=f'Phone Traffic, {phone_mac} / {phone_mac2}')
glasses_time_counts.plot(label=f'Glasses Traffic {glasses_mac}')
   
plt.title("Traffic Over Time: Phone vs Glasses")
plt.xlabel("Time (Seconds)")
plt.ylabel("Packet Count")
plt.xticks(x_positions, labels=[f"{x // 60 :.1f}" for x in x_positions], rotation=45)
plt.legend(title="Device", loc='upper left')
plt.tight_layout()

output_file = os.path.join(output_dir, "glasses_vs_phone_traffic.png")
plt.savefig(output_file)
print(f"Line plot for all ble traffic saved to {output_file}")
plt.close()



















