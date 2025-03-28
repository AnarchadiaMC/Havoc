#!/usr/bin/env python3
"""
C Obfuscator - A tool to obfuscate C code
Features:
1. String obfuscation (non-XOR, byte-based)
2. Method scrambling (rearranges function definitions while preserving call order)
"""

import sys
import os
import argparse
import random
import re
import shutil
from typing import List, Dict, Set, Any

# Import modules
from modules.file_io import read_input_file, write_output_file
from modules.code_analysis import (
    preprocess_code, 
    remove_comments, 
    compact_code,
    extract_string_literals, 
    extract_function_declarations,
    extract_functions, 
    analyze_function_dependencies,
    extract_code_sections,
    remove_empty_lines,
    extract_global_variables
)
from modules.string_obfuscation import (
    generate_encryption_key,
    generate_deobfuscation_function,
    obfuscate_strings_in_text
)
from modules.function_scrambling import scramble_functions

class CObfuscator:
    def __init__(self, input_file: str, output_file: str = None, verbose: bool = False):
        """Initialize the C obfuscator
        
        Args:
            input_file: Path to the input C file
            output_file: Path to the output file to write obfuscated code
            verbose: Whether to print verbose output
        """
        self.input_file = input_file
        self.output_file = output_file
        self.verbose = verbose
        self.code = None
        self.obfuscated_code = None
        self.strings = []
        self.functions = {}
        self.declarations = []
        self.global_vars = []
        self.function_dependencies = {}
        self.encryption_key = generate_encryption_key()
        self.deobf_function = generate_deobfuscation_function(self.encryption_key)
        
    def read_input_file(self) -> None:
        """Read the input file and store its contents
        """
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                self.code = f.read()
                if self.verbose:
                    print(f"Read {len(self.code)} bytes from {self.input_file}")
        except Exception as e:
            print(f"Error reading input file: {e}")
            exit(1)
            
    def write_output_file(self) -> None:
        """Write the obfuscated code to the output file
        """
        if not self.output_file:
            self.output_file = self.input_file + ".obf"
            
        try:
            # Create a backup of the output file if it exists
            if os.path.exists(self.output_file):
                backup = self.output_file + '.bak'
                try:
                    shutil.copy2(self.output_file, backup)
                    if self.verbose:
                        print(f"Created backup at {backup}")
                except Exception as e:
                    print(f"Warning: Could not create backup: {e}")
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                f.write(self.obfuscated_code)
                if self.verbose:
                    print(f"Wrote {len(self.obfuscated_code)} bytes to {self.output_file}")
        except Exception as e:
            print(f"Error writing output file: {e}")
            exit(1)
    
    def obfuscate(self) -> None:
        """Perform the obfuscation process
        """
        if not self.code:
            self.read_input_file()
            
        # Preprocess the code (add needed includes, etc.)
        self.code = preprocess_code(self.code, self.verbose)
            
        # Remove comments from the code
        self.code = remove_comments(self.code, self.verbose)
        
        # Remove empty lines from the code
        self.code = remove_empty_lines(self.code, self.verbose)
        
        # Extract string literals
        self.strings = extract_string_literals(self.code, self.verbose)
        
        # Extract function declarations for dependency tracking
        self.declarations = extract_function_declarations(self.code, self.verbose)
        
        # Extract function definitions
        self.functions = extract_functions(self.code, self.verbose)
        
        # Analyze function dependencies
        self.function_dependencies = analyze_function_dependencies(self.functions, self.verbose)
        
        # Extract global variables
        self.global_vars = extract_global_variables(self.code, self.functions, self.declarations, self.verbose)
        
        # Extract different code sections
        code_sections = extract_code_sections(
            self.code,
            self.functions,
            self.declarations,
            self.global_vars,
            self.verbose
        )
        
        # Build the obfuscated code
        self._build_obfuscated_code(code_sections)
        
        # Write the output
        self.write_output_file()
        
    def _build_obfuscated_code(self, code_sections: Dict[str, str]) -> None:
        """Build the obfuscated code from scratch to avoid duplicates
        
        Args:
            code_sections: Dictionary containing 'includes', 'globals', and 'remaining' sections
        """
        if self.verbose:
            print("Building obfuscated code from scratch to avoid duplicates")
        
        # Process includes - force no blank lines between them
        includes = [line.strip() for line in code_sections['includes'].split('\n') if line.strip().startswith('#include')]
        includes_section = '\n'.join(includes)
        
        # Start with the compacted includes
        obfuscated = includes_section
        
        # Add deobfuscation function - no extra newlines
        obfuscated += "\n" + self.deobf_function.strip()
        
        # Add global variables - these MUST come before any functions
        obfuscated += "\n" + code_sections['globals'].strip()
        
        # Scramble functions while respecting dependencies
        scrambled_functions = scramble_functions(self.functions, self.function_dependencies, self.verbose)
        
        # Apply string obfuscation to each function
        if self.verbose:
            print("Applying string obfuscation...")
            
        obfuscated_functions = []
        for function_info in scrambled_functions:
            # Obfuscate strings in this function
            obfuscated_function_text = obfuscate_strings_in_text(
                function_info['text'], 
                self.encryption_key, 
                self.verbose
            ).strip()
            obfuscated_functions.append(obfuscated_function_text)
        
        # Join all functions without blank lines between them
        obfuscated += "\n" + "\n".join(obfuscated_functions)
        
        # Add remaining code (after string obfuscation)
        if code_sections['remaining'].strip():
            remaining_code = obfuscate_strings_in_text(
                code_sections['remaining'], 
                self.encryption_key, 
                self.verbose
            ).strip()
            obfuscated += "\n" + remaining_code
        
        # Set the final obfuscated code
        self.obfuscated_code = obfuscated
        
        if self.verbose:
            print(f"Final obfuscated code size: {len(self.obfuscated_code)} bytes")


def main():
    """Main entry point for the script
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Obfuscate C code')
    parser.add_argument('input_file', help='Input C file to obfuscate')
    parser.add_argument('-o', '--output', help='Output file (default: <input>.obf.c)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    # Default output file if not specified
    if not args.output:
        args.output = args.input_file + '.obf'
    
    # Create and run the obfuscator
    obfuscator = CObfuscator(args.input_file, args.output, args.verbose)
    obfuscator.obfuscate()
    
if __name__ == '__main__':
    main()
