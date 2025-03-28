"""
File I/O Module - Handles reading from and writing to files
"""

import os
import sys


def read_input_file(file_path: str, verbose: bool = False) -> str:
    """Read the input C file and return its contents
    
    Args:
        file_path: Path to the input file
        verbose: Whether to print verbose output
        
    Returns:
        The contents of the file as a string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        if verbose:
            print(f"Read {len(code)} bytes from {file_path}")
        return code
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)


def write_output_file(file_path: str, content: str, verbose: bool = False) -> None:
    """Write the obfuscated code to the output file
    
    Args:
        file_path: Path to the output file
        content: Content to write to the file
        verbose: Whether to print verbose output
    """
    try:
        # Safety check: don't write empty content
        if not content:
            print("ERROR: Generated obfuscated code is empty! Not writing to avoid data loss.")
            sys.exit(1)
            
        # Validate file size
        if len(content) < 100:
            print(f"WARNING: Generated obfuscated code is suspiciously small ({len(content)} bytes)!")
            user_input = input("Continue with writing? (y/n): ").lower()
            if user_input != 'y':
                print("Aborted by user.")
                sys.exit(1)
        
        # Create a backup of the original file if it exists
        if os.path.exists(file_path):
            backup_file = f"{file_path}.bak"
            try:
                with open(file_path, 'r', encoding='utf-8') as src, open(backup_file, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                if verbose:
                    print(f"Created backup at {backup_file}")
            except Exception as e:
                print(f"Warning: Failed to create backup: {e}")
        
        # Write the obfuscated code
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        if verbose:
            print(f"Wrote {len(content)} bytes to {file_path}")
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1) 