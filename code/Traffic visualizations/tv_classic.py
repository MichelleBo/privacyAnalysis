import os
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import numpy as np
import matplotlib.cm as cm



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
    

output_dir = os.path.join(os.path.dirname(input_csv), "images")
os.makedirs(output_dir, exist_ok=True) 

# LAP address for glasses and phone
lap_glasses = '0x00347a8c'
lap_phone = '0x002ff7a8'

# Remove time gap
time_gap1 = 420 - 330
time_gap2 = 867 - 752

data = data[~data['Time'].between(330, 420)] 
data = data[~data['Time'].between(752, 867)] 


data['Time_Adjusted'] = data['Time']
data.loc[data['Time'] > 420, 'Time_Adjusted'] -= time_gap1
data.loc[data['Time'] > 867, 'Time_Adjusted'] -= time_gap2


# Filter data for glasses and phone
data['SP'] = data['Info'].str.extract(r'SP:\s*(-?\d+)').astype(float)
data['Time_Seconds'] = data['Time_Adjusted'].astype(int)

print(data[['Time', 'Time_Adjusted']])

sp_data_glasses = data[data['Lower Address Part'] == lap_glasses].dropna(subset=['SP']).sort_values('Time_Seconds')
sp_data_phone = data[data['Lower Address Part'] == lap_phone].dropna(subset=['SP']).sort_values('Time_Seconds')

average_sp_glasses = sp_data_glasses['SP'].mean()
average_sp_phone = sp_data_phone['SP'].mean()
print(f"Average sp of glasses: {average_sp_glasses}")
print(f"Average sp of phone: {average_sp_phone}")

min_t = int(data['Time_Seconds'].min())
max_t = (int(data['Time_Seconds'].max()) + 1)
x_positions = range(min_t, max_t, 60)

"""
data['Time Interval'] = (data['Time'] // 30).astype(int)

filtered_data = data[data['Lower Address Part'].isin(lap_addresses)]

experiment_trials = filtered_data['ExperimentTrial'].unique()





#####################     Shows traffic volume     #####################

# Create a function to visualize signal strength trends for specific LAPs
fig, axes = plt.subplots(len(experiment_trials), 1, figsize=(12, 8), sharex=True)

for i, trial in enumerate(experiment_trials):
    trial_data = filtered_data[filtered_data['ExperimentTrial'] == trial]

    for lap in lap_addresses:
        lap_data = trial_data[trial_data['Lower Address Part'] == lap]
        # Count packets over time (or use `lap_data['Time']` directly for raw data)
        traffic_counts = lap_data.groupby('Time').size()
        axes[i].plot(traffic_counts.index, traffic_counts.values, label=f'LAP: {lap}')

    axes[i].set_title(f'Experiment Trial: {trial}')
    axes[i].set_xlabel('Time (seconds)')
    axes[i].set_ylabel('Packet Count')
    axes[i].legend()
plt.tight_layout()

"""


### Line Plot for the packet count for glasses and phone ###
packet_count_by_second = data.groupby(['Time_Seconds', 'Lower Address Part']).size().reset_index(name='Count')

average_packet_glasses = packet_count_by_second[packet_count_by_second['Lower Address Part'] == lap_glasses].groupby('Time_Seconds')['Count'].mean()
average_packet_phone = packet_count_by_second[packet_count_by_second['Lower Address Part'] == lap_phone].groupby('Time_Seconds')['Count'].mean()



plt.figure(figsize=(12, 6))

plt.bar(average_packet_glasses.index, average_packet_glasses, label='Glasses (LAP: 0x00347a8c)', alpha=0.7, zorder=2)
plt.bar(average_packet_phone.index, average_packet_phone, label='Phone (LAP: 0x002ff7a8)', alpha=0.7, zorder=1)

plt.title('Average Traffic Volume per Second for Glasses and Phone')
plt.xlabel('Time (seconds)')
plt.ylabel('Packet Count per Second')
plt.xticks(x_positions, labels=[f"{x // 60 :.1f}" for x in x_positions], rotation=45)
plt.legend()
plt.tight_layout()

output_file = os.path.join(output_dir, "avg_packet_count_traffic.png")
plt.savefig(output_file)
print(f"Line plot for traffic count saved to {output_file}")
plt.close()


### Line Plot for the packet count for all addresses ###
average_packet_all = packet_count_by_second.groupby(['Time_Seconds', 'Lower Address Part'])['Count'].mean().reset_index()
unique_addresses = average_packet_all['Lower Address Part'].unique()

color_map = cm.get_cmap('tab20', len(unique_addresses))  

plt.figure(figsize=(12, 8))

for i, address in enumerate(unique_addresses):
    address_data = average_packet_all[average_packet_all['Lower Address Part'] == address]
    plt.bar(address_data['Time_Seconds'], 
            address_data['Count'], 
            label=f'Address: {address}', 
            color=color_map(i), 
            alpha=0.7)

plt.title('Average Traffic Volume per Second for Glasses and Phone')
plt.xlabel('Time (seconds)')
plt.ylabel('Packet Count per Second')
plt.xticks(x_positions, labels=[f"{x // 60 :.1f}" for x in x_positions], rotation=45)
plt.legend()
plt.tight_layout()

output_file = os.path.join(output_dir, "avg_packet_count_all_traffic.png")
plt.savefig(output_file)
print(f"Line plot for traffic count saved to {output_file}")
plt.close()


### Line Plot for the signal power (SP) for glasses and phone ###
average_sp_glasses = data[data['Lower Address Part'] == lap_glasses].groupby('Time_Seconds')['SP'].mean()
average_sp_phone = data[data['Lower Address Part'] == lap_phone].groupby('Time_Seconds')['SP'].mean()

plt.figure(figsize=(12, 6))

plt.plot(average_sp_glasses.index, average_sp_glasses, label='SP (Glasses)', linestyle='-', marker='o', markersize=4, zorder=2)
plt.plot(average_sp_phone.index, average_sp_phone, label='SP (Phone)', linestyle='-', marker='o', markersize=4, zorder=1)

plt.title('Average SP Over Time for Glasses and Phone')
plt.xlabel('Time (seconds)')
plt.ylabel('SP (Signal Power)')
plt.xticks(x_positions, labels=[f"{x // 60 :.1f}" for x in x_positions], rotation=45)
plt.legend()
plt.tight_layout()

output_file = os.path.join(output_dir, "avg_sp_traffic.png")
plt.savefig(output_file)
print(f"Line plot for traffic sp saved to {output_file}")
plt.close()


### Line Plot for the signal power (SP) for all addresses ###
average_sp_all = data.groupby(['Time_Seconds', 'Lower Address Part'])['SP'].mean().reset_index()
unique_addresses = average_sp_all['Lower Address Part'].unique()

colors = cm.get_cmap('tab20', len(unique_addresses))

plt.figure(figsize=(12, 6))

for i, address in enumerate(unique_addresses):
    address_data = average_sp_all[average_sp_all['Lower Address Part'] == address].sort_values('Time_Seconds')
    plt.plot(address_data['Time_Seconds'], 
             address_data['SP'], 
             label=f'Address: {address}', 
             color=colors(i), 
             linestyle='-', 
             marker='o', 
             markersize=4)

plt.title('Average SP Over Time for All Addresses')
plt.xlabel('Time (seconds)')
plt.ylabel('SP (Signal Power)')
plt.xticks(x_positions, labels=[f"{x // 60 :.1f}" for x in x_positions], rotation=45)
plt.legend(loc='upper left', bbox_to_anchor=(1, 1)) 
plt.tight_layout()

output_file = os.path.join(output_dir, "avg_sp_all_traffic.png")
plt.savefig(output_file)
print(f"Line plot for traffic sp saved to {output_file}")
plt.close()


### Line Plot for the signal power (SP) for all addresses after 30 seconds ###
first_30_seconds_data = data[data['Time_Seconds'] < 30]  
addresses_in_first_30_seconds = first_30_seconds_data['Lower Address Part'].unique() 

remaining_addresses = [addr for addr in unique_addresses if addr not in addresses_in_first_30_seconds]
average_sp_remaining = average_sp_all[average_sp_all['Lower Address Part'].isin(remaining_addresses)]

colors = cm.get_cmap('tab20', len(remaining_addresses))

plt.figure(figsize=(12, 6))

for i, address in enumerate(remaining_addresses):
    address_data = average_sp_remaining[average_sp_remaining['Lower Address Part'] == address].sort_values('Time_Seconds')
    plt.plot(address_data['Time_Seconds'], 
             address_data['SP'], 
             label=f'Address: {address}', 
             color=colors(i), 
             linestyle='-', 
             marker='o', 
             markersize=4)

plt.title('Average SP Over Time for All Addresses')
plt.xlabel('Time (seconds)')
plt.ylabel('SP (Signal Power)')
plt.xticks(x_positions, labels=[f"{x // 60 :.1f}" for x in x_positions], rotation=45)
plt.legend(loc='upper left', bbox_to_anchor=(1, 1)) 
plt.tight_layout()

output_file = os.path.join(output_dir, "avg_sp_all_after_30_traffic.png")
plt.savefig(output_file)
print(f"Line plot for traffic sp saved to {output_file}")
plt.close()


