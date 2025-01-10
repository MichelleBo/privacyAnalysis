import os
import pandas as pd
import requests
from ipwhois import IPWhois
from socket import gethostbyaddr, herror

# Mapping services from known hostnames
known_services = {
    'instagram-p3-shv-01-zrh1.fbcdn.net': 'Facebook/Meta-Instagram',
    'whatsapp-cdn-shv-01-zrh1.fbcdn.net':  'Facebook/Meta-WhatsApp',
    'facebook.com': 'Facebook/Meta',
    'whatsapp': 'Facebook/Meta-WhatsApp',
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
    'Thefa-3': 'Facebook, Inc.',
    'Google-2': 'Google',
    'Googl-2': 'Google',
    'Google Cloud': 'Google-Cloud',
}

# Resolve IP details
def get_ip_details(ip):
    # Get hostname for ip address
    try:
        hostname = gethostbyaddr(ip)[0]
    except herror:
        hostname = "Unknown"

    # Get isp and owner for ip address
    try:
        obj = IPWhois(ip)
        results = obj.lookup_rdap()
        isp = results.get('network', {}).get('name', 'Unknown')  
        if isp == "Unknown":  
            isp = results.get('asn_description', 'Unknown')
        isp = isp.title()  
        owner = isp 
    except Exception:
        isp = "Unknown"
        owner = "Unknown"

    # The mappings
    service = "Unknown"
    for key, value in known_services.items():
        if key in hostname:
            service = value
            break
            
    if isp in mapping_isp:
        owner = mapping_isp[isp]
        isp = mapping_isp[isp]

    # Geolocation lookup using ip-api.com
    url = f"http://ip-api.com/json/{ip}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            geo_data = response.json()
            return {
                'IP Address': ip,
                'ISP': isp,
                'Service': service,
                'Hostname': hostname,
                'Owner': owner,
                'Country': geo_data.get('country', 'Unknown'),
                'Region': geo_data.get('regionName', 'Unknown'),
                'City': geo_data.get('city', 'Unknown'),
                'Latitude': geo_data.get('lat', None),
                'Longitude': geo_data.get('lon', None)
            }
    except Exception as e:
        print(f"Error fetching geolocation for IP {ip}: {e}")

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
 
 # Resolve missing IPs and update the CSV  
def update_ip_csv(ip_list, csv_path):
  
    if os.path.exists(csv_path):
        ip_owner_df = pd.read_csv(csv_path)
    else:
        ip_owner_df = pd.DataFrame(columns=['IP Address', 'Hostname', 'Owner', 'Service', 'Country', 'Region', 'City', 'Latitude', 'Longitude', 'ISP'])

    new_ip_details = []
    for ip in ip_list:
        if ip not in ip_owner_df['IP Address'].values:
            print(f"Resolving IP: {ip}")
            details = get_ip_details(ip)
            new_ip_details.append(details)

    if new_ip_details:
        new_ip_details_df = pd.DataFrame(new_ip_details)
        ip_owner_df = pd.concat([ip_owner_df, new_ip_details_df], ignore_index=True)
        ip_owner_df.to_csv(csv_path, index=False)
        print(f"Updated IP details saved to {csv_path}")
    else:
        print("No new IPs to resolve.")

    return ip_owner_df
    
    
    
