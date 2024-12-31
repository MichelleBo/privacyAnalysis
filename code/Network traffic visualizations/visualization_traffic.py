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
ip_owner_df['Traffic Type'] = ip_owner_df['Service'].apply(filters.classify_traffic_by_service)

data['Traffic Type'] = data['Destination'].map(ip_owner_df.set_index('IP Address')['Traffic Type'])

data['First Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'First Party', 0).astype(float)
data['Support Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'Support Party', 0).astype(float)
data['Third Party Traffic'] = data['Length'].where(data['Traffic Type'] == 'Third Party', 0).astype(float)

# Group by time intervals
data['Time Interval'] = (data['Time'] // 30).astype(int)

traffic_by_experiment = data.groupby(['Time Interval', 'ExperimentTrial', 'Traffic Type'])['Length'].sum().unstack(level='Traffic Type', fill_value=0)

time_intervals = traffic_by_experiment.index.get_level_values('Time Interval').unique()

"""
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
"""

### Pie Chart for third party traffic ###
third_party_data = data[data['Traffic Type'] == 'Third Party']
third_party_ip_traffic = third_party_data.groupby('Destination')['Length'].sum()
third_party_ip_traffic = third_party_ip_traffic.reset_index()
third_party_ip_traffic['ISP'] = third_party_ip_traffic['Destination'].map(ip_owner_df.set_index('IP Address')['ISP'])

# Sort and group smaller contributions into "Other"
third_party_ip_traffic = third_party_ip_traffic.sort_values('Length', ascending=False)
threshold = 0.019 * third_party_ip_traffic['Length'].sum()  # Define a threshold (2% of total traffic)
major_ips = third_party_ip_traffic[third_party_ip_traffic['Length'] >= threshold]
other_traffic = third_party_ip_traffic[third_party_ip_traffic['Length'] < threshold]['Length'].sum()

# Combine the major IPs with "Other"
major_ips = major_ips.copy()
if other_traffic > 0:
    major_ips = pd.concat([major_ips, pd.DataFrame([{'Destination': 'Other', 'Length': other_traffic, 'ISP': ''}])])


# Get the labels and sizes for the pie chart
labels = [f"{row['Destination']}\n({row['ISP']})" if row['Destination'] != "Other" else "Other" for _, row in major_ips.iterrows()]
sizes = major_ips['Length'].values

# Generate the pie chart
plt.figure(figsize=(10, 10))
wedges, autotexts, _ = plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, textprops={'fontsize': 10})
    
# This needs to be changed according to the need of the experiments
positions = [
    (1.0, 1.0), 
    (1.0, 1.0), 
    (1.0, 1.0), 
    (1.0, 1.0), 
    (0.6, 1.0), 
    (-0.3, 1.0), 
    (0.8, 0.98), 
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


### Bar Plot for combined trials mean ###
first_party_traffic_mean = traffic_by_experiment['First Party'].groupby(level='Time Interval').mean()
support_party_traffic_mean = traffic_by_experiment['Support Party'].groupby(level='Time Interval').mean()
third_party_traffic_mean = traffic_by_experiment['Third Party'].groupby(level='Time Interval').mean()

bar_width = 0.6
x_positions = np.arange(len(time_intervals))

plt.figure(figsize=(12, 8))
plt.bar(x_positions, first_party_traffic_mean.values, bar_width, label="First Party Traffic")
plt.bar(x_positions, support_party_traffic_mean.values, bar_width, bottom=first_party_traffic_mean.values, label="Support Party Traffic", color="cyan")
plt.bar(x_positions, third_party_traffic_mean.values, bar_width, bottom=(first_party_traffic_mean.values + support_party_traffic_mean.values), label="Third-Party Traffic", color="orange")

plt.title("Traffic Volume: First vs Support vs Third Party Traffic")
plt.xlabel("Time Interval (minutes)")
plt.ylabel("Traffic Volume (bytes)")
plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
plt.legend(loc="upper left")
plt.tight_layout()

output_file = os.path.join(output_dir, "bar_combined_different_party_traffic.png")
plt.savefig(output_file)
print(f"Bar plot saved to {output_file}")
plt.close()


### Line Plot for the types of parties ###
experiments = traffic_by_experiment.index.get_level_values('ExperimentTrial').unique()
color_map = {experiment: color for experiment, color in zip(experiments, cm.tab10.colors)}

def plot_traffic_by_type(traffic_type, file_suffix, title):
    plt.figure(figsize=(12, 8))
    for experiment in experiments:
        traffic = traffic_by_experiment.loc[(slice(None), experiment), traffic_type]
        time_intervals = traffic.index.get_level_values('Time Interval')
        plt.plot(time_intervals, traffic.values, label=f"{experiment}", color=color_map[experiment], linewidth=2, alpha=0.7)
    plt.title(f'{title}: {traffic_type} Traffic')
    plt.xlabel('Time Interval (minutes)')
    plt.ylabel('Traffic Volume (bytes)')
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    plt.legend(loc='upper left', fontsize='small', title='Experiments')
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"{file_suffix}.png")
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
    support_party_traffic = traffic_for_trial['Support Party']
    third_party_traffic = traffic_for_trial['Third Party']

    bar_width = 0.6
    x_positions = np.arange(len(time_intervals))

    plt.figure(figsize=(12, 8))
    plt.bar(x_positions, first_party_traffic.values, bar_width, label="First Party Traffic")
    plt.bar(x_positions, support_party_traffic.values, bar_width, bottom=first_party_traffic.values, label="Support Party Traffic", color="cyan")
    plt.bar(x_positions, third_party_traffic.values, bar_width, bottom=(first_party_traffic.values + support_party_traffic.values), label="Third-Party Traffic", color="orange")

    plt.title(f"Traffic Volume for {experiment_trial}: First vs Support vs Third Party Traffic")
    plt.xlabel("Time Interval (minutes)")
    plt.ylabel("Traffic Volume (bytes)")
    plt.xticks(x_positions, labels=[f"{x * 0.5:.1f}" for x in x_positions], rotation=45)
    plt.legend(loc="upper left")
    plt.tight_layout()

    output_file = os.path.join(output_dir, f"bar_{experiment_trial.replace(' ', '_')}_party_traffic.png")
    plt.savefig(output_file)
    print(f"Bar plot saved to {output_file}")
    plt.close()
"""

"""
#####################     Shows traffic volume for encrypted data     #####################
# Add column for encryption
data['Is Encrypted'] = data['Protocol'].apply(filters.is_encrypted_traffic)

data['Encrypted Traffic'] = data['Length'].where(data['Is Encrypted'], 0).astype(float)
data['Plain-Text Traffic'] = data['Length'].where(~data['Is Encrypted'], 0).astype(float)

data['Traffic Category'] = data.apply(lambda row: f"{row['Traffic Type']} - Encrypted" if row['Is Encrypted'] else f"{row['Traffic Type']} - Plain-Text", axis=1)

traffic_by_category = data.groupby(['Time Interval', 'Traffic Category'])['Length'].sum().unstack(fill_value=0)

### Bar Plot for combined trials ###
bar_width = 0.6
x_positions = np.arange(len(traffic_by_category.index))

plt.figure(figsize=(12, 8))
for i, category in enumerate(traffic_by_category.columns):
    plt.bar(x_positions, traffic_by_category[category].values, bottom=traffic_by_category.iloc[:, :i].sum(axis=1).values, label=category)

plt.title("Traffic Volume: Encrypted vs Plain-Text for different Parties")
plt.xlabel("Time Interval (minutes)")
plt.ylabel("Traffic Volume (bytes)")
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
        encrypted_count = traffic_by_category_encryption.loc[(category, True)]
        unencrypted_count = traffic_by_category_encryption.loc[(category, False)]

        labels = ['Encrypted', 'Unencrypted']
        sizes = [encrypted_count, unencrypted_count]

        plt.figure(figsize=(8, 8))
        plt.pie(sizes, autopct='%1.1f%%', startangle=140)
        plt.title(f'{category} Traffic: Encrypted vs Unencrypted')
        plt.tight_layout()

        output_file = os.path.join(output_dir, f"pie_{category.replace(' ', '_')}_traffic.png")
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
    (1.0, 1.0), 
    (1.2, 1.3), 
    (1.15, 1.2), 
    (1.07, 1.1), 
    (1.0, 1.0)
]

for autotext, position in zip(autotexts, positions):
    x, y = autotext.get_position()
    autotext.set_position((x * position[0], y * position[1])) 

plt.legend(wedges, labels, loc="best", bbox_to_anchor=(1, 0.5), fontsize=10)

plt.title('Traffic Distribution by Party and Encryption Status')
plt.tight_layout()

output_file = os.path.join(output_dir, "pie_encrypted_vs_unencrypted_traffic.png")
plt.savefig(output_file)
print(f"Combined pie chart saved to {output_file}")
plt.close()




