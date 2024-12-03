import os
import pandas as pd
import requests
from socket import gethostbyaddr, herror
from ipwhois import IPWhois

# Known mapping of services/apps (you can expand this list)
known_services = {
    '1e100.net': 'Google (e.g., YouTube, Gmail)',
    'fbcdn.net': 'Facebook/Meta (e.g., Instagram, WhatsApp)',
    'akamaitechnologies.com': 'Akamai CDN',
    'amazonaws.com': 'Amazon AWS',
    # Add more known domains or services as needed
}

# Geolocation function using ip-api.com
def get_geolocation(ip):
    """Fetch precise geographical details for an IP address using ip-api.com."""
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

# Reverse DNS and WHOIS lookup
def get_ip_details(ip):
    """Fetches ownership, service, and location details for an IP address."""
    try:
        # Step 1: Attempt reverse DNS lookup
        hostname = gethostbyaddr(ip)[0]
    except herror:
        hostname = "Unknown"

    # Step 2: Determine the owner using WHOIS
    try:
        obj = IPWhois(ip)
        results = obj.lookup_rdap()
        owner = results.get('network', {}).get('name', 'Unknown')
    except Exception:
        owner = 'Unknown'

    # Step 3: Map hostname to known services/apps
    service = 'Unknown'
    for key, value in known_services.items():
        if key in hostname:
            service = value
            break

    return hostname, owner, service

# Load the existing IP owners CSV file
file_path = os.path.expanduser("~/ip_owners.csv")

if not os.path.exists(file_path):
    print(f"Error: {file_path} does not exist.")
    exit()

ip_owners = pd.read_csv(file_path)

# Prepare a new list to store enhanced details
enhanced_ip_details = []

for _, row in ip_owners.iterrows():
    ip = row['IP Address']
    print(f"Processing IP: {ip}")
    
    # Fetch hostname, owner, and service details
    hostname, owner, service = get_ip_details(ip)
    
    # Fetch geolocation details
    geo = get_geolocation(ip)
    
    # Combine all details
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

# Convert to a DataFrame and save to a new CSV file
enhanced_ip_details_df = pd.DataFrame(enhanced_ip_details)
enhanced_ip_details_df.to_csv('ip_owners_with_geo.csv', index=False)

print(f"Enhanced IP-to-name mapping with geolocation saved")

