import os
import pandas as pd
import matplotlib.pyplot as plt
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

# Load IP owners mapping csv file
geo_dir = os.path.dirname(os.path.abspath(__file__))
geo_file_path = os.path.join(geo_dir, 'ip_owners_with_geo.csv')

# Resolve missing IPs and update the CSV
unique_ips = pd.concat([data['Source'], data['Destination']]).unique()
unique_ips = [ip for ip in unique_ips if filters.is_valid_ip(ip)]
ip_owner_df = get_ip.update_ip_csv(unique_ips, geo_file_path)

# Count occurrences of all IP addresses
ip_frequencies = data['Destination'].value_counts()

# Remove the top 5 highest frequency IP addresses
top_5_ips = ip_frequencies.nlargest(5).index
ip_frequencies = ip_frequencies.drop(top_5_ips)

# Map IPs to ISP + Service for visualization
ip_labels = []
for ip in ip_frequencies.index:
    ip_details = ip_owner_df[ip_owner_df['IP Address'] == ip]
    if not ip_details.empty:
        isp = ip_details.iloc[0]['ISP']
        service = ip_details.iloc[0]['Service']
        # print(f"{ip}, {isp}, {service}")
        if service != "Unknown":
            label = f"{ip} ({isp}, {service})"
        else:
            label = f"{ip} ({isp})"
        ip_labels.append(label)
    else:
        ip_labels.append(f"{ip} (Unknown)")
        

# Create a DataFrame for plotting
ip_plot_df = pd.DataFrame({'IP Address': ip_labels, 'Frequency': ip_frequencies.values})

# Plot
plt.figure(figsize=(12, 8))
ip_plot_df.set_index('IP Address')['Frequency'].plot(kind='barh')
plt.title('Traffic Frequency')
plt.xlabel('Frequency')
plt.ylabel('IP Address (ISP, Service)')
plt.tight_layout()

# Save the image
output_dir = os.path.join(os.path.dirname(input_csv), "image")
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "tv_freq_all_traffic_minus.png")
plt.savefig(output_file)
print("Plot saved to ", output_dir, "/tv_freq_all_traffic_minus.png")

