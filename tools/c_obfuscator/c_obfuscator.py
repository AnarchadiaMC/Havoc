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
    remove_empty_lines
)
from modules.string_obfuscation import generate_deobfuscation_function, obfuscate_strings_in_text
from modules.function_scrambling import scramble_functions

class CObfuscator:
    def __init__(self, input_file: str, output_file: str, verbose: bool = False):
        """Initialize the C obfuscator
        
        Args:
            input_file: Path to the input C file
            output_file: Path to the output file to write obfuscated code
            verbose: Whether to print verbose output
        """
        self.input_file = input_file
        self.output_file = output_file
        self.verbose = verbose
        self.code = ""
        self.obfuscated_code = ""
        self.functions = []
        self.function_declarations = []
        self.function_dependencies = {}
        self.string_literals = []
        self.deobf_function = ""
        self.encryption_key = []
        
    def obfuscate(self) -> None:
        """Obfuscate the C code"""
        # Step 1: Read input file
        self.code = read_input_file(self.input_file, self.verbose)
        
        # Step 2: Preprocess code
        self.code = preprocess_code(self.code, self.verbose)
        
        # Step 3: Remove comments
        self.code = remove_comments(self.code, self.verbose)
        
        # Step 4: Remove empty whitespace lines
        self.code = remove_empty_lines(self.code, self.verbose)
        
        # Step 5: Extract string literals
        self.string_literals = extract_string_literals(self.code, self.verbose)
        
        # Step 6: Extract function declarations
        self.function_declarations = extract_function_declarations(self.code, self.verbose)
        
        # Step 7: Extract functions
        self.functions = extract_functions(self.code, self.verbose)
        
        # Step 8: Analyze function dependencies
        self.function_dependencies = analyze_function_dependencies(self.functions, self.verbose)
        
        # Step 9: Extract sections of the code
        code_sections = extract_code_sections(
            self.code, 
            self.functions, 
            self.function_declarations, 
            self.verbose
        )
        
        # Step 10: Generate deobfuscation function and key
        self.deobf_function, self.encryption_key = generate_deobfuscation_function()
        
        # Step 11: Build obfuscated code
        self._build_obfuscated_code(code_sections)
        
        # Step 12: Write output file
        write_output_file(self.output_file, self.obfuscated_code, self.verbose)
        
    def _build_obfuscated_code(self, code_sections: Dict[str, str]) -> None:
        """Build the obfuscated code from scratch to avoid duplicates
        
        Args:
            code_sections: Dictionary containing 'includes', 'globals', and 'remaining' sections
        """
        if self.verbose:
            print("Building obfuscated code from scratch to avoid duplicates")
        
        # Start with includes
        obfuscated = code_sections['includes'] + "\n"
        
        # Add deobfuscation function
        obfuscated += self.deobf_function + "\n"
        
        # Add global variables
        obfuscated += code_sections['globals'] + "\n"
        
        # Scramble functions while respecting dependencies
        scrambled_functions = scramble_functions(self.functions, self.function_dependencies, self.verbose)
        
        # Apply string obfuscation to each function
        if self.verbose:
            print("Applying string obfuscation...")
            
        obfuscated_functions = []
        for function in scrambled_functions:
            # Obfuscate strings in this function
            obfuscated_function_text = obfuscate_strings_in_text(
                function['text'], 
                self.encryption_key, 
                self.verbose
            )
            obfuscated_functions.append(obfuscated_function_text)
        
        # Join all functions
        obfuscated += "\n".join(obfuscated_functions)
        
        # Add remaining code (after string obfuscation)
        remaining_code = obfuscate_strings_in_text(
            code_sections['remaining'], 
            self.encryption_key, 
            self.verbose
        )
        obfuscated += "\n" + remaining_code
        
        # Set the final obfuscated code
        self.obfuscated_code = obfuscated
        
        if self.verbose:
            print(f"Final obfuscated code size: {len(self.obfuscated_code)} bytes")


def main():
    """Main entry point for the obfuscator"""
    parser = argparse.ArgumentParser(description='Obfuscate C code')
    parser.add_argument('input_file', help='Input C file to obfuscate')
    parser.add_argument('-o', '--output', required=True, help='Output file for obfuscated code')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    obfuscator = CObfuscator(args.input_file, args.output, args.verbose)
    obfuscator.obfuscate()
    

if __name__ == '__main__':
    main()
