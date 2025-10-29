#!/usr/bin/env python3
"""
Script to update order values in o2c_data_orders_only.xml
Sets random values between 1000 and 50000 for each order
"""

import xml.etree.ElementTree as ET
import random
import os

# Set seed for reproducibility (optional - remove if you want different values each time)
random.seed(42)

# File paths
script_dir = os.path.dirname(os.path.abspath(__file__))
xml_file = os.path.join(script_dir, '..', 'data', 'o2c_data_orders_only.xml')

print(f"Reading XML file: {xml_file}")
tree = ET.parse(xml_file)
root = tree.getroot()

# Count traces (orders)
traces = root.findall('trace')
print(f"Found {len(traces)} orders")

# Update each order's value
updated_count = 0
for trace in traces:
    for string_elem in trace.findall('string'):
        if string_elem.get('key') == 'order_value':
            # Generate random order value between 1000 and 50000
            new_value = random.uniform(1000, 50000)
            string_elem.set('value', str(new_value))
            updated_count += 1
            
            if updated_count % 200 == 0:
                print(f"Updated {updated_count} orders...")

print(f"\n✅ Updated {updated_count} order values")

# Write back to file
print(f"Writing updated XML back to file...")
tree.write(xml_file, encoding='UTF-8', xml_declaration=True)

print(f"✅ Successfully updated {xml_file}")
print(f"\nOrder values now range from $1,000 to $50,000")

