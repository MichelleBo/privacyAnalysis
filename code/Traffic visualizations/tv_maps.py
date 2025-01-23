import os
import pandas as pd
import folium
import argparse
import plotly.express as px
import filters
import numpy as np

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
ip_owner_df = pd.read_csv(geo_file_path)

# Filter the IP owner file
unique_ips = pd.concat([data['Source'], data['Destination']]).unique()
unique_ips = [ip for ip in unique_ips if filters.is_valid_ip(ip)]
filtered_ip_owner_df = ip_owner_df[ip_owner_df['IP Address'].isin(unique_ips)]
filtered_ip_owner_df = filtered_ip_owner_df.dropna(subset=['Latitude', 'Longitude'])

filtered_ip_owner_df['Latitude'] += np.random.uniform(-0.01, 0.01, size=len(filtered_ip_owner_df))
filtered_ip_owner_df['Longitude'] += np.random.uniform(-0.01, 0.01, size=len(filtered_ip_owner_df))

# Check for traffic type
#filtered_ip_owner_df['Traffic Type'] = filtered_ip_owner_df['Service'].apply(filters.classify_traffic_by_service)

unique_dest_protocol = data.drop_duplicates(subset='Destination', keep='first').set_index('Destination')['Protocol']

filtered_ip_owner_df['Protocol'] = data['Destination'].map(unique_dest_protocol)
filtered_ip_owner_df['Protocol'].fillna('Unknown', inplace=True)
filtered_ip_owner_df['Traffic Type'] = filtered_ip_owner_df.apply(lambda row: filters.classify_traffic_by_service(row['Service'], row['Protocol']), axis=1)
filtered_ip_owner_df = filtered_ip_owner_df[filtered_ip_owner_df['Traffic Type'] != 'Private']


# Create the scatter geo plot
fig = px.scatter_geo(
    filtered_ip_owner_df,
    lat='Latitude',
    lon='Longitude',
    color='Traffic Type',
    title='Geolocation of Network Traffic by Traffic Type',
    hover_name='Traffic Type',
    hover_data={
        'IP Address': True,
        'ISP': True,
        'Service': True,
        'Country': True,
        'Region': True,
        'City': True
    }
) 

# Adjust the layout
fig.update_layout(
    geo=dict(
        showland=True, 
        showocean=True,  
        #landcolor="lightblue",
        oceancolor="lightblue",      
        showcoastlines=True,
        coastlinecolor="black",       
        showframe=False, 
        projection_type="natural earth",
        showcountries=True,   
        countrycolor="gray", 
        countrywidth=1,
        showlakes=True,   
        lakecolor="lightblue",    
    ),
    legend=dict(
        title="Traffic Type",
        x=0.87,  
        y=0.7,  
        xanchor='left',  
        yanchor='top',   
        bgcolor='rgba(255, 255, 255, 0.8)', 
        bordercolor='black', 
        borderwidth=1 
    )
)
fig.update_traces(marker=dict(size=17))

# Save the html file
output_dir = os.path.join(os.path.dirname(input_csv), "images")
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "geo_traffic_map.html")
fig.write_html(output_file)
print(f"Geo map saved to {output_file}")


