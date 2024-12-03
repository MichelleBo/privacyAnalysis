import os
import pandas as pd
import requests
from ipwhois import IPWhois
from socket import gethostbyaddr, herror

# Known mapping of services/apps
known_services = {
    'instagram-p3-shv-01-zrh1.fbcdn.net': 'Facebook/Meta - Instagram',
    'whatsapp-cdn-shv-01-zrh1.fbcdn.net':  'Facebook/Meta - WhatsApp',
    'facebook.com': 'Facebook/Meta',
    'whatsapp': 'Facebook/Meta - WhatsApp',
    '1e100.net': 'Google',
    'googleusercontent.com': 'Google Cloud',
    'amazonaws.com': 'Amazon AWS'
}

# Function to resolve IP details
def get_ip_details(ip):
    """Fetch ISP, Service, and other details for an IP."""
    try:
        # Attempt reverse DNS lookup
        hostname = gethostbyaddr(ip)[0]
    except herror:
        hostname = "Unknown"

    try:
        # Use IPWhois to get ISP/Owner details
        obj = IPWhois(ip)
        results = obj.lookup_rdap()
        isp = results.get('network', {}).get('name', 'Unknown')  # Prefer 'network' field for ISP
        if isp == "Unknown":  # Fallback to ASN description if network name is missing
            isp = results.get('asn_description', 'Unknown')
        isp = isp.title()  # Format ISP name properly (e.g., 'Google LLC')
        owner = isp  # Use ISP as the owner if no better details are available
    except Exception:
        isp = "Unknown"
        owner = "Unknown"

    # Determine the service based on the hostname
    service = "Unknown"
    for key, value in known_services.items():
        if key in hostname:
            service = value
            break

    # Geolocation lookup (optional)
    url = f"http://ip-api.com/json/{ip}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            geo_data = response.json()
            return {
                'IP Address': ip,
                'ISP': isp,
                'Service': service,  # Use the determined service
                'Hostname': hostname,
                'Owner': owner,
                'Country': geo_data.get('country', 'Unknown'),
                'Region': geo_data.get('regionName', 'Unknown'),
                'City': geo_data.get('city', 'Unknown'),
                'Latitude': geo_data.get('lat', None),
                'Longitude': geo_data.get('lon', None)
            }
    except Exception:
        pass

    return {
        'IP Address': ip,
        'ISP': isp,
        'Service': service,
        'Hostname': hostname,
        'Owner': owner,
        'Country': 'Unknown',
        'Region': 'Unknown',
        'City': 'Unknown',
        'Latitude': None,
        'Longitude': None
    }
    
def update_ip_csv(ip_list, csv_path):
    """Resolve missing IPs and update the CSV."""
    # Load the existing CSV or create a new DataFrame
    if os.path.exists(csv_path):
        ip_owner_df = pd.read_csv(csv_path)
    else:
        ip_owner_df = pd.DataFrame(columns=['IP Address', 'Hostname', 'Owner', 'Service', 'Country', 'Region', 'City', 'Latitude', 'Longitude', 'ISP'])

    # Resolve new IPs
    new_ip_details = []
    for ip in ip_list:
        if ip not in ip_owner_df['IP Address'].values:
            print(f"Resolving IP: {ip}")
            details = get_ip_details(ip)
            new_ip_details.append(details)

    # Add new IP details to the DataFrame and save
    if new_ip_details:
        new_ip_details_df = pd.DataFrame(new_ip_details)
        ip_owner_df = pd.concat([ip_owner_df, new_ip_details_df], ignore_index=True)
        ip_owner_df.to_csv(csv_path, index=False)
        print(f"Updated IP details saved to {csv_path}")
    else:
        print("No new IPs to resolve.")

    return ip_owner_df
