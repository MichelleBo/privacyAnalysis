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
elif "Voice Commands" in input_csv:
    interaction_interval = 0
elif "Pairing Sequence" in input_csv:
    interaction_interval == 0



#####################     Shows traffic volume for the types of parties     #####################
# Classify traffic for the analysis
ip_owner_df['Traffic Type'] = ip_owner_df['Service'].apply(filters.classify_traffic_by_service)
data['Traffic Type'] = data['Destination'].map(ip_owner_df.set_index('IP Address')['Traffic Type'])

data['First Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'First Party', 0).astype(float)
data['Support Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'Support Party', 0).astype(float)
data['Third Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'Third Party', 0).astype(float)


# Group by time intervals
data_10 = data.copy()
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



### Scatter Plot for all traffic by trial ###
plt.figure(figsize=(12, 8))

for experiment in data_10['ExperimentTrial'].unique():
    trial_data = data_10[data_10['ExperimentTrial'] == experiment]
    grouped_data = trial_data.groupby('Time Interval')['Length'].sum()
    plt.scatter(grouped_data.index * 10, grouped_data.values, label=f"Trial {experiment}", alpha=0.7)

for i in range (0, 24):
    place = i * 30
    plt.axvline(x=place, color='cyan', linestyle='--', linewidth=1)
    
plt.yscale('log')
plt.title(f'Traffic Volume for All Traffic (log)')
plt.xlabel("Time (seconds)")
plt.ylabel("Traffic Volume (bytes)")
plt.legend(loc='upper right', fontsize='small', title='Experiments')
plt.tight_layout()

output_file = os.path.join(output_dir, f"scatter_log_all_traffic.png")
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
    plt.axvline(x=1, color='magenta', linestyle='--', linewidth=1, label='Power on glasses and Open app')
    plt.axvline(x=6, color='cyan', linestyle='--', linewidth=1, label='Import media')

plt.title(f'Traffic Volume for all Traffic (Log)')
plt.xlabel("Time Interval (minutes)")
plt.yscale('log')
plt.ylabel("Traffic Volume (bytes)")
plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
plt.legend(loc='upper right', fontsize='small', title='Experiments')
plt.tight_layout()

output_file = os.path.join(output_dir, f"line_log_all_traffic.png")
plt.savefig(output_file)
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

    plt.title(f'Timeline of {traffic_type} Traffic')
    plt.xlabel("Time (minutes)")
    plt.ylabel("Traffic Volume (bytes)")
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    
    # Add for solo vertical lines
    if (interaction_interval == 15):
    	plt.axvline(x=1, color='magenta', linestyle='--', linewidth=1, label='Power on glasses and Open app')
    	plt.axvline(x=6, color='cyan', linestyle='--', linewidth=1, label='Import media')
    	
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title='IP Addresses', fontsize='small')
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"line_combined_{traffic_type.lower().replace(' ', '_')}_traffic.png")
    plt.savefig(output_file)
    print(f"Line plot saved to {output_file}")
    plt.close()


### Line Plot for ip addresses for each party type keeping outlier ###
for traffic_type in ['First Party', 'Support Party', 'Third Party']:
    plt.figure(figsize=(12, 8))
    
    traffic_data = data_copy[data_copy['Traffic Type'] == traffic_type]
    
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
    
    plt.title(f'Timeline of {traffic_type} Traffic')
    plt.xlabel("Time (minutes)")
    plt.ylabel("Traffic Volume (bytes)")
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    
    # Add for solo vertical lines
    if (interaction_interval == 15):
    	plt.axvline(x=1, color='magenta', linestyle='--', linewidth=1, label='Power on glasses and Open app')
    	plt.axvline(x=6, color='cyan', linestyle='--', linewidth=1, label='Import media')
    	
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title='IP Addresses', fontsize='small')
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"line_combined_keeping_outlier_{traffic_type.lower().replace(' ', '_')}_traffic.png")
    plt.savefig(output_file)
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


### Pie Chart for combined trials ###
first_party_traffic_count = data['First Party Traffic'].sum()
support_party_traffic_count = data['Support Party Traffic'].sum()
third_party_traffic_count = data['Third Party Traffic'].sum()

labels = ['First Party Traffic', 'Support Party Traffic', 'Third Party Traffic']
sizes = [first_party_traffic_count, support_party_traffic_count, third_party_traffic_count]

plt.figure(figsize=(8, 8))
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
plt.title('Proportion of Encrypted vs Unencrypted Traffic')
plt.tight_layout()

output_file = os.path.join(output_dir, "pie_encrypted_vs_unencrypted_pie_chart.png")
plt.savefig(output_file)
print(f"Pie chart saved to {output_file}")
plt.close()


### Pie Chart for third party traffic ###
third_party_data = data[data['Traffic Type'] == 'Third Party']
third_party_ip_traffic = third_party_data.groupby('Destination')['Length'].sum()
third_party_ip_traffic = third_party_ip_traffic.reset_index()
third_party_ip_traffic['ISP'] = third_party_ip_traffic['Destination'].map(ip_owner_df.set_index('IP Address')['ISP'])
third_party_ip_traffic['Service'] = third_party_ip_traffic['Destination'].map(ip_owner_df.set_index('IP Address')['Service'])

third_party_ip_traffic = third_party_ip_traffic.sort_values('Length', ascending=False)
# Define a threshold according to the need of the analysis
threshold = 0.019 * third_party_ip_traffic['Length'].sum()  
major_ips = third_party_ip_traffic[third_party_ip_traffic['Length'] >= threshold]
other_traffic = third_party_ip_traffic[third_party_ip_traffic['Length'] < threshold]['Length'].sum()

major_ips = major_ips.copy()
if other_traffic > 0:
    major_ips = pd.concat([major_ips, pd.DataFrame([{'Destination': 'Other', 'Length': other_traffic, 'ISP': '', 'Service': ''}])])

labels = [f"{row['Destination']}\n({row['ISP']}, {row['Service']})" if row['Service'] else f"{row['Destination']}\n({row['ISP']})" if row['Destination'] != "Other" else "Other" for _, row in major_ips.iterrows()]
sizes = major_ips['Length'].values

num_colors = len(major_ips)
if num_colors <= 20:
    color_palette = plt.cm.tab20.colors[:num_colors]
else:
    cmap = plt.cm.get_cmap('hsv', num_colors)
    color_palette = [cmap(i) for i in range(num_colors)]

plt.figure(figsize=(10, 10))
wedges, autotexts, _ = plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 10}, colors=color_palette)
    
# This needs to be changed according to the need of the experiments

positions = [
    (1.0, 1.0), 
    (1.0, 1.0), 
    (1.0, 0.9), 
    (1.1, 0.93), 
    (0.5, 1.0), 
    (1.0, 1.0), 
    (1.0, 1.0)
]

for autotext, position in zip(autotexts, positions):
    x, y = autotext.get_position()
    autotext.set_position((x * position[0], y * position[1])) 

plt.title('Proportion of Traffic by Third-Party IP Addresses')
plt.tight_layout()

output_file = os.path.join(output_dir, "pie_third_party_ip_traffic.png")
plt.savefig(output_file)
print(f"Pie chart saved to {output_file}")
plt.close()


### Pie Chart for third party traffic keeping outliers ###
third_party_data = data_copy[data_copy['Traffic Type'] == 'Third Party']
third_party_ip_traffic = third_party_data.groupby('Destination')['Length'].sum()
third_party_ip_traffic = third_party_ip_traffic.reset_index()
third_party_ip_traffic['ISP'] = third_party_ip_traffic['Destination'].map(ip_owner_df.set_index('IP Address')['ISP'])
third_party_ip_traffic['Service'] = third_party_ip_traffic['Destination'].map(ip_owner_df.set_index('IP Address')['Service'])

third_party_ip_traffic = third_party_ip_traffic.sort_values('Length', ascending=False)
# Define a threshold according to the need of the analysis
threshold = 0.019 * third_party_ip_traffic['Length'].sum() 
major_ips = third_party_ip_traffic[third_party_ip_traffic['Length'] >= threshold]
other_traffic = third_party_ip_traffic[third_party_ip_traffic['Length'] < threshold]['Length'].sum()

major_ips = major_ips.copy()
if other_traffic > 0:
    major_ips = pd.concat([major_ips, pd.DataFrame([{'Destination': 'Other', 'Length': other_traffic, 'ISP': '', 'Service': ''}])])


labels = [f"{row['Destination']}\n({row['ISP']}, {row['Service']})" if row['Service'] else f"{row['Destination']}\n({row['ISP']})" if row['Destination'] != "Other" else "Other" for _, row in major_ips.iterrows()]
sizes = major_ips['Length'].values

num_colors = len(major_ips)
if num_colors <= 20:
    color_palette = plt.cm.tab20.colors[:num_colors]
else:
    cmap = plt.cm.get_cmap('hsv', num_colors)
    color_palette = [cmap(i) for i in range(num_colors)]

plt.figure(figsize=(10, 10))
wedges, autotexts, _ = plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 10}, colors=color_palette)
    
# This needs to be changed according to the need of the experiments

positions = [
    (1.0, 1.0), 
    (1.0, 1.0), 
    (1.0, 1.0), 
    (1.0, 0.92), 
    (1.1, 0.95), 
    (-1.5, 1.03), 
    (1.0, 0.95), 
    (1.0, 0.93)
]

for autotext, position in zip(autotexts, positions):
    x, y = autotext.get_position()
    autotext.set_position((x * position[0], y * position[1])) 

plt.title('Proportion of Traffic by Third-Party IP Addresses')
plt.tight_layout()

output_file = os.path.join(output_dir, "pie_third_party_ip_keeping_outliers_traffic.png")
plt.savefig(output_file)
print(f"Pie chart saved to {output_file}")
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
plt.bar(x_positions, first_party_traffic_mean.values, bar_width, label="First Party Traffic")
plt.bar(x_positions, support_party_traffic_mean.values, bar_width, bottom=first_party_traffic_mean.values, label="Support Party Traffic", color="cyan")
plt.bar(x_positions, third_party_traffic_mean.values, bar_width, bottom=(first_party_traffic_mean.values + support_party_traffic_mean.values), label="Third-Party Traffic", color="orange")

plt.title("Traffic Volume: First vs Support vs Third Party Traffic")
plt.xlabel("Time Interval (minutes)")
plt.ylabel("Traffic Volume (bytes)")
plt.ylim(0, max_value * 1.1)
plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
plt.legend(loc="upper left")
plt.tight_layout()

output_file = os.path.join(output_dir, "bar_combined_different_party_traffic.png")
plt.savefig(output_file)
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
    	plt.axvline(x=1, color='magenta', linestyle='--', linewidth=1, label='Power on glasses and Open app')
    	plt.axvline(x=6, color='cyan', linestyle='--', linewidth=1, label='Import media')

    plt.title(f'{title}')
    plt.xlabel("Time Interval (minutes)")
    plt.ylabel("Traffic Volume (bytes)")
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    plt.legend(loc='upper right', fontsize='small', title='Experiments')
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"line_{file_suffix}.png")
    plt.savefig(output_file)
    print(f"Line plot for {traffic_type} saved to {output_file}")
    plt.close()

plot_traffic_by_type(
    traffic_type='First Party',
    file_suffix='first_party_traffic',
    title='Traffic Volume for First Parties by Experiment'
)

plot_traffic_by_type(
    traffic_type='Support Party',
    file_suffix='support_party_traffic',
    title='Traffic Volume for Support Parties by Experiment'
)

plot_traffic_by_type(
    traffic_type='Third Party',
    file_suffix='third_party_traffic',
    title='Traffic Volume for Third Parties by Experiment'
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
    plt.title(f'{title} (Log)')
    plt.xlabel("Time Interval (minutes)")
    plt.ylabel("Traffic Volume (bytes)")
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    plt.legend(loc='upper right', fontsize='small', title='Experiments')
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"line_log_{file_suffix}.png")
    plt.savefig(output_file)
    print(f"Line plot for {traffic_type} saved to {output_file}")
    plt.close()

plot_traffic_by_type(
    traffic_type='First Party',
    file_suffix='first_party_traffic',
    title='Traffic Volume for First Parties by Experiment'
)

plot_traffic_by_type(
    traffic_type='Support Party',
    file_suffix='support_party_traffic',
    title='Traffic Volume for Support Parties by Experiment'
)

plot_traffic_by_type(
    traffic_type='Third Party',
    file_suffix='third_party_traffic',
    title='Traffic Volume for Third Parties by Experiment'
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


### Pie Chart for combined trials ###
encrypted_traffic_count = data.loc[data['Is Encrypted'], 'Length'].sum()
unencrypted_traffic_count = data.loc[~data['Is Encrypted'], 'Length'].sum()

labels = ['Encrypted Traffic', 'Unencrypted Traffic']
sizes = [encrypted_traffic_count, unencrypted_traffic_count]

plt.figure(figsize=(8, 8))
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
plt.title('Proportion of Encrypted vs Unencrypted Traffic')
plt.tight_layout()

output_file = os.path.join(output_dir, "pie_combined_encrypted_vs_unencrypted_traffic.png")
plt.savefig(output_file)
print(f"Pie chart saved to {output_file}")
plt.close()


### Pie Chart for the types of parties ###
traffic_by_category_encryption = data.groupby(['Traffic Type', 'Is Encrypted'])['Length'].sum()

for category in ['First Party', 'Support Party', 'Third Party']:
    if category in traffic_by_category_encryption.index.get_level_values('Traffic Type'):
        encrypted_count = traffic_by_category_encryption.get((category, True), 0)
        unencrypted_count = traffic_by_category_encryption.get((category, False), 0)
        
        if encrypted_count == 0 and unencrypted_count == 0:
            print(f"Skipping {category} as it has no data.")
            continue

        labels = ['Encrypted', 'Unencrypted']
        sizes = [encrypted_count, unencrypted_count]

        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        plt.title(f'{category} Traffic: Encrypted vs Unencrypted')
        plt.tight_layout()

        output_file = os.path.join(output_dir, f"pie_{category.lower().replace(' ', '_')}_traffic.png")
        plt.savefig(output_file)
        print(f"Pie chart for {category} saved to {output_file}")
        plt.close()


### Pie Chart for each specific trial ###
traffic_distribution = data.groupby('Traffic Category')['Length'].sum()
labels = traffic_distribution.index.tolist()
sizes = traffic_distribution.values
plt.figure(figsize=(10, 10))

wedges, texts, autotexts = plt.pie(
    sizes,
    labels=None,
    autopct='%1.1f%%',
    startangle=140
)

# This needs to be changed according to the need of the experiments

positions = [
    (1.0, 1.0), 
    (1.25, 1.25), 
    (1.13, 1.15), 
    (1.1, 1.1), 
    (1.0, 0.98), 
    (1.0, 1.0)
]

for autotext, position in zip(autotexts, positions):
    x, y = autotext.get_position()
    autotext.set_position((x * position[0], y * position[1])) 

plt.legend(wedges, labels, loc="best", fontsize=10)

plt.title('Traffic Distribution by Party and Encryption Status')
plt.tight_layout()

output_file = os.path.join(output_dir, "pie_encrypted_vs_unencrypted_traffic.png")
plt.savefig(output_file)
print(f"Combined pie chart saved to {output_file}")
plt.close()



