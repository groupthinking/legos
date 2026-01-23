#!/usr/bin/env python3
"""
Example script demonstrating the complete Blob+Map workflow.

This creates sample license data, builds the Blob+Map, and demonstrates
lazy-loading lookups.
"""

import json
from pathlib import Path


def create_sample_data():
    """Create sample license data for demonstration."""
    print("[EXAMPLE] Creating sample license data...")
    
    licenses = [
        {
            "id": 0,
            "name": "requests",
            "license_type": "Apache-2.0",
            "content": "Apache License\nVersion 2.0, January 2004\nhttp://www.apache.org/licenses/\n\nLicensed under the Apache License, Version 2.0",
            "links": ["https://github.com/psf/requests"]
        },
        {
            "id": 1,
            "name": "flask",
            "license_type": "BSD-3-Clause",
            "content": "BSD 3-Clause License\n\nCopyright (c) Pallets\n\nRedistribution and use in source and binary forms are permitted.",
            "links": ["https://github.com/pallets/flask"]
        },
        {
            "id": 2,
            "name": "numpy",
            "license_type": "BSD-3-Clause",
            "content": "NumPy License\n\nCopyright (c) NumPy Developers\n\nRedistribution and use permitted under BSD terms.",
            "links": ["https://github.com/numpy/numpy"]
        },
    ]
    
    # Write JSONL
    output_path = Path("example_licenses.jsonl")
    with open(output_path, 'w', encoding='utf-8') as f:
        for license in licenses:
            json.dump(license, f, ensure_ascii=False)
            f.write('\n')
    
    print(f"[EXAMPLE] Created {len(licenses)} sample licenses in {output_path}")
    return output_path


def main():
    """Run the example workflow."""
    print("=" * 80)
    print("Blob+Map Pattern Example Workflow")
    print("=" * 80)
    print()
    
    # Step 1: Create sample data
    jsonl_path = create_sample_data()
    print()
    
    # Step 2: Explain the build process
    print("[EXAMPLE] Next steps:")
    print()
    print("  1. Build the Blob+Map:")
    print(f"     python build.py {jsonl_path} example_output/")
    print()
    print("  2. This will create:")
    print("     - example_output/licenses.txt (the blob)")
    print("     - example_output/index.json (the map)")
    print()
    print("  3. Demonstrate lazy-loading:")
    print("     python build.py --demo example_output/index.json example_output/licenses.txt 0")
    print()
    print("=" * 80)
    print()
    
    # Let user know they can run build.py now
    print("[EXAMPLE] Sample data created! Run the commands above to see it in action.")


if __name__ == "__main__":
    main()
