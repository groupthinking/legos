#!/usr/bin/env python3
"""
Blob+Map Pattern Builder for License Data

This script converts JSONL license data into Google's efficient "Blob+Map" pattern:
- licenses.txt: Monolithic file containing all license text (the "blob")
- index.json: Byte offset map for O(1) license lookup (the "map")

This enables lazy-loading: only the index is loaded initially, and individual
licenses are fetched on-demand using byte-range requests or file seeks.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple


class BlobMapBuilder:
    """Builds the Blob+Map pattern from JSONL input."""
    
    def __init__(self, input_path: Path, output_dir: Path):
        """
        Initialize the builder.
        
        Args:
            input_path: Path to input JSONL file
            output_dir: Directory for output files
        """
        self.input_path = input_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.blob_path = self.output_dir / "licenses.txt"
        self.index_path = self.output_dir / "index.json"
    
    def load_jsonl(self) -> List[Dict[str, Any]]:
        """
        Load and parse JSONL input file.
        
        Returns:
            List of license dictionaries
        """
        licenses = []
        
        print(f"[INFO] Loading JSONL from: {self.input_path}")
        
        with open(self.input_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    licenses.append(data)
                except json.JSONDecodeError as e:
                    print(f"[WARN] Skipping invalid JSON at line {line_num}: {e}")
                    continue
        
        print(f"[INFO] Loaded {len(licenses)} license entries")
        return licenses
    
    def build_blob_and_index(self, licenses: List[Dict[str, Any]]) -> Tuple[str, Dict[str, Any]]:
        """
        Build the blob file and index map.
        
        The blob contains all license text concatenated together.
        The index contains metadata and byte offsets for each license.
        
        Args:
            licenses: List of license dictionaries
            
        Returns:
            Tuple of (blob_content, index_data)
        """
        print("[INFO] Building blob and index...")
        
        blob_content = ""
        index_entries = []
        current_offset = 0
        
        for idx, license_data in enumerate(licenses):
            # Extract the main content (text to store in blob)
            content = license_data.get('content', '')
            
            # If no content field, try to serialize the entire object
            if not content:
                content = json.dumps(license_data, ensure_ascii=False, indent=2)
            
            # Ensure content ends with newline for readability
            if content and not content.endswith('\n'):
                content += '\n'
            
            # Add separator between entries for readability
            separator = f"\n{'='*80}\n"
            if idx > 0:
                content = separator + content
                current_offset += len(separator.encode('utf-8'))
            
            # Calculate byte length (UTF-8 encoding)
            content_bytes = content.encode('utf-8')
            byte_length = len(content_bytes)
            
            # Build index entry
            index_entry = {
                'id': license_data.get('id', idx),
                'offset': current_offset,
                'length': byte_length,
            }
            
            # Add optional metadata to index
            if 'name' in license_data:
                index_entry['name'] = license_data['name']
            if 'license_type' in license_data:
                index_entry['license_type'] = license_data['license_type']
            if 'links' in license_data:
                index_entry['links'] = license_data['links']
            
            # Maximum size for metadata list values (in characters)
            MAX_METADATA_SIZE = 200
            
            # Store any other metadata (excluding large fields)
            for key, value in license_data.items():
                if key not in ['content', 'html'] and key not in index_entry:
                    # Only include small metadata
                    if isinstance(value, (str, int, float, bool)) or (isinstance(value, list) and len(str(value)) < MAX_METADATA_SIZE):
                        index_entry[key] = value
            
            index_entries.append(index_entry)
            
            # Append to blob
            blob_content += content
            current_offset += byte_length
        
        # Build complete index structure
        index_data = {
            'version': '1.0',
            'total_licenses': len(licenses),
            'blob_file': 'licenses.txt',
            'encoding': 'utf-8',
            'entries': index_entries
        }
        
        print(f"[INFO] Built blob: {current_offset} bytes")
        print(f"[INFO] Built index: {len(index_entries)} entries")
        
        return blob_content, index_data
    
    def save_blob(self, content: str) -> None:
        """
        Save the blob file.
        
        Args:
            content: The blob content to save
        """
        print(f"[INFO] Writing blob to: {self.blob_path}")
        
        with open(self.blob_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Get file size
        size_bytes = self.blob_path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        print(f"[SUCCESS] Blob written: {size_bytes:,} bytes ({size_mb:.2f} MB)")
    
    def save_index(self, index_data: Dict[str, Any]) -> None:
        """
        Save the index file.
        
        Args:
            index_data: The index data to save
        """
        print(f"[INFO] Writing index to: {self.index_path}")
        
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        # Get file size
        size_bytes = self.index_path.stat().st_size
        size_kb = size_bytes / 1024
        print(f"[SUCCESS] Index written: {size_bytes:,} bytes ({size_kb:.2f} KB)")
    
    def build(self) -> bool:
        """Execute the complete build process.
        
        Returns:
            True if build succeeded, False otherwise
        """
        try:
            # Load JSONL
            licenses = self.load_jsonl()
            
            if not licenses:
                print("[ERROR] No licenses loaded from input file!")
                return False
            
            # Build blob and index
            blob_content, index_data = self.build_blob_and_index(licenses)
            
            # Save outputs
            self.save_blob(blob_content)
            self.save_index(index_data)
            
            print("\n[SUCCESS] Blob+Map build completed successfully!")
            print(f"[INFO] Output directory: {self.output_dir}")
            print(f"[INFO]   - Blob: {self.blob_path.name}")
            print(f"[INFO]   - Index: {self.index_path.name}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Build failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def lookup_license(index_path: Path, blob_path: Path, license_id: int) -> str:
    """
    Demonstrate lazy-loading: lookup a license by ID using the index.
    
    This is the key benefit of the Blob+Map pattern:
    1. Load only the small index.json (few KB)
    2. Use byte offsets to seek directly to the license
    3. Read only the bytes needed for that license
    
    Args:
        index_path: Path to index.json
        blob_path: Path to licenses.txt
        license_id: ID of the license to lookup
        
    Returns:
        The license text content
    """
    # Load index (small file, always in memory)
    with open(index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)
    
    # Find the entry
    entry = None
    for e in index['entries']:
        if e['id'] == license_id:
            entry = e
            break
    
    if not entry:
        raise ValueError(f"License ID {license_id} not found in index")
    
    # Lazy-load: seek to offset and read only the needed bytes
    with open(blob_path, 'rb') as f:
        f.seek(entry['offset'])
        content_bytes = f.read(entry['length'])
        content = content_bytes.decode('utf-8')
    
    return content


def main():
    """Main execution function."""
    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python build.py <input.jsonl> [output_dir]")
        print("       python build.py --demo <index.json> <licenses.txt> <license_id>")
        print()
        print("Examples:")
        print("  python build.py licenses.jsonl")
        print("  python build.py licenses.jsonl ./output")
        print("  python build.py --demo output/index.json output/licenses.txt 0")
        return 1
    
    # Demo mode: demonstrate lazy-loading
    if sys.argv[1] == "--demo":
        if len(sys.argv) < 5:
            print("[ERROR] Demo mode requires: --demo <index.json> <licenses.txt> <license_id>")
            return 1
        
        index_path = Path(sys.argv[2])
        blob_path = Path(sys.argv[3])
        license_id = int(sys.argv[4])
        
        print(f"[DEMO] Lazy-loading license ID {license_id}")
        print(f"[DEMO] Index: {index_path}")
        print(f"[DEMO] Blob: {blob_path}")
        
        try:
            content = lookup_license(index_path, blob_path, license_id)
            print(f"\n[DEMO] Retrieved license (ID {license_id}):")
            print("="*80)
            print(content[:500] + "..." if len(content) > 500 else content)
            print("="*80)
            return 0
        except Exception as e:
            print(f"[ERROR] Demo failed: {e}")
            return 1
    
    # Build mode
    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./output")
    
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        return 1
    
    print("[INFO] Starting Blob+Map builder")
    print(f"[INFO] Input: {input_path}")
    print(f"[INFO] Output: {output_dir}")
    
    builder = BlobMapBuilder(input_path, output_dir)
    success = builder.build()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
