import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import get_ip
import ipaddress
import argparse
import filters
import numpy as np
import matplotlib.patches as mpatches



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

# Load IP owners mapping csv file
geo_dir = os.path.dirname(os.path.abspath(__file__))
geo_file_path = os.path.join(geo_dir, 'ip_owners_with_geo.csv')

# Resolve missing IPs and update the CSV
data = data[data['Destination'].apply(filters.is_valid_ip) & data['Source'].apply(filters.is_valid_ip)]
unique_ips = pd.concat([data['Source'], data['Destination']]).unique()
ip_owner_df = get_ip.update_ip_csv(unique_ips, geo_file_path)

    
output_dir = os.path.join(os.path.dirname(input_csv), "images")
os.makedirs(output_dir, exist_ok=True) 



#####################     Shows traffic volume for the types of parties     #####################
# Classify traffic for the analysis
data['Service'] = data['Destination'].map(ip_owner_df.set_index('IP Address')['Service'])

data['Traffic Type'] = data.apply(lambda row: filters.classify_traffic_by_service(row['Service'], row['Protocol']), axis=1)

data['First Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'First Party', 0).astype(float)
data['Support Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'Support Party', 0).astype(float)
data['Third Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'Third Party', 0).astype(float)

fp_volume = data['First Party Traffic'].sum() / 5
sp_volume = data['Support Party Traffic'].sum() / 5
tp_volume = data['Third Party Traffic'].sum() / 5
tt_volume = fp_volume + sp_volume + tp_volume
print(f"First Party: {fp_volume / 1048576} MB with {fp_volume / tt_volume * 100}%")
print(f"Support Party: {sp_volume / 1024} KB with {sp_volume / tt_volume * 100}%")
print(f"Third Party: {tp_volume / 1024} KB with {tp_volume / tt_volume * 100}%")



# Group by time intervals
data_10 = data.copy()
if "8hCapture.csv" in input_csv:
    data_10['Time Interval'] = (data_10['Time'] // (60 * 10)).astype(int)
    data['Time Interval'] = (data['Time'] // (60 * 15)).astype(int)
else:
    data_10['Time Interval'] = (data_10['Time'] // 10).astype(int)
    data['Time Interval'] = (data['Time'] // 30).astype(int)

time_intervals = data['Time Interval'].unique()
x_positions = np.arange(len(time_intervals))

#print(f"Google: {data[(data['Traffic Type'] == 'Third Party') & (data['Service'] == 'Google')]['Length'].sum() / 1024} KB")
#print(f"Spotify: {data[(data['Traffic Type'] == 'Third Party') & (data['Service'] == 'Spotify')]['Length'].sum() / 1024} KB")



### Bar Plot for all traffic by protocol ###
readability_colors = {
    'Unreadable': 'blue',
    'Partially Readable': 'orange',
    'Readable': 'green',
    'Unknown': 'gray'
}

data['Readability'] = data.apply(lambda row: filters.check_readability(row['Protocol'], row['Info']), axis=1)

partially_readable_third_party = data[(data['Traffic Type'] == 'Third Party') & (data['Readability'] == 'Partially Readable')]
print(partially_readable_third_party[['Destination', 'Protocol', 'Info', 'Length']])

"""
refined_readability_bytes = data.groupby(['Protocol', 'Readability'])['Length'].sum().reset_index()
    
pivot_data = refined_readability_bytes.pivot(index='Protocol', columns='Readability', values='Length').fillna(0)


pivot_data = pivot_data[[col for col in readability_colors if col in pivot_data.columns]]
colors = [readability_colors[col] for col in pivot_data.columns]

pivot_data.plot(kind='bar', stacked=True, figsize=(12, 8))
plt.yscale('log')
plt.title('Traffic Volume for All Traffic by Protocol and Readability',  fontsize=18)
plt.xlabel('Protocol',  fontsize=16)
plt.ylabel('Total Bytes',  fontsize=16)
plt.tick_params(axis='x', labelsize=14, rotation=45)
plt.tick_params(axis='y', labelsize=14)
plt.legend(title='Readability', loc='upper left',  fontsize=14, title_fontsize=14)
plt.tight_layout()

output_file = os.path.join(output_dir, f"bar_log_all_protocol_traffic.png")
plt.savefig(output_file)
print(f"Bar plot for all traffic saved to {output_file}")
plt.close()


### Bar Plot for different party type traffic by protocol ###
for traffic_type in ['First Party', 'Support Party', 'Third Party']:
    party_data = data[data['Traffic Type'] == traffic_type]
    if party_data['Length'].sum() == 0:
        continue
    party_data.loc[:, 'Readability'] = party_data.apply(lambda row: filters.check_readability(row['Protocol'], row['Info']), axis=1)

    refined_readability_bytes = party_data.groupby(['Protocol', 'Readability'])['Length'].sum().reset_index()
        
    pivot_data = refined_readability_bytes.pivot(index='Protocol', columns='Readability', values='Length').fillna(0)

    pivot_data = pivot_data[[col for col in readability_colors if col in pivot_data.columns]]
    colors = [readability_colors[col] for col in pivot_data.columns]
    
    pivot_data.plot(kind='bar', stacked=True, figsize=(12, 8))
    plt.yscale('log')
    plt.title(f'Traffic Volume for {traffic_type} by Protocol and Readability',  fontsize=18)
    plt.xlabel('Protocol',  fontsize=16)
    plt.ylabel('Total Bytes',  fontsize=16)
    plt.tick_params(axis='x', labelsize=14, rotation=45)
    plt.tick_params(axis='y', labelsize=14)
    plt.legend(title='Readability', loc='upper left',  fontsize=14, title_fontsize=14)
    plt.tight_layout()
    
    output_file = os.path.join(output_dir, f"bar_log_{traffic_type.lower().replace(' ', '_')}_protocol_traffic.png")
    plt.savefig(output_file)
    print(f"Bar plot for all traffic saved to {output_file}")
    plt.close()


### Scatter Plot for all traffic ###
plt.figure(figsize=(12, 8))

grouped_data = data_10.groupby('Time Interval')['Length'].sum()
plt.scatter(grouped_data.index * 60 * 10, grouped_data.values, alpha=0.7)

for i in range (0, 11):
    place = i * 30
    plt.axvline(x=place, color='cyan', linestyle='--', linewidth=1)

if "8hCapture.csv" in input_csv:
    plt.xticks(x_positions, labels=[f"{x * 0.25:.1f}" for x in x_positions], rotation=45)
else:
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)

plt.yscale('log')
plt.title(f'Traffic Volume for All Traffic (Log)')
plt.xlabel("Time (seconds)")
plt.ylabel("Traffic Volume (bytes)")
plt.tight_layout()

output_file = os.path.join(output_dir, f"scatter_all_traffic.png")
plt.savefig(output_file)
print(f"Scatter plot for all traffic saved to {output_file}")
plt.close()



### Line Plot for packet distribution ###
packet_size_distribution = data['Length'].value_counts().sort_index()

plt.figure(figsize=(12, 6))
plt.plot(packet_size_distribution.index, packet_size_distribution.values)
plt.title('Packet Size Distribution')
plt.xlabel('Packet Size (Bytes)')
plt.ylabel('Frequency')
plt.tight_layout()
output_file = os.path.join(output_dir, f"packet_distribution.png")
plt.savefig(output_file)
print(f"Line plot for packet distribution saved to {output_file}")
plt.close()


### Line Plot for all traffic ###
plt.figure(figsize=(12, 8))

combined_traffic = data.groupby(['Time Interval'])['Length'].sum()
plt.plot(combined_traffic.index, combined_traffic.values, label="Combined Traffic", linewidth=2, alpha=0.7)

if not "8hCapture.csv" in input_csv:
    for i in range (0, 6):
        place = i * 2 + 1
        plt.axvline(x=place, color='cyan', linestyle='--', linewidth=1)

if "8hCapture.csv" in input_csv:
    plt.xticks(x_positions, labels=[f"{x * 0.25:.1f}" for x in x_positions], rotation=45)
else:
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    
plt.title('Combined Traffic Volume Across All Traffic Types')
plt.xlabel("Time Interval (hours)")
plt.ylabel("Traffic Volume (bytes)")
plt.tight_layout()

output_file = os.path.join(output_dir, "line_all_traffic.png")
plt.savefig(output_file)
print(f"Combined traffic plot saved to {output_file}")
plt.close()


### Line Plot for ip addresses for each party type in one graph ###
plt.figure(figsize=(16, 8))

combined_data = data[data['Traffic Type'].isin(['First Party', 'Support Party', 'Third Party'])]
packets = combined_data.groupby(['Time Interval', 'Destination'])['Length'].sum().unstack(fill_value=0)
ip_addresses = packets.columns
cumulative_counts = packets.cumsum()

color_map = {ip: color for ip, color in zip(ip_addresses, cm.rainbow(np.linspace(0, 1, len(ip_addresses))))}

for ip in ip_addresses:
    ip_details = ip_owner_df[ip_owner_df['IP Address'] == ip]
    final_cumsum = cumulative_counts[ip].iloc[-1]
    if not ip_details.empty:
        isp = ip_details.iloc[0]['ISP']
        service = ip_details.iloc[0]['Service']
        if service != "Unknown":
            label = f"{ip} ({isp}, {service}) - {final_cumsum}B"
        else:
            label = f"{ip} ({isp}) - {final_cumsum}B"
    else:
        label = f"{ip} - {final_cumsum}B"
    plt.plot(packets.index, packets[ip], label=label, color=color_map[ip], linewidth=2, alpha=0.7)


# Add solo vertical lines for rounds
if not "8hCapture.csv" in input_csv:
    for i in range (0, 6):
        place = i * 2 + 1
        plt.axvline(x=place, color='cyan', linestyle='--', linewidth=1)

plt.title("Traffic Volume for All Traffic", fontsize=18)
plt.xlabel("Time Interval (hours)", fontsize=16)
plt.ylabel("Traffic Volume (bytes)", fontsize=16)
plt.tick_params(axis='x', labelsize=14, rotation=45)
plt.tick_params(axis='y', labelsize=14)

if "8hCapture.csv" in input_csv:
    plt.xticks(x_positions, labels=[f"{x * 0.25:.1f}" for x in x_positions], rotation=45)
else:
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)

plt.legend(bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=14)
plt.tight_layout()
output_file = os.path.join(output_dir, f"line_all_ip_address_traffic.png")
plt.savefig(output_file)
print(f"Line plot for all traffic saved to {output_file}")
plt.close()



### Line Plot for ip addresses for each party type ###
for traffic_type in ['First Party', 'Third Party']:
    plt.figure(figsize=(14, 9))
    
    traffic_data = data[data['Traffic Type'] == traffic_type]
    if traffic_data.empty:
        print(f"No data available for {traffic_type}. Skipping...")
        continue
        
    packets = traffic_data.groupby(['Time Interval', 'Destination'])['Length'].sum().unstack(fill_value=0)
    filtered_packets = packets.loc[:, packets.sum() > 1000]
    ip_addresses = filtered_packets.columns
    cumulative_counts = filtered_packets.cumsum()
    
    color_map = {ip: color for ip, color in zip(ip_addresses, cm.rainbow(np.linspace(0, 1, len(ip_addresses))))}

    for ip in ip_addresses:
        ip_details = ip_owner_df[ip_owner_df['IP Address'] == ip]
        final_cumsum = cumulative_counts[ip].iloc[-1]
        if not ip_details.empty:
            isp = ip_details.iloc[0]['ISP']
            service = ip_details.iloc[0]['Service']
            if service != "Unknown":
                label = f"{ip} ({isp}, {service}) - {final_cumsum}B"
            else:
                label = f"{ip} ({isp}) - {final_cumsum}B"
        else:
            label = f"{ip} - {final_cumsum}B"
        plt.plot(filtered_packets.index, filtered_packets[ip], label=label, color=color_map[ip], linewidth=2, alpha=0.7)

    plt.title(f'Timeline of {traffic_type} Traffic', fontsize=18)
    plt.xlabel("Time (hours)", fontsize=16)
    plt.ylabel("Traffic Volume (bytes)", fontsize=16)
    plt.tick_params(axis='x', labelsize=14, rotation=45)
    plt.tick_params(axis='y', labelsize=14)

    # Add for solo vertical lines
    if not "8hCapture.csv" in input_csv:
        for i in range (0, 6):
            place = i * 2 + 1
            plt.axvline(x=place, color='cyan', linestyle='--', linewidth=1)

    if "8hCapture.csv" in input_csv:
        plt.xticks(x_positions, labels=[f"{x * 0.25:.1f}" for x in x_positions], rotation=45)
    else:
        plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    
    plt.legend(loc='upper right', fontsize=12)
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"line_combined_{traffic_type.lower().replace(' ', '_')}_traffic.png")
    plt.savefig(output_file)
    print(f"Line plot saved to {output_file}")
    plt.close()



### Log Bar Plot for traffic type ###
first_party_traffic = data.groupby('Time Interval')['First Party Traffic'].sum()
support_party_traffic = data.groupby('Time Interval')['Support Party Traffic'].sum()
third_party_traffic = data.groupby('Time Interval')['Third Party Traffic'].sum()

max_value = (first_party_traffic + support_party_traffic + third_party_traffic).max()

bar_width = 0.6
time_intervals = first_party_traffic.index.get_level_values('Time Interval').unique()
x_positions = np.arange(len(time_intervals))

plt.figure(figsize=(12, 8))
plt.bar(x_positions, first_party_traffic.values, bar_width, label="First Party Traffic")
plt.bar(x_positions, support_party_traffic.values, bar_width, bottom=first_party_traffic.values, label="Support Party Traffic", color="cyan")
plt.bar(x_positions, third_party_traffic.values, bar_width, bottom=(first_party_traffic.values + support_party_traffic.values), label="Third Party Traffic", color="orange")

plt.yscale('log')
plt.title("(Log) Traffic Volume: First vs Support vs Third Party Traffic", fontsize=18)
plt.xlabel("Time Interval (hours)", fontsize=16)
plt.ylabel("Traffic Volume (bytes)", fontsize=16)
plt.ylim(0, max_value * 1.1)
plt.tick_params(axis='x', labelsize=14, rotation=45)
plt.tick_params(axis='y', labelsize=14)

if "8hCapture.csv" in input_csv:
    plt.xticks(x_positions, labels=[f"{x * 0.25:.1f}" for x in x_positions], rotation=45)
else:
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    
plt.legend(loc="upper right", fontsize=14)
plt.tight_layout()
 
output_file = os.path.join(output_dir, "bar_log_different_party_traffic.png")
plt.savefig(output_file)
print(f"Bar plot saved to {output_file}")
plt.close()



### Bar Plot for traffic type ###
first_party_traffic = data.groupby('Time Interval')['First Party Traffic'].sum()
support_party_traffic = data.groupby('Time Interval')['Support Party Traffic'].sum()
third_party_traffic = data.groupby('Time Interval')['Third Party Traffic'].sum()

max_value = (first_party_traffic + support_party_traffic + third_party_traffic).max()

bar_width = 0.6
time_intervals = first_party_traffic.index.get_level_values('Time Interval').unique()
x_positions = np.arange(len(time_intervals))

plt.figure(figsize=(12, 8))
plt.bar(x_positions, first_party_traffic.values, bar_width, label="First Party Traffic")
plt.bar(x_positions, support_party_traffic.values, bar_width, bottom=first_party_traffic.values, label="Support Party Traffic", color="cyan")
plt.bar(x_positions, third_party_traffic.values, bar_width, bottom=(first_party_traffic.values + support_party_traffic.values), label="Third Party Traffic", color="orange")


plt.title("Traffic Volume: First vs Support vs Third Party Traffic", fontsize=18)
plt.xlabel("Time Interval (hours)", fontsize=16)
plt.ylabel("Traffic Volume (bytes)", fontsize=16)
plt.ylim(0, max_value * 1.1)
plt.tick_params(axis='x', labelsize=14, rotation=45)
plt.tick_params(axis='y', labelsize=14)

if "8hCapture.csv" in input_csv:
    plt.xticks(x_positions, labels=[f"{x * 0.25:.1f}" for x in x_positions], rotation=45)
else:
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    
plt.legend(loc="upper left", fontsize=14)
plt.tight_layout()
 
output_file = os.path.join(output_dir, "bar_different_party_traffic.png")
plt.savefig(output_file)
print(f"Bar plot saved to {output_file}")
plt.close()


#####################     Shows traffic volume for encrypted data     #####################
# Add column for encryption
data['Is Encrypted'] = data['Protocol'].apply(filters.is_encrypted_traffic)
data['Encrypted Traffic'] = data['Length'].where(data['Is Encrypted'], 0).astype(float)

data['Traffic Category'] = data.apply(lambda row: f"{row['Traffic Type']} - Encrypted" if row['Is Encrypted'] else f"{row['Traffic Type']} - Plain-Text", axis=1)

traffic_by_category = data.groupby(['Time Interval', 'Traffic Category'])['Length'].sum().unstack(fill_value=0)


### Bar Plot for experiment ###
bar_width = 0.6
x_positions = np.arange(len(traffic_by_category.index))

plt.figure(figsize=(12, 8))
for i, category in enumerate(traffic_by_category.columns):
    plt.bar(x_positions, traffic_by_category[category].values, bottom=traffic_by_category.iloc[:, :i].sum(axis=1).values, label=category)

plt.yscale('log')
plt.title("Traffic Volume: Encrypted vs Plain-Text for different Parties")
plt.xlabel("Time Interval (hours)")
plt.ylabel("Traffic Volume (bytes)")

if "8hCapture.csv" in input_csv:
    plt.xticks(x_positions, labels=[f"{x * 0.25:.1f}" for x in x_positions], rotation=45)
else:
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    
plt.legend(loc="upper right")
plt.tight_layout()

output_file = os.path.join(output_dir, "bar_combined_encrypted_vs_plain_text_traffic.png")
plt.savefig(output_file)
print(f"Bar plot saved to {output_file}")
plt.close()

"""


