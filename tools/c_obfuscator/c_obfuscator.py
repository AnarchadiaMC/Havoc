#!/usr/bin/env python3
"""
C Obfuscator - A tool to obfuscate C code
Features:
1. String obfuscation (non-XOR, byte-based)
2. Method scrambling (rearranges function definitions while preserving call order)
3. Reference proxying (wraps function calls through proxy functions)
"""

import os
import sys
import tempfile
import random
from typing import List, Dict, Set, Any, Tuple, Optional

# Make sure we can import from modules directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modules
from modules.file_io import read_input_file, write_output_file
from modules.clang_analysis import (
    preprocess_code, 
    remove_comments, 
    compact_code,
    extract_string_literals, 
    extract_function_declarations,
    extract_functions, 
    analyze_function_dependencies,
    extract_code_sections,
    remove_empty_lines,
    extract_global_variables,
    extract_includes
)
from modules.string_obfuscation import (
    generate_encryption_key,
    generate_deobfuscation_function,
    obfuscate_strings_in_text,
    encrypt_string
)
from modules.function_scrambling import scramble_functions

class CObfuscator:
    def __init__(self, input_file, output_file=None, reference_proxying=True, verbose=False):
        """Initialize the obfuscator with the given input file.
        
        Args:
            input_file: Path to the input C file
            output_file: Path to the output file (default: input_file + ".obf")
            reference_proxying: Whether to enable reference proxying
            verbose: Whether to print verbose output
        """
        self.input_file = input_file
        self.output_file = output_file or f"{input_file}.obf"
        self.reference_proxying = reference_proxying
        self.verbose = verbose
        self.code = ""
        self.obfuscated_code = ""
        self.strings = []
        self.functions = {}
        self.function_dependencies = {}
        self.declarations = []
        self.global_vars = []
        
        # Generate a random encryption key
        self.encryption_key = generate_encryption_key()
        self.deobf_function = generate_deobfuscation_function(self.encryption_key)
        
        # Check if clang is available
        try:
            import clang.cindex
            self.has_clang = True
        except ImportError:
            self.has_clang = False
            if self.verbose:
                print("Warning: clang.cindex not available. Some advanced features disabled.")
        
        # Read the input file
        self.read_input_file()
        
    def read_input_file(self):
        """Read the input file and store its contents"""
        self.code = read_input_file(self.input_file, self.verbose)
        
        # Check if the code already has a deobfuscation function
        self.has_deobfuscation_function = False
        if "static char* deobfuscate_string" in self.code or "static char * deobfuscate_string" in self.code:
            self.has_deobfuscation_function = True
            if self.verbose:
                print("Detected existing deobfuscation function in the input file")
                
    def write_output_file(self):
        """Write the obfuscated code to the output file"""
        write_output_file(self.output_file, self.obfuscated_code, self.verbose)
    
    def obfuscate(self):
        """Obfuscate the read code and write to the output file"""
        # Make sure we have code to obfuscate
        if not self.code:
            self.read_input_file()
            
        # Preprocess the code
        if self.verbose:
            print("Preprocessing code...")
        code = preprocess_code(self.code, self.verbose)
        
        # Extract includes, strings, declarations, functions, and globals
        code_sections = extract_code_sections(code, self.verbose)
        
        # Get the includes
        includes = code_sections.get('includes', '')
        
        # Extract other sections
        self.strings = code_sections.get('strings', [])
        self.declarations = code_sections.get('declarations', [])
        self.functions = code_sections.get('functions', {})
        self.global_vars = code_sections.get('globals', [])
        self.function_dependencies = code_sections.get('dependencies', {})
        
        # Apply reference proxying if enabled
        proxy_functions = []
        if self.reference_proxying:
            try:
                # Apply reference proxying to the code
                from modules.reference_proxying import apply_reference_proxying
                proxied_code, proxy_functions = apply_reference_proxying(
                    code,
                    self.functions,
                    self.verbose
                )
                code = proxied_code
            except ImportError:
                if self.verbose:
                    print("Reference proxying module not found, skipping")
        
        # Obfuscate strings
        obfuscated_code = obfuscate_strings_in_text(code, self.encryption_key, self.verbose)
        
        # Build final obfuscated code
        self.obfuscated_code = self._build_obfuscated_code(
            {
                'includes': includes,
                'deobfuscation_function': self.deobf_function,
                'proxy_functions': proxy_functions,
                'globals': self.global_vars,
                'declarations': self.declarations,
                'functions': self.functions,
                'dependencies': self.function_dependencies,
                'obfuscated_code': obfuscated_code
            }
        )
        
        # Write to output file
        self.write_output_file()
        
        return True

    def _build_obfuscated_code(self, components):
        """Build the final obfuscated code from components.
        
        Args:
            components: Dictionary of code components
            
        Returns:
            The built obfuscated code as a string
        """
        parts = []
        
        # Add includes first - this will contain all unique includes
        if 'includes' in components and components['includes']:
            parts.append(components['includes'])
        
        # Add deobfuscation function only if one doesn't already exist
        if not self.has_deobfuscation_function and 'deobfuscation_function' in components:
            parts.append(components['deobfuscation_function'])
        
        # Add proxy functions
        if 'proxy_functions' in components and components['proxy_functions']:
            if self.verbose:
                print(f"Adding {len(components['proxy_functions'])} proxy functions")
            parts.append("/* Function proxies for reference obfuscation */")
            parts.append('\n'.join(components['proxy_functions']))
        
        # Add globals, declarations, and functions
        # We need to extract these from the obfuscated code since they should be there already
        # but we don't want to duplicate the include statements
        if 'obfuscated_code' in components:
            # Get the content without the includes
            content = components['obfuscated_code']
            
            # Remove any include statements from obfuscated code to avoid duplication
            lines = content.split('\n')
            filtered_lines = [line for line in lines if not line.strip().startswith('#include')]
            content = '\n'.join(filtered_lines)
            
            # Remove the deobfuscation function if we're adding our own
            if not self.has_deobfuscation_function and "static char* deobfuscate_string" in content:
                # Use string manipulation to remove the deobfuscation function
                start_idx = content.find("static char* deobfuscate_string")
                if start_idx == -1:
                    start_idx = content.find("static char * deobfuscate_string")
                
                if start_idx != -1:
                    # Find the end of the function (closing brace)
                    open_braces = 0
                    end_idx = start_idx
                    for i in range(start_idx, len(content)):
                        if content[i] == '{':
                            open_braces += 1
                        elif content[i] == '}':
                            open_braces -= 1
                            if open_braces == 0:
                                end_idx = i + 1
                                break
                    
                    # Remove the function
                    if end_idx > start_idx:
                        content = content[:start_idx] + content[end_idx:]
            
            # Clean up excessive newlines
            content = '\n\n'.join(part for part in content.split('\n\n') if part.strip())
            if content.strip():
                parts.append(content.strip())
        
        return '\n\n'.join(parts)

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Obfuscate C code")
    parser.add_argument("input_file", help="Input C file to obfuscate")
    parser.add_argument("-o", "--output", help="Output file (default: input_file.obf)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-n", "--no-proxying", action="store_true", help="Disable reference proxying")
    
    args = parser.parse_args()
    
    # Create and run the obfuscator
    obfuscator = CObfuscator(
        input_file=args.input_file,
        output_file=args.output,
        reference_proxying=not args.no_proxying,
        verbose=args.verbose
    )
    obfuscator.obfuscate()

if __name__ == "__main__":
    main()
