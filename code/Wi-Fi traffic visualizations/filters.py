import pandas as pd
import ipaddress

relevant_criteria = {
    "IP Addresses": ["192.168.1.141", "192.168.1.100"],  # relevant IPs
    "ISPs": ["Facebook, Inc.", "Thefa-3"],  # relevant ISPs
    "Services": ["Facebook/Meta", "Instagram", "WhatsApp"],  # relevant service names
}

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

# Checks for relevant traffic criteria (Meta View and Ray-Ban glasses)
def is_relevant_traffic(ip, isp, service):
    is_relevant_ip = ip.isin(relevant_criteria["IP Addresses"])
    is_relevant_isp = isp.isin(relevant_criteria["ISPs"])
    is_relevant_service = service.str.contains('|'.join(relevant_criteria["Services"]), na=False)
    return is_relevant_ip | is_relevant_isp | is_relevant_service


