# This code is only used because in the beginning geolocation was not considered in the project

import os
import pandas as pd
import requests
from socket import gethostbyaddr, herror
from ipwhois import IPWhois

# Mapping services from known hostnames
known_services = {
    'instagram-p3-shv-01-zrh1.fbcdn.net': 'Facebook/Meta - Instagram',
    'whatsapp-cdn-shv-01-zrh1.fbcdn.net':  'Facebook/Meta - WhatsApp',
    'facebook.com': 'Facebook/Meta',
    'whatsapp': 'Facebook/Meta - WhatsApp',
    '1e100.net': 'Google',
    'googleusercontent.com': 'Google Cloud',
    'akamaitechnologies.com': 'Akamai CDN',
    'amazonaws.com': 'Amazon AWS'
}

# Mapping isps and owners from known alt. names
mapping_isp = {
    'Amazo-Cf': 'Amazon-CloudFront',
    'Amazon-Cf': 'Amazon-CloudFront',
    'Msft': 'Microsoft Azure',
    'Asepl-Sg': 'Alibaba-Sg',
    'Al-3': 'Alibaba-Sg',
    'C-212': 'Swiss Education and Research Network',
    'Thefa-3': 'Facebook, Inc.'
}

# Geolocation look up using ip-api.com
def get_geolocation(ip):
    url = f"http://ip-api.com/json/{ip}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return {
                'Country': data.get('country', 'Unknown'),
                'Region': data.get('regionName', 'Unknown'),
                'City': data.get('city', 'Unknown'),
                'Latitude': data.get('lat', None),
                'Longitude': data.get('lon', None),
                'ISP': data.get('isp', 'Unknown'),
            }
    except Exception as e:
        print(f"Error fetching geolocation for IP {ip}: {e}")
        
    return {
        'Country': 'Unknown',
        'Region': 'Unknown',
        'City': 'Unknown',
        'Latitude': None,
        'Longitude': None,
        'ISP': 'Unknown',
    }

# Resolve IP details
def get_ip_details(ip):
    try:
        hostname = gethostbyaddr(ip)[0]
    except herror:
        hostname = "Unknown"

    try:
        obj = IPWhois(ip)
        results = obj.lookup_rdap()
        owner = results.get('network', {}).get('name', 'Unknown')
    except Exception:
        owner = 'Unknown'

    service = 'Unknown'
    for key, value in known_services.items():
        if key in hostname:
            service = value
            break

    return hostname, owner, service

# Load the existing IP owners CSV file that did not include geo location
file_path = os.path.expanduser("~/ip_owners.csv")

if not os.path.exists(file_path):
    print(f"Error: {file_path} does not exist.")
    exit()

ip_owners = pd.read_csv(file_path)


enhanced_ip_details = []

for _, row in ip_owners.iterrows():
    ip = row['IP Address']
    print(f"Processing IP: {ip}")
    
    hostname, owner, service = get_ip_details(ip)    
    geo = get_geolocation(ip)
    
    enhanced_ip_details.append({
        'IP Address': ip,
        'Hostname': hostname,
        'Owner': owner,
        'Service': service,
        'Country': geo['Country'],
        'Region': geo['Region'],
        'City': geo['City'],
        'Latitude': geo['Latitude'],
        'Longitude': geo['Longitude'],
        'ISP': geo['ISP'],
    })

# Convert to a DataFrame and save to the CSV file
enhanced_ip_details_df = pd.DataFrame(enhanced_ip_details)
enhanced_ip_details_df.to_csv('ip_owners_with_geo.csv', index=False)

print(f"Enhanced IP-to-name mapping with geolocation saved")

