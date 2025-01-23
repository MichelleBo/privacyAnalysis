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

# Exclude redundant traffic
data['Is Redundant'] = data.apply(lambda row: filters.is_redundant_traffic(row['Protocol'], row['Info']), axis=1)
data = data[~data['Is Redundant']]

    
output_dir = os.path.join(os.path.dirname(input_csv), "images")
os.makedirs(output_dir, exist_ok=True) 



#####################     Shows traffic volume for the types of parties     #####################
# Classify traffic for the analysis
ip_owner_df['Traffic Type'] = ip_owner_df['Service'].apply(filters.classify_traffic_by_service)

data['Traffic Type'] = data['Destination'].map(ip_owner_df.set_index('IP Address')['Traffic Type'])

data['First Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'First Party', 0).astype(float)
data['Support Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'Support Party', 0).astype(float)
data['Third Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'Third Party', 0).astype(float)

# Group by time intervals
data['Time Interval'] = (data['Time'] // 30).astype(int)


### Line Plot for ip addresses for each party type ###
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
        ip_labels.append(f"{ip}")

for traffic_type in ['First Party', 'Support Party', 'Third Party']:
    plt.figure(figsize=(12, 8))
    
    traffic_data = data[data['Traffic Type'] == traffic_type]
    if traffic_data.empty:
        print(f"No data available for {traffic_type}. Skipping...")
        continue
        
    packet_counts = traffic_data.groupby(['Time Interval', 'Destination']).size().unstack(fill_value=0)
    ip_addresses = packet_counts.columns

    plt.figure(figsize=(12, 8))
    color_map = {ip: color for ip, color in zip(packet_counts.columns, cm.rainbow(np.linspace(0, 1, len(packet_counts.columns))))}

    for ip in ip_addresses:
        ip_details = ip_owner_df[ip_owner_df['IP Address'] == ip]
        total_packets = packet_counts[ip].sum()
        if not ip_details.empty:
            isp = ip_details.iloc[0]['ISP']
            service = ip_details.iloc[0]['Service']
            if service != "Unknown":
                label = f"{ip} ({isp}, {service}) - {total_packets} packets"
            else:
                label = f"{ip} ({isp}) - {total_packets} packets"
        else:
            label = f"{ip} - {total_packets} packets"
        plt.plot(packet_counts.index, packet_counts[ip], label=label, color=color_map[ip], linewidth=2, alpha=0.7)


    plt.title('Timeline of All Traffic')
    plt.xlabel('Time (seconds)')
    plt.ylabel('IP Address')
    plt.xticks(rotation=45)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title='IP Addresses', fontsize='small')
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"line_all_{traffic_type.lower()}_traffic.png")
    plt.savefig(output_file)
    print(f"Line plot saved to {output_file}")
    plt.close()
    

### Pie Chart for experiment ###
first_party_traffic_count = data['First Party Traffic'].sum()
support_party_traffic_count = data['Support Party Traffic'].sum()
third_party_traffic_count = data['Third Party Traffic'].sum()

labels = ['First Party Traffic', 'Support Party Traffic', 'Third Party Traffic']
sizes = [first_party_traffic_count, support_party_traffic_count, third_party_traffic_count]

plt.figure(figsize=(8, 8))
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
plt.title('Proportion of Encrypted vs Unencrypted Filtered Traffic')
plt.tight_layout()

output_file = os.path.join(output_dir, "filtered_pie_encrypted_vs_unencrypted_pie_chart.png")
plt.savefig(output_file)
print(f"Pie chart saved to {output_file}")
plt.close()


### Pie Chart for third party traffic ###
third_party_data = data[data['Traffic Type'] == 'Third Party']
third_party_ip_traffic = third_party_data.groupby('Destination')['Length'].sum()
third_party_ip_traffic = third_party_ip_traffic.reset_index()
third_party_ip_traffic['ISP'] = third_party_ip_traffic['Destination'].map(ip_owner_df.set_index('IP Address')['ISP'])

third_party_ip_traffic = third_party_ip_traffic.sort_values('Length', ascending=False)
threshold = 0.019 * third_party_ip_traffic['Length'].sum()  # Define a threshold (2% of total traffic)
major_ips = third_party_ip_traffic[third_party_ip_traffic['Length'] >= threshold]
other_traffic = third_party_ip_traffic[third_party_ip_traffic['Length'] < threshold]['Length'].sum()

major_ips = major_ips.copy()
if other_traffic > 0:
    major_ips = pd.concat([major_ips, pd.DataFrame([{'Destination': 'Other', 'Length': other_traffic, 'ISP': ''}])])


labels = [f"{row['Destination']}\n({row['ISP']})" if row['Destination'] != "Other" else "Other" for _, row in major_ips.iterrows()]
sizes = major_ips['Length'].values

plt.figure(figsize=(10, 10))
wedges, autotexts, _ = plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 10})
    
# This needs to be changed according to the need of the experiments
positions = [
    (1.0, 1.0), 
    (1.0, 1.0), 
    (1.0, 1.0), 
    (1.0, 1.0), 
    (-1.4, 1.0), 
    (0.8, 1.0), 
    (0.9, 1.0), 
    (1.0, 1.0)
]

for autotext, position in zip(autotexts, positions):
    x, y = autotext.get_position()
    autotext.set_position((x * position[0], y * position[1])) 

plt.title('Proportion of Traffic by Third-Party IP Addresses')
plt.tight_layout()

output_file = os.path.join(output_dir, "filtered_pie_third_party_ip_traffic.png")
plt.savefig(output_file)
print(f"Pie chart saved to {output_file}")
plt.close()


### Line Plot for the types of parties ###

def plot_traffic_by_type(traffic_type, file_suffix, title):

    traffic_data = data[data['Traffic Type'] == traffic_type]
    if traffic_data.empty:
        print(f"No data available for {traffic_type}. Skipping...")
        return
    
    traffic_by_interval = traffic_data.groupby('Time Interval')['Length'].sum()
    x_positions = traffic_by_interval.index

    plt.figure(figsize=(12, 8))
    plt.plot(x_positions, traffic_by_interval.values, label=traffic_type, linewidth=2, alpha=0.7)
    	
    # Add for solo vertical lines
    # specific_time = 30
    # plt.axvline(x=specific_time, color='red', linestyle='--', linewidth=1, label=f'Event @ {specific_time}s')

    plt.title(f'{title}: {traffic_type} Traffic')
    plt.xlabel('Time Interval (minutes)')
    plt.ylabel('Traffic Volume (bytes)')
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    plt.legend(loc='upper left', fontsize='small')
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"filtered_line_{file_suffix}.png")
    plt.savefig(output_file)
    print(f"Line plot for {traffic_type} saved to {output_file}")
    plt.close()

plot_traffic_by_type(
    traffic_type='First Party',
    file_suffix='first_party_traffic',
    title='Filtered Traffic Volume for First Parties by Experiment'
)

plot_traffic_by_type(
    traffic_type='Support Party',
    file_suffix='support_party_traffic',
    title='Filtered Traffic Volume for Support Parties by Experiment'
)

plot_traffic_by_type(
    traffic_type='Third Party',
    file_suffix='third_party_traffic',
    title='Filtered Traffic Volume for Third Parties by Experiment'
)


# Line Plot for the IP address in third-party traffic (Additional)
def plot_traffic_by_ip(traffic_type, file_suffix, title):
    plt.figure(figsize=(12, 8))
    
    third_party_data = data[data['Traffic Type'] == 'Third Party']
    traffic_by_ip = third_party_data.groupby(['Time Interval', 'Destination'])['Length'].sum().unstack(fill_value=0)

    ip_addresses = traffic_by_ip.columns
    
    ip_labels = {}
    for ip in ip_owner_df['IP Address']:
        ip_details = ip_owner_df[ip_owner_df['IP Address'] == ip]
        if not ip_details.empty:
            isp = ip_details.iloc[0]['ISP']
            service = ip_details.iloc[0]['Service']
            if service != "Unknown":
                ip_labels[ip] = f"{ip} ({isp}, {service})"
            else:
                ip_labels[ip] = f"{ip} ({isp})"
        else:
            ip_labels[ip] = f"{ip}"
            

    for ip in (ip_addresses):
        traffic = traffic_by_ip[ip]
        label = ip_labels.get(ip, ip)
        plt.plot(
            traffic.index,
            traffic.values,
            label=label,
            linewidth=2,
            alpha=0.7
        )

    # Add for solo vertical lines
    # specific_time = 30
    # plt.axvline(x=specific_time, color='red', linestyle='--', linewidth=1, label=f'Event @ {specific_time}s')
    
    plt.title(f'{title}: Traffic Volume by IP Address')
    plt.xlabel('Time Interval (minutes)')
    plt.ylabel('Traffic Volume (bytes)')
    plt.xticks(traffic_by_ip.index, labels=[f"{x * 0.5:.1f}" for x in traffic_by_ip.index], rotation=45)
    plt.legend(loc='upper left', fontsize='small', title='IP Addresses', bbox_to_anchor=(1, 1))
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"filtered_line_{file_suffix}.png")
    plt.savefig(output_file)
    print(f"Line plot for {traffic_type} saved to {output_file}")
    plt.close()

plot_traffic_by_ip(
    traffic_type='Third Party',
    file_suffix='third_party_ip_traffic',
    title='Traffic Volume for Third-Party Traffic by IP Address'
)


### Bar Plot for experiment ###
first_party_traffic = data.groupby('Time Interval')['First Party Traffic'].sum()
support_party_traffic = data.groupby('Time Interval')['Support Party Traffic'].sum()
third_party_traffic = data.groupby('Time Interval')['Third Party Traffic'].sum()

bar_width = 0.6
time_intervals = first_party_traffic.index.get_level_values('Time Interval').unique()
x_positions = np.arange(len(time_intervals))

plt.figure(figsize=(12, 8))
plt.bar(x_positions, first_party_traffic.values, bar_width, label="First Party Traffic")
plt.bar(x_positions, support_party_traffic.values, bar_width, bottom=first_party_traffic.values, label="Support Party Traffic", color="cyan")
plt.bar(x_positions, third_party_traffic.values, bar_width, bottom=(first_party_traffic.values + support_party_traffic.values), label="Third Party Traffic", color="orange")


plt.title("Filtered Traffic Volume: First vs Support vs Third Party Traffic")
plt.xlabel("Time Interval (minutes)")
plt.ylabel("Traffic Volume (bytes)")
plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
plt.legend(loc="upper left")
plt.tight_layout()
 
output_file = os.path.join(output_dir, "filtered_bar_different_party_traffic.png")
plt.savefig(output_file)
print(f"Bar plot saved to {output_file}")
plt.close()


#####################     Shows traffic volume for encrypted data     #####################
# Add column for encryption
data['Is Encrypted'] = data['Protocol'].apply(filters.is_encrypted_traffic)

data['Encrypted Traffic'] = data['Length'].where(data['Is Encrypted'], 0).astype(float)
data['Plain-Text Traffic'] = data['Length'].where(~data['Is Encrypted'], 0).astype(float)

data['Traffic Category'] = data.apply(lambda row: f"{row['Traffic Type']} - Encrypted" if row['Is Encrypted'] else f"{row['Traffic Type']} - Plain-Text", axis=1)

traffic_by_category = data.groupby(['Time Interval', 'Traffic Category'])['Length'].sum().unstack(fill_value=0)

### Bar Plot for experiment ###
bar_width = 0.6
x_positions = np.arange(len(traffic_by_category.index))

plt.figure(figsize=(12, 8))
for i, category in enumerate(traffic_by_category.columns):
    plt.bar(x_positions, traffic_by_category[category].values, bottom=traffic_by_category.iloc[:, :i].sum(axis=1).values, label=category)

plt.title("Filtered Traffic Volume: Encrypted vs Plain-Text for different Parties")
plt.xlabel("Time Interval (minutes)")
plt.ylabel("Traffic Volume (bytes)")
plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
plt.legend(loc="upper left")
plt.tight_layout()

output_file = os.path.join(output_dir, "filtered_bar_combined_encrypted_vs_plain_text_traffic.png")
plt.savefig(output_file)
print(f"Bar plot saved to {output_file}")
plt.close()


### Pie Chart for experiment ###
encrypted_traffic_count = data.loc[data['Is Encrypted'], 'Length'].sum()
unencrypted_traffic_count = data.loc[~data['Is Encrypted'], 'Length'].sum()

labels = ['Encrypted Traffic', 'Unencrypted Traffic']
sizes = [encrypted_traffic_count, unencrypted_traffic_count]

plt.figure(figsize=(8, 8))
plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
plt.title('Proportion of Encrypted vs Unencrypted Filtered Traffic')
plt.tight_layout()

output_file = os.path.join(output_dir, "filtered_pie_combined_encrypted_vs_unencrypted_traffic.png")
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
        plt.pie(sizes, autopct='%1.1f%%', startangle=140)
        plt.title(f'Filtered {category} Traffic: Encrypted vs Unencrypted')
        plt.tight_layout()

        output_file = os.path.join(output_dir, f"filtered_pie_{category.replace(' ', '_')}_traffic.png")
        plt.savefig(output_file)
        print(f"Pie chart for {category} saved to {output_file}")
        plt.close()



