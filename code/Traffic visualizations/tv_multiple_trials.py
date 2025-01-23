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

# Time for each interaction
if "Touch Commands" in input_csv:
    interaction_interval = 15
    data = data[data['Time'] < 310]
elif "Voice Commands" in input_csv:
    interaction_interval = 30
elif "Pairing Sequence" in input_csv:
    interaction_interval == 0



#####################     Shows traffic volume for the types of parties     #####################
# Classify traffic for the analysis
#ip_owner_df['Traffic Type'] = ip_owner_df.apply(lambda row: filters.classify_traffic_by_service(row['Service'], row['Protocol']), axis=1)

#data['Traffic Type'] = data['Destination'].map(ip_owner_df.set_index('IP Address')['Traffic Type'])
data['Service'] = data['Destination'].map(ip_owner_df.set_index('IP Address')['Service'])

data['Traffic Type'] = data.apply(lambda row: filters.classify_traffic_by_service(row['Service'], row['Protocol']), axis=1)

data['Private Traffic'] = data['Length'].where(data['Traffic Type'] == 'Private', 0).astype(float)
data['First Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'First Party', 0).astype(float)
data['Support Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'Support Party', 0).astype(float)
data['Third Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'Third Party', 0).astype(float)


# Group by time intervals
data_10 = data.copy()
data_10 = data_10[data_10['Traffic Type'] != 'Private']
data_10['Time Interval'] = (data_10['Time'] // 10).astype(int)
data['Time Interval'] = (data['Time'] // 30).astype(int)

# For outliers if need be, but keep it in line plots
data_copy = data.copy()
trial_to_exclude = 4
#data = data[data['ExperimentTrial'] != trial_to_exclude]


traffic_by_experiment = data.groupby(['Time Interval', 'ExperimentTrial', 'Traffic Type'])['Length'].sum().unstack(level='Traffic Type', fill_value=0)
traffic_by_experiment_copy = data_copy.groupby(['Time Interval', 'ExperimentTrial', 'Traffic Type'])['Length'].sum().unstack(level='Traffic Type', fill_value=0)

time_intervals = traffic_by_experiment.index.get_level_values('Time Interval').unique()
x_positions = np.arange(len(time_intervals))


readability_colors = {
    'Unreadable': 'blue',
    'Partially Readable': 'orange',
    'Readable': 'green',
    'Unknown': 'gray'
}
data['Readability'] = data.apply(lambda row: filters.check_readability(row['Protocol'], row['Info']), axis=1)

"""
## Print Statistics ##
print(f"Private address: {data[data['Traffic Type'] == 'Private']['Destination'].unique()}")

pt_volume = data['Private Traffic'].sum() / 5
fp_volume = data['First Party Traffic'].sum() / 5
sp_volume = data['Support Party Traffic'].sum() / 5
tp_volume = data['Third Party Traffic'].sum() / 5
tt_volume = fp_volume + sp_volume + tp_volume
tv_volume = pt_volume + fp_volume + sp_volume + tp_volume
print(f"Private: {pt_volume / 1048576} MB with {pt_volume / tv_volume * 100}%")
print(f"Public: {tt_volume / 1048576} MB with {tt_volume / tv_volume * 100}%")
print(f"First Party: {fp_volume / 1048576} MB with {fp_volume / tt_volume * 100}%")
print(f"Support Party: {sp_volume / 1024} KB with {sp_volume / tt_volume * 100}%")
print(f"Third Party: {tp_volume / 1024} KB with {tp_volume / tt_volume * 100}%")

#print(data[data['Traffic Type'] == 'Support Party']['Destination'])
print(f"Support addreess: {data[(data['Traffic Type'] == 'Support Party')]['Destination'].unique()}")
print(f"Support: {data[(data['Destination'] == '157.240.17.61')]['Length'].sum() / 1024} KB")

print(data[data['Protocol'] == 'TLSv1']['Time'])

print(f"Google: {data[(data['Traffic Type'] == 'Third Party') & (data['Service'] == 'Google')]['Length'].sum() / 1024} KB")
print(f"Spotify: {data[(data['Traffic Type'] == 'Third Party') & (data['Service'] == 'Spotify')]['Length'].sum() / 1024} KB")
print(f"Rest: {data[(data['Traffic Type'] == 'Third Party') & (data['Service'] != 'Spotify') & (data['Service'] != 'Google')]['Length'].sum() / 1024} KB")

print(f"Spotify protocol: {data[(data['Traffic Type'] == 'Third Party') & (data['Service'] == 'Spotify')]['Protocol'].unique()}")
print(f"Spotify TCP: {data[(data['Traffic Type'] == 'Third Party') & (data['Service'] == 'Spotify') & (data['Protocol'] == 'TCP')]['Length'].sum() / 1024} KB")
print(f"Spotify TLSv1.2: {data[(data['Traffic Type'] == 'Third Party') & (data['Service'] == 'Spotify') & (data['Protocol'] == 'TLSv1.2')]['Length'].sum() / 1024} KB")
print(f"Spotify TLSv1.3: {data[(data['Traffic Type'] == 'Third Party') & (data['Service'] == 'Spotify') & (data['Protocol'] == 'TLSv1.3')]['Length'].sum() / 1024} KB")

partially_readable_third_party = data[(data['Traffic Type'] == 'Third Party') & (data['Readability'] == 'Partially Readable')]
#print(partially_readable_third_party[['Destination', 'Protocol', 'Info', 'Length']])
#print(f"Support Party: {data[(data['Traffic Type'] == 'Support Party') & (data['Time'] > 420) & (data['Time'] < 540)][['Destination', 'ExperimentTrial']]}")

print(f"Third-party NTP: {data[(data['Traffic Type'] == 'Third Party') & (data['Protocol'] == 'NTP')]['Service'].unique()}")
print(f"Third-party QUIC: {data[(data['Traffic Type'] == 'Third Party') & (data['Protocol'] == 'QUIC')]['Service'].unique()}")
print(f"Third-party TCP: {data[(data['Traffic Type'] == 'Third Party') & (data['Protocol'] == 'TCP')]['Service'].unique()}")
print(f"Third-party TLSv1.2: {data[(data['Traffic Type'] == 'Third Party') & (data['Protocol'] == 'TLSv1.2')]['Service'].unique()}")
print(f"Third-party TLSv1.3: {data[(data['Traffic Type'] == 'Third Party') & (data['Protocol'] == 'TLSv1.3')]['Service'].unique()}")
print(f"Third-party Partially Readable TLSv1.3: {data[(data['Traffic Type'] == 'Third Party') & (data['Protocol'] == 'TLSv1.3') & (data['Readability'] == 'Partially Readable')]['Service'].unique()}")

120
500
Voice:
WhatsApp - 157.240.17.60: 620 / 620 / 620 / 620 / 620
WhatsApp - 157.240.17.61: 590-690 / 58-85, 590-690 / 590-690 / 550-690 / 56, 216-300, 590-690
Insta - 157.240.17.63: 554 / 646-670 / throughout / none /  none


### Bar Plot for all traffic by protocol ###
refined_readability_bytes = data.groupby(['Protocol', 'Readability'])['Length'].sum().reset_index()

pivot_data = refined_readability_bytes.pivot(index='Protocol', columns='Readability', values='Length').fillna(0)

pivot_data = pivot_data[[col for col in readability_colors if col in pivot_data.columns]]
colors = [readability_colors[col] for col in pivot_data.columns]

pivot_data.plot(kind='bar', stacked=True, figsize=(12, 8))
plt.yscale('log')
plt.title('Traffic Volume for All Traffic by Protocol and Readability',  fontsize=20)
plt.xlabel('Protocol',  fontsize=18)
plt.ylabel('Total Bytes',  fontsize=18)
plt.tick_params(axis='x', labelsize=16, rotation=45)
plt.tick_params(axis='y', labelsize=16)
plt.legend(title='Readability', loc='upper left',  fontsize=16, title_fontsize=16)
plt.tight_layout()

output_file = os.path.join(output_dir, f"bar_log_all_protocol_traffic.pdf")
plt.savefig(output_file, format='pdf')
print(f"Bar plot for all traffic saved to {output_file}")
plt.close()


### Bar Plot for different party type traffic by protocol ###
for traffic_type in ['Private', 'First Party', 'Support Party', 'Third Party']:
    party_data = data[data['Traffic Type'] == traffic_type]
    party_data.loc[:, 'Readability'] = party_data.apply(lambda row: filters.check_readability(row['Protocol'], row['Info']), axis=1)

    refined_readability_bytes = party_data.groupby(['Protocol', 'Readability'])['Length'].sum().reset_index()
        
    pivot_data = refined_readability_bytes.pivot(index='Protocol', columns='Readability', values='Length').fillna(0)

    pivot_data = pivot_data[[col for col in readability_colors if col in pivot_data.columns]]
    colors = [readability_colors[col] for col in pivot_data.columns]
    
    pivot_data.plot(kind='bar', stacked=True, figsize=(12, 8))
    plt.yscale('log')
    plt.title(f'Traffic Volume for {traffic_type} by Protocol and Readability',  fontsize=20)
    plt.xlabel('Protocol',  fontsize=18)
    plt.ylabel('Total Bytes',  fontsize=18)
    plt.tick_params(axis='x', labelsize=16, rotation=45)
    plt.tick_params(axis='y', labelsize=16)
    plt.legend(title='Readability', loc='upper left',  fontsize=16, title_fontsize=16)
    plt.tight_layout()
    
    output_file = os.path.join(output_dir, f"bar_log_{traffic_type.lower().replace(' ', '_')}_protocol_traffic.pdf")
    plt.savefig(output_file, format='pdf')
    print(f"Bar plot for all traffic saved to {output_file}")
    plt.close()


### Scatter Plot for all traffic by trial ###
plt.figure(figsize=(12, 8))

data_10 = data_10[data_10['Traffic Type'] != 'Private']

for experiment in data_10['ExperimentTrial'].unique():
    trial_data = data_10[data_10['ExperimentTrial'] == experiment]
    grouped_data = trial_data.groupby('Time Interval')['Length'].sum()
    plt.scatter(grouped_data.index * 10 / 60, grouped_data.values, label=f"Trial {experiment}", alpha=0.7)


if (interaction_interval == 15):
    plt.axvline(x=30 / 60, color='cyan', linestyle='--', linewidth=1)
    for i in range (0, 8):
        place = i * 30 + 90
        plt.axvline(x=place, color='cyan', linestyle='--', linewidth=1)
    for i in range (0, 4):
        place = i * 15 + 240
        plt.axvline(x=place / 60, color='cyan', linestyle='--', linewidth=1)
elif (interaction_interval == 30):
    plt.axvline(x=30 / 60, color='cyan', linestyle='--', linewidth=1)
    for i in range (0, 21):
        place = i * 30 + 90
        plt.axvline(x=place / 60, color='cyan', linestyle='--', linewidth=1)
    
plt.yscale('log')
plt.title("(Log) Traffic Volume for Public Traffic by Trial", fontsize=20)
plt.xlabel("Time (minutes)", fontsize=18)
plt.ylabel("Traffic Volume (bytes)", fontsize=18)
plt.tick_params(axis='x', labelsize=16, rotation=45)
plt.tick_params(axis='y', labelsize=16)
plt.legend(loc='upper right', fontsize=15)
plt.tight_layout()

output_file = os.path.join(output_dir, f"scatter_log_public_traffic.pdf")
plt.savefig(output_file, format='pdf')
print(f"Scatter plot for all traffic saved to {output_file}")
plt.close()

"""

### Line Plot for packet distribution ###
packet_size_distribution = data['Length'].value_counts().sort_index()

plt.figure(figsize=(12, 6))
plt.plot(packet_size_distribution.index, packet_size_distribution.values)
plt.title('Packet Size Distribution', fontsize=20)
plt.xlabel('Packet Size (Bytes)', fontsize=18)
plt.ylabel('Packet Count', fontsize=18)
plt.tick_params(axis='x', labelsize=16, rotation=45)
plt.tick_params(axis='y', labelsize=16)
plt.tight_layout()
output_file = os.path.join(output_dir, f"packet_distribution.pdf")
plt.savefig(output_file, format='pdf')
print(f"Line plot for packet distribution saved to {output_file}")
plt.close()
"""

### Line Plot for all traffic by trial ###
experiments = traffic_by_experiment_copy.index.get_level_values('ExperimentTrial').unique()

plt.figure(figsize=(12, 8))
        
for experiment in experiments:
    total_traffic = traffic_by_experiment_copy.xs(experiment, level='ExperimentTrial')
    traffic_sum = total_traffic.sum(axis=1)
    #print(traffic)
    time_intervals = total_traffic.index.get_level_values('Time Interval')
    plt.plot(time_intervals, traffic_sum.values, label=f"Trial {experiment}", linewidth=2, alpha=0.7)
    	
# Add for solo vertical lines
if (interaction_interval == 15):
    plt.axvline(x=1, color='magenta', linestyle='--', linewidth=1, label='Power on glasses')
    plt.axvline(x=6, color='cyan', linestyle='--', linewidth=1, label='Import media')
if (interaction_interval == 30):
    plt.axvline(x=1, color='magenta', linestyle='--', linewidth=1, label='Power on glasses')
    plt.axvline(x=18, color='cyan', linestyle='--', linewidth=1, label='Import media')

plt.yscale('log')
plt.title("(Log) Traffic Volume for Public Traffic",  fontsize=20)
plt.xlabel("Time (minutes)", fontsize=18)
plt.ylabel("Traffic Volume (bytes)", fontsize=18)
plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
plt.tick_params(axis='x', labelsize=16, rotation=45)
plt.tick_params(axis='y', labelsize=16)
plt.legend(loc='lower center', ncol=2, fontsize=16, title_fontsize=13)
plt.tight_layout()

output_file = os.path.join(output_dir, f"line_log_all_traffic.pdf")
plt.savefig(output_file, format='pdf')
print(f"Line plot for all traffic saved to {output_file}")
plt.close()


### Line Plot for ip addresses for each party type ###
for traffic_type in ['First Party', 'Support Party', 'Third Party']:
    plt.figure(figsize=(12, 8))
    
    traffic_data = data[data['Traffic Type'] == traffic_type]
    if traffic_data.empty:
        print(f"No data available for {traffic_type}. Skipping...")
        continue
        
    packets = traffic_data.groupby(['Time Interval', 'Destination'])['Length'].sum().unstack(fill_value=0)
    ip_addresses = packets.columns
    cumulative_counts = packets.cumsum()

    plt.figure(figsize=(16, 8))
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

    plt.title(f'Timeline of {traffic_type} Traffic', fontsize=18)
    plt.xlabel("Time (minutes)", fontsize=16)
    plt.ylabel("Traffic Volume (bytes)", fontsize=16)
    plt.tick_params(axis='x', labelsize=14, rotation=45)
    plt.tick_params(axis='y', labelsize=14)
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    
    # Add for solo vertical lines
    if (interaction_interval == 15):
    	plt.axvline(x=1, color='magenta', linestyle='--', linewidth=1, label='Power on glasses and Open app')
    	plt.axvline(x=6, color='cyan', linestyle='--', linewidth=1, label='Import media')
    	
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=14)
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"line_combined_{traffic_type.lower().replace(' ', '_')}_traffic.png")
    plt.savefig(output_file)
    print(f"Line plot saved to {output_file}")
    plt.close()


### Line Plot for ip addresses for each party type keeping outlier ###
for traffic_type in ['Private', 'First Party', 'Support Party', 'Third Party']:
    
    traffic_data = data_copy[data_copy['Traffic Type'] == traffic_type]
    
    if traffic_data.empty:
        print(f"No data available for {traffic_type}. Skipping...")
        continue
        
    packets = traffic_data.groupby(['Time Interval', 'Destination'])['Length'].sum().unstack(fill_value=0)
    filtered_packets = packets.loc[:, packets.sum() > 300]
    ip_addresses = filtered_packets.columns
    cumulative_counts = filtered_packets.cumsum()
    

    plt.figure(figsize=(15, 8))
    color_map = {ip: color for ip, color in zip(ip_addresses, cm.rainbow(np.linspace(0, 1, len(ip_addresses))))}

    for ip in ip_addresses:
        ip_details = ip_owner_df[ip_owner_df['IP Address'] == ip]
        final_cumsum = cumulative_counts[ip].iloc[-1]
        if not ip_details.empty:
            isp = ip_details.iloc[0]['ISP']
            service = ip_details.iloc[0]['Service']
            if service != "Unknown":
                label = f"{ip} ({service}) - {final_cumsum}B"
            else:
                label = f"{ip} ({isp}) - {final_cumsum}B"
        else:
            label = f"{ip} - {final_cumsum}B"
        plt.plot(filtered_packets.index, filtered_packets[ip], label=label, color=color_map[ip], linewidth=2, alpha=0.7)
    
    plt.title(f'IP Address of {traffic_type} Traffic', fontsize=20)
    plt.xlabel("Time (minutes)", fontsize=18)
    plt.ylabel("Traffic Volume (bytes)", fontsize=18)
    plt.tick_params(axis='x', labelsize=16, rotation=45)
    plt.tick_params(axis='y', labelsize=16)
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    
    # Add for solo vertical lines
    if (interaction_interval == 15):
    	plt.axvline(x=1, color='magenta', linestyle='--', linewidth=1, label='Power on glasses and Open app')
    	plt.axvline(x=6, color='cyan', linestyle='--', linewidth=1, label='Import media')
    	
    plt.legend(title='IP Addresses', bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=15, title_fontsize=16)
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"line_combined_keeping_outlier_{traffic_type.lower().replace(' ', '_')}_traffic.pdf")
    plt.savefig(output_file, format='pdf')
    print(f"Line plot saved to {output_file}")
    plt.close()


### Line Plot (Log) for ip addresses for each party type keeping outlier ###
for traffic_type in ['First Party', 'Support Party', 'Third Party']:
    plt.figure(figsize=(12, 8))
    
    traffic_data = data_copy[data_copy['Traffic Type'] == traffic_type]
    
    if traffic_data.empty:
        print(f"No data available for {traffic_type}. Skipping...")
        continue
        
    packets = traffic_data.groupby(['Time Interval', 'Destination'])['Length'].sum().unstack(fill_value=0)
    ip_addresses = packets.columns
    cumulative_counts = packets.cumsum()
    packets = packets.replace(0, 1)

    plt.figure(figsize=(16, 8))
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
    
    plt.yscale('log')
    plt.title(f'Timeline of {traffic_type} Traffic (Log)')
    plt.xlabel("Time (minutes)")
    plt.ylabel("Traffic Volume (bytes)")
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    
    # Add for solo vertical lines
    if (interaction_interval == 15):
    	plt.axvline(x=1, color='magenta', linestyle='--', linewidth=1, label='Power on glasses and Open app')
    	plt.axvline(x=6, color='cyan', linestyle='--', linewidth=1, label='Import media')
    	
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title='IP Addresses', fontsize='small')
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"line_combined_log_keeping_outlier_{traffic_type.lower().replace(' ', '_')}_traffic.png")
    plt.savefig(output_file)
    print(f"Line plot saved to {output_file}")
    plt.close()


### Bar Plot for combined trials mean ###
first_party_traffic_mean = traffic_by_experiment['First Party'].groupby(level='Time Interval').mean()
if 'Support Party' in traffic_by_experiment:
    support_party_traffic_mean = traffic_by_experiment['Support Party'].groupby(level='Time Interval').mean()
else:
    support_party_traffic_mean = pd.Series(0, index=traffic_by_experiment.index.get_level_values('Time Interval').unique())

third_party_traffic_mean = traffic_by_experiment['Third Party'].groupby(level='Time Interval').mean()

bar_width = 0.6
x_positions = np.arange(len(first_party_traffic_mean))
max_value = (first_party_traffic_mean.values + support_party_traffic_mean.values + third_party_traffic_mean.values).max()

plt.figure(figsize=(12, 8))
plt.bar(x_positions, first_party_traffic_mean.values, bar_width, label="First-Party Traffic")
plt.bar(x_positions, support_party_traffic_mean.values, bar_width, bottom=first_party_traffic_mean.values, label="Support-Party Traffic", color="cyan")
plt.bar(x_positions, third_party_traffic_mean.values, bar_width, bottom=(first_party_traffic_mean.values + support_party_traffic_mean.values), label="Third-Party Traffic", color="orange")


plt.yscale('log')
plt.title("(Log) Traffic Volume: First vs Support vs Third Party Traffic", fontsize=20)
plt.xlabel("Time (minutes)", fontsize=18)
plt.ylabel("Traffic Volume (bytes)", fontsize=18)

ticks = [10**i for i in range(4, 7)]  
plt.yticks(ticks, labels=[f"$10^{i}$" for i in range(4, 7)])
plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
plt.tick_params(axis='x', labelsize=16)
plt.tick_params(axis='y', labelsize=16)
plt.legend(loc="upper right", fontsize=16)
plt.tight_layout()

output_file = os.path.join(output_dir, "bar_log_combined_different_party_traffic.pdf")
plt.savefig(output_file, format='pdf')
print(f"Bar plot saved to {output_file}")
plt.close()


### Line Plot for the types of parties ###
experiments = traffic_by_experiment_copy.index.get_level_values('ExperimentTrial').unique()

def plot_traffic_by_type(traffic_type, file_suffix, title):
    plt.figure(figsize=(12, 8))
        
    for experiment in experiments:
        if not traffic_type in traffic_by_experiment_copy.columns or not traffic_by_experiment_copy[traffic_type].sum() > 0:
            print(f"No data available for {traffic_type}. Skipping...")
            return
        
        traffic = traffic_by_experiment_copy.loc[(slice(None), experiment), traffic_type]
        time_intervals = traffic.index.get_level_values('Time Interval')
        plt.plot(time_intervals, traffic.values, label=f"Trial {experiment}", linewidth=2, alpha=0.7)
        
    # Add for solo vertical lines
    if (interaction_interval == 15):
    	plt.axvline(x=1, color='magenta', linestyle='--', linewidth=1, label='Power on glasses')
    	plt.axvline(x=6, color='cyan', linestyle='--', linewidth=1, label='Import media')
    

    plt.title(f'{title}', fontsize=20)
    plt.xlabel("Time (minutes)", fontsize=18)
    plt.ylabel("Traffic Volume (bytes)", fontsize=18)
    plt.tick_params(axis='x', labelsize=16, rotation=45)
    plt.tick_params(axis='y', labelsize=16)
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    plt.legend(loc='upper right', fontsize=16)
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"line_{file_suffix}.pdf")
    plt.savefig(output_file, format='pdf')
    print(f"Line plot for {traffic_type} saved to {output_file}")
    plt.close()

plot_traffic_by_type(
    traffic_type='First Party',
    file_suffix='first_party_traffic',
    title='Traffic Volume for First Parties by Trial'
)

plot_traffic_by_type(
    traffic_type='Support Party',
    file_suffix='support_party_traffic',
    title='Traffic Volume for Support Parties by Trial'
)

plot_traffic_by_type(
    traffic_type='Third Party',
    file_suffix='third_party_traffic',
    title='Traffic Volume for Third Parties by Trial'
)


### Line Plot (Log) for the types of parties ###
experiments = traffic_by_experiment_copy.index.get_level_values('ExperimentTrial').unique()

def plot_traffic_by_type(traffic_type, file_suffix, title):
    plt.figure(figsize=(12, 8))
        
    for experiment in experiments:
        if not traffic_type in traffic_by_experiment_copy.columns or not traffic_by_experiment_copy[traffic_type].sum() > 0:
            print(f"No data available for {traffic_type}. Skipping...")
            return
        
        traffic = traffic_by_experiment_copy.loc[(slice(None), experiment), traffic_type]
        traffic = traffic.replace(0, 1)
        time_intervals = traffic.index.get_level_values('Time Interval')
        plt.plot(time_intervals, traffic.values, label=f"Trial {experiment}", linewidth=2, alpha=0.7)
        
    # Add for solo vertical lines
    if (interaction_interval == 15):
    	plt.axvline(x=1, color='magenta', linestyle='--', linewidth=1, label='Power on glasses and Open app')
    	plt.axvline(x=6, color='cyan', linestyle='--', linewidth=1, label='Import media')

    plt.yscale('log')
    plt.title(f'(Log) {title}', fontsize=20)
    plt.xlabel("Time (minutes)", fontsize=18)
    plt.ylabel("Traffic Volume (bytes)", fontsize=18)
    plt.tick_params(axis='x', labelsize=16, rotation=45)
    plt.tick_params(axis='y', labelsize=16)
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    plt.legend(loc='upper right', fontsize=16)
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"line_log_{file_suffix}.pdf")
    plt.savefig(output_file, format='pdf')
    print(f"Line plot for {traffic_type} saved to {output_file}")
    plt.close()

plot_traffic_by_type(
    traffic_type='First Party',
    file_suffix='first_party_traffic',
    title='Traffic Volume for First Parties by Trial'
)

plot_traffic_by_type(
    traffic_type='Support Party',
    file_suffix='support_party_traffic',
    title='Traffic Volume for Support Parties by Trial'
)

plot_traffic_by_type(
    traffic_type='Third Party',
    file_suffix='third_party_traffic',
    title='Traffic Volume for Third Parties by Trial'
)


### Bar Plot for each specific trial ###
for experiment_trial in traffic_by_experiment.index.get_level_values('ExperimentTrial').unique():
    traffic_for_trial = traffic_by_experiment.xs(experiment_trial, level='ExperimentTrial')

    first_party_traffic = traffic_for_trial['First Party']
    if 'Support Party' in traffic_for_trial:
        support_party_traffic = traffic_for_trial['Support Party']
    else:
        support_party_traffic = pd.Series(0, index=traffic_for_trial.index.get_level_values('Time Interval').unique())
    third_party_traffic = traffic_for_trial['Third Party']

    bar_width = 0.6
    x_positions = np.arange(len(first_party_traffic))
    max_value = (first_party_traffic_mean.values + support_party_traffic_mean.values + third_party_traffic_mean.values).max()

    plt.figure(figsize=(12, 8))
    plt.bar(x_positions, first_party_traffic.values, bar_width, label="First Party Traffic")
    plt.bar(x_positions, support_party_traffic.values, bar_width, bottom=first_party_traffic.values, label="Support Party Traffic", color="cyan")
    plt.bar(x_positions, third_party_traffic.values, bar_width, bottom=(first_party_traffic.values + support_party_traffic.values), label="Third-Party Traffic", color="orange")

    plt.title(f"Traffic Volume for {experiment_trial}: First vs Support vs Third Party Traffic")
    plt.xlabel("Time Interval (minutes)")
    plt.ylabel("Traffic Volume (bytes)")
    plt.ylim(0, max_value * 1.1)
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    plt.legend(loc="upper left")
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"bar_{experiment_trial}_traffic.png")
    plt.savefig(output_file)
    print(f"Bar plot saved to {output_file}")
    plt.close()


#####################     Shows traffic volume for encrypted data     #####################
# Add column for encryption
data['Is Encrypted'] = data['Protocol'].apply(filters.is_encrypted_traffic)
data['Encrypted Traffic'] = data['Length'].where(data['Is Encrypted'], 0).astype(float)

data['Traffic Category'] = data.apply(lambda row: f"{row['Traffic Type']} - Encrypted" if row['Is Encrypted'] else f"{row['Traffic Type']} - Plain-Text", axis=1)

traffic_by_category = data.groupby(['Time Interval', 'Traffic Category'])['Length'].sum().unstack(fill_value=0)

### Bar Plot for combined trials ###
bar_width = 0.6
x_positions = np.arange(len(traffic_by_category.index))

plt.figure(figsize=(12, 8))
max_value = traffic_by_category.sum(axis=1).max()
for i, category in enumerate(traffic_by_category.columns):
    plt.bar(x_positions, traffic_by_category[category].values, bottom=traffic_by_category.iloc[:, :i].sum(axis=1).values, label=category)

plt.title("Traffic Volume: Encrypted vs Plain-Text for different Parties")
plt.xlabel("Time Interval (minutes)")
plt.ylabel("Traffic Volume (bytes)")
plt.ylim(0, max_value * 1.1)
plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
plt.legend(loc="upper left")
plt.tight_layout()

output_file = os.path.join(output_dir, "bar_combined_encrypted_vs_plain_text_traffic.png")
plt.savefig(output_file)
print(f"Bar plot saved to {output_file}")
plt.close()

"""
