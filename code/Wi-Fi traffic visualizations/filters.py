import pandas as pd
import ipaddress

# Check if an IP address is valid.
def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

# Checks for rows with Private Owner and Hostname marked as Private
def is_private_ip(ip, ip_owner_df):
    private_ips = ip_owner_df[
        (ip_owner_df['Owner'] == 'Private') & (ip_owner_df['Hostname'] == 'Private')
    ]['IP Address']
    return ip in private_ips.values

# Checks for ACK packets
def is_ack_packet(row):
    if isinstance(row['Info'], str):
        if row['Protocol'] == 'TCP' and 'ACK' in row['Info']:
            return True
    return False

# Checks for retransmissions and duplicates
def is_redundant_packet(row):
    if isinstance(row['Info'], str):
        if "Retransmission" in row['Info'] or "Duplicate" in row['Info']:
            return True
    return False

# Checks for broadcast or multicast packets
def is_broadcast_or_multicast(ip):
    if ip.startswith("255.") or ip.startswith("224.") or ip.startswith("239."):
        return True
    return False

# Checks for non-application protocols
def is_excluded_protocol(protocol):
    excluded_protocols = ['ARP', 'ICMP']
    return protocol in excluded_protocols

