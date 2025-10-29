# filter_orders.py
import xml.etree.ElementTree as ET
import sys
import os

def filter_o2c_data(input_file, output_file):
    """
    Parses a large XML file in a streaming fashion and filters it to only include 'Order' objects.
    """
    print(f"Starting to process {input_file}...")
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'wb') as out_f:
        out_f.write(b"<?xml version='1.0' encoding='UTF-8'?>\n<log>\n")

        # Use iterparse to handle large files
        context = ET.iterparse(input_file, events=('start', 'end'))

        # Get the root element
        _, root = next(context)

        is_in_object_types = False
        is_in_event_types = False

        for event, elem in context:
            if event == 'start':
                if elem.tag == 'object-types':
                    is_in_object_types = True
                    out_f.write(b'  <object-types>\n')
                elif elem.tag == 'event-types':
                    is_in_event_types = True
                    out_f.write(b'  <event-types>\n')

            elif event == 'end':
                # Handle the schema part: only keep 'Order' object-type
                if is_in_object_types:
                    if elem.tag == 'object-type' and elem.attrib.get('name') == 'Order':
                        out_f.write(b'    ')
                        out_f.write(ET.tostring(elem, encoding='utf-8'))
                    elif elem.tag == 'object-types':
                        out_f.write(b'  </object-types>\n')
                        is_in_object_types = False
                
                # Copy all event types as they might be referenced
                elif is_in_event_types:
                    if elem.tag != 'event-types':
                        out_f.write(b'    ')
                        out_f.write(ET.tostring(elem, encoding='utf-8'))
                    else:
                        out_f.write(b'  </event-types>\n')
                        is_in_event_types = False

                # Handle the data part: find <objects> blocks and extract <Order> from them
                elif elem.tag == 'objects':
                    order_element = elem.find('Order')
                    if order_element is not None:
                        # Re-create the <objects> block with only the <Order> inside
                        out_f.write(b'  <objects>\n')
                        out_f.write(b'    ')
                        out_f.write(ET.tostring(order_element, encoding='utf-8'))
                        out_f.write(b'  </objects>\n')
                
                # Clear the element to free up memory
                elem.clear()
                # Aggressive cleanup for streaming parser
                for child in list(root):
                    root.remove(child)


        out_f.write(b'</log>\n')
    print(f"✅ Successfully created filtered dataset at {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python filter_orders.py <input_xml_path> <output_xml_path>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    try:
        filter_o2c_data(input_path, output_path)
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        sys.exit(1)
