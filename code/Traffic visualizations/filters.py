import pandas as pd
import ipaddress

relevant_criteria = {
    "IP Addresses": ["192.168.1.141", "192.168.1.100"],  
    "ISPs": ["Facebook, Inc.", "Thefa-3"], 
    "Services": ["Facebook/Meta", "Instagram", "WhatsApp"]
}

criteria = {
    "First Party": ["Facebook/Meta", "Thefa-3", "Facebook, Inc.", "Facebook"], 
    "Support Party": ["Facebook/Meta-Instagram", "Facebook/Meta-WhatsApp"]
}


# Check if an IP address is valid - Exclude link-local, multicast, and unspecified IPv6 addresses
def is_valid_ip(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        if isinstance(ip_obj, ipaddress.IPv6Address):
            if ip_obj.is_link_local or ip_obj.is_multicast or ip_obj.is_unspecified:
                return False
        return True
    except ValueError:
        return False

"""
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
    excluded_protocols = ['ICMP']
    return any(proc in protocol.upper() for proc in excluded_protocols)


# Checks for relevant traffic criteria (Meta View and Ray-Ban glasses)
def is_relevant_traffic(ip, isp, service):
    is_relevant_ip = ip.isin(relevant_criteria["IP Addresses"])
    is_relevant_isp = isp.isin(relevant_criteria["ISPs"])
    is_relevant_service = service.str.contains('|'.join(relevant_criteria["Services"]), na=False)
    return is_relevant_ip | is_relevant_isp | is_relevant_service


# Checks if the traffic is encrypted based on protocol
def is_encrypted_traffic(protocol):
    encrypted_protocols = {'HTTPS', 'TLS', 'SSL', 'QUIC', 'SSH', 'IPSEC', 'SFTP', 'SMTPS', 'IMAPS', 'POP3S', 'TCP', 'UDP'}
    return any(enc in protocol.upper() for enc in encrypted_protocols)
    
# Checks if the traffic is TCP
def is_tcp_traffic(protocol):
    protocols = {'TCP'}
    return any(enc in protocol.upper() for enc in protocols)

# Checks if the traffic is UDP
def is_udp_traffic(protocol):
    protocols = {'UDP'}
    return any(enc in protocol.upper() for enc in protocols)

# Checks whether a given protocol is redundant based on research goals 
def is_redundant_traffic(protocol, info):
    redundant_protocols = {
        'MDNS',  # Multicast DNS, used for local name resolution - local device discovery
        'SSDP',  # Simple Service Discovery Protocol, used for service discovery - local service discovery
        'ARP',   # Address Resolution Protocol, used to resolve MAC addresses - local network communication
        'ICMPv6',  # Internet Control Message Protocol for IPv6, diagnostic or admin traffic
        'DHCP'   # Dynamic Host Configuration Protocol, used for IP address assignment to devices - network configuration
    }
    
    redundant_keywords = {
    'Window Update', 
    'Standard query', 'Standard query response', 
    'PTR', 'AAAA',
    'Multicast', 'Broadcast', 'SSDP', 'MDNS', 
    'Binding Request', 'Time Request', 'Time Reply', 
    'Echo Request', 'Echo Reply', 'Destination Unreachable', 
    'Who has', 'Tell', 
    }
    
    if protocol.upper() in redundant_protocols:
        return True

    if any(keyword.lower() in str(info).lower() for keyword in redundant_keywords):
        return True

    return False
"""

# Groups traffic types based on services
def classify_traffic_by_service(service, protocol):
    if service in ['Private'] or protocol in ['MDNS', 'SSDP', 'ARP', 'DCHP', 'IGMPv3']:
        return "Private"
    elif service in criteria["First Party"]:
        return "First Party"
    elif service in criteria["Support Party"]:
        return "Support Party"
    else:
        return "Third Party"

# Groups traffic readability based on protocol + info       
def check_readability(protocol, info):
    if protocol in ['TCP', 'TLSv1.2', 'TLSv1.3']:
        if 'Client Hello (SNI=' in str(info):   
            return 'Partially Readable'
    if protocol in ['TLSv1.2', 'TLSv1.3']:
        if 'Certificate' == str(info) or 'Server Hello' in str(info):
            return 'Partially Readable'
    if protocol in ['DHCP']:
        if 'Request' in str(info):
            return 'Partially Readable'
    if protocol in ['DNS', 'MDNS', 'UDP', 'TLSv1']:
        return 'Partially Readable'
    elif protocol in ['TLSv1.2', 'TLSv1.3', 'SSL', 'ICMPv6', 'NTP', 'QUIC', 'TCP', 'IGMPv3', 'DHCP', 'STUN', 'ICMP']:
        return 'Unreadable'
    elif protocol in ['HTTP', 'SSDP']:
        return 'Readable'
    else:
        return 'Unknown'





