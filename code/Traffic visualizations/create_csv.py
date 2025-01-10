import os
import pyshark
import csv
import argparse


cap = pyshark.FileCapture(
    '/home/michelle/traffic_visualizations/Touch Commands/ExpNT2.pcapng',
    use_json=True,
    custom_parameters=['--no-duplicate-keys']
)
cap.set_debug()  # Enable debug mode
for packet in cap:
    print(packet)
    
    
"""
# Argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("category", help="Name of the directory of which contains the csv that would be merged")
args = parser.parse_args()

cur_dir = os.path.dirname(os.path.abspath(__file__))
category = args.category
experiment_path = os.path.join(cur_dir, category)
csv_files = [os.path.join(experiment_path, f) for f in os.listdir(experiment_path) if f.endswith(".pcapng")]
    

for file in csv_files:

    if not csv_files:
        print(f"No CSV files found in directory: {experiment_dir}")

    # Output CSV file
    print(f"Loading {file}...")
    exp_name = os.path.splitext(os.path.basename(file))[0]
    experiment_name = exp_name[-1]
    output_csv_file = f"Z_NT{experiment_name}.csv"

    # Define the columns you want in the CSV file
    columns = ['No.', 'Time', 'Source', 'Destination', 'Protocol', 'Length', 'Info', 'Payload']

    # Open the CSV file for writing
    with open(output_csv_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
    
        # Write the header
        writer.writerow(columns)
    
        # Read packets from the .pcapng file
        cap = pyshark.FileCapture(file, use_json=True)  # Use JSON for detailed payload access
        cap.set_debug()
        for packet in cap:
            print(f"Packet #{packet.number}:")
            try:
                no = packet.number
                time = packet.sniff_time
                source = getattr(packet.ip, 'src', 'N/A') if hasattr(packet, 'ip') else 'N/A'
                destination = getattr(packet.ip, 'dst', 'N/A') if hasattr(packet, 'ip') else 'N/A'
                protocol = packet.highest_layer
                length = packet.length
                info = str(packet)
                
                print(f"Packet {packet.number}:")
                print(f"Timestamp {packet.sniff_time}")

        	# Print all layers and their fields
                for layer in packet.layers:
            	    print(f"Layer Name: {layer.layer_name}")
            	    print(f"Fields: {layer.field_names}")

            	    # Print individual fields and their values
            	    for field in layer.field_names:
                        field_value = getattr(layer, field, None)
                        print(f"  {field}: {field_value}")
                print("\n")  # Separate packets visually

                # Extract payload safely
                payload = None
                if hasattr(packet, '_packet'):
                    raw_data = packet._packet.data
                    if isinstance(raw_data, list):
                        payload = ''.join([bytes(data).hex() for data in raw_data])
                    else:
                        payload = raw_data.hex() if hasattr(raw_data, 'hex') else 'N/A'

                # Write to CSV
                writer.writerow([no, time, source, destination, protocol, length, info, payload or 'N/A'])
            except Exception as e:
                pass


    # Confirm completion
    print(f"CSV file with all payloads saved to {output_csv_file}")


"""
