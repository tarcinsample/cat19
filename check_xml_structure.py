#!/usr/bin/env python3
"""Check XML structure and fix unclosed records."""

import re

with open('/home/parthiv/workspace/15-oec-com/openeducat_erp/openeducat_attendance/demo/attendance_line_demo.xml', 'r') as f:
    lines = f.readlines()

# Track unclosed records
unclosed = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # Check if this is a record start
    if '<record' in line and 'op.attendance.line' in line:
        record_start = i + 1  # Line numbers are 1-based
        found_close = False
        
        # Look for closing tag
        j = i + 1
        while j < len(lines) and j < i + 15:  # Check next 15 lines max
            if '</record>' in lines[j]:
                found_close = True
                break
            elif '<record' in lines[j]:  # Found another record start
                break
            j += 1
        
        if not found_close:
            # Extract record id
            match = re.search(r'id="([^"]+)"', line)
            record_id = match.group(1) if match else f"line_{record_start}"
            unclosed.append((record_start, record_id))
    
    i += 1

if unclosed:
    print(f"Found {len(unclosed)} unclosed records:")
    for line_num, record_id in unclosed:
        print(f"  Line {line_num}: {record_id}")
else:
    print("All records are properly closed")

# Also check for proper XML structure
try:
    import xml.etree.ElementTree as ET
    tree = ET.parse('/home/parthiv/workspace/15-oec-com/openeducat_erp/openeducat_attendance/demo/attendance_line_demo.xml')
    print("\n✅ XML is valid and well-formed")
except ET.ParseError as e:
    print(f"\n❌ XML parsing error: {e}")
    print(f"Error at line {e.position[0]}, column {e.position[1]}")