"""
String Obfuscation Module - Handles string obfuscation in C code
"""

import re
import random
from typing import List, Dict, Any


def generate_encryption_key() -> List[int]:
    """Generate a random encryption key for string obfuscation
    
    Returns:
        List of random bytes for the encryption key
    """
    # Generate a 16-byte random key
    return [random.randint(0, 255) for _ in range(16)]


def generate_deobfuscation_function(encryption_key: List[int]) -> str:
    """Generate a C function to deobfuscate strings at runtime
    
    Args:
        encryption_key: The encryption key to embed in the function
        
    Returns:
        C code for the deobfuscation function
    """
    # Format the key as a comma-separated list of bytes
    key_str = ', '.join(str(b) for b in encryption_key)
    
    # Create the deobfuscation function code
    deobf_function = f"""/* String deobfuscation function */
#include <stdlib.h>
#include <string.h>

static char* deobfuscate_string(const unsigned char* obfuscated, size_t len) {{
    static unsigned char key[16] = {{{key_str}}};
    char* result = (char*)malloc(len + 1);
    if (!result) return NULL;
    
    for (size_t i = 0; i < len; i++) {{
        unsigned char k = key[i % 16];
        result[i] = (char)((obfuscated[i] + (256 - k)) % 256);
    }}
    result[len] = '\\0';
    
    return result;
}}"""
    
    return deobf_function


def obfuscate_strings_in_text(text: str, encryption_key: List[int], verbose: bool = False) -> str:
    """Obfuscate string literals in the given text
    
    Args:
        text: C code text to process
        encryption_key: The encryption key to use
        verbose: Whether to print verbose output
        
    Returns:
        Text with string literals obfuscated
    """
    # Extract all string literals from the text
    result = text
    
    # First handle printf format strings (which need special handling due to format specifiers)
    printf_pattern = r'PRINTF\s*\(\s*("(?:[^"\\]|\\.)*"(?:\s*,)?(?:\s*"(?:[^"\\]|\\.)*")*)'
    
    for match in re.finditer(printf_pattern, result, re.DOTALL):
        format_str_group = match.group(1)
        
        # Check if this is actually a format string with arguments
        if '\\n' in format_str_group or '%' in format_str_group:
            if verbose:
                shortened = format_str_group[:20] + ('...' if len(format_str_group) > 20 else '')
                print(f"Obfuscated printf format string: {shortened}")
                
            # Extract the individual parts: format string and literal parts
            parts = re.findall(r'"([^"]*)"', format_str_group)
            
            if len(parts) == 1:
                # Single format string - simple case
                obfuscated = _obfuscate_string(parts[0], encryption_key)
                result = result.replace(f'"{parts[0]}"', f'deobfuscate_string((const unsigned char[]){{' + obfuscated + '}}, {len(parts[0])})')
            else:
                # Multiple string parts in a printf - more complex
                if verbose:
                    print(f"Obfuscated format string with {len(parts)} parts")
                
                # Build a replacement that preserves the original structure
                replacement = format_str_group
                for part in parts:
                    if part:  # Skip empty strings
                        obfuscated = _obfuscate_string(part, encryption_key)
                        replacement = replacement.replace(f'"{part}"', f'deobfuscate_string((const unsigned char[]){{' + obfuscated + '}}, {len(part)})')
                
                result = result.replace(format_str_group, replacement)
    
    # Then handle simple string literals (PUTS, assignments, etc.)
    string_pattern = r'"((?:[^"\\]|\\.)*)"'
    
    for match in re.finditer(string_pattern, result):
        string_content = match.group(1)
        original = f'"{string_content}"'
        
        # Skip already processed strings (from printf handling)
        if 'deobfuscate_string(' in original:
            continue
            
        # Skip empty strings
        if not string_content:
            continue
            
        # Obfuscate the string
        obfuscated = _obfuscate_string(string_content, encryption_key)
        replacement = f'deobfuscate_string((const unsigned char[]){{' + obfuscated + '}}, {len(string_content)})'
        
        if verbose:
            shortened = string_content[:20] + ('...' if len(string_content) > 20 else '')
            print(f'Obfuscated string: "{shortened}"')
        
        # Replace in the result, but only whole strings (not parts of other replacements)
        result = result.replace(original, replacement)
    
    return result 


def _obfuscate_string(string: str, key: List[int]) -> str:
    """Obfuscate a string using the encryption key
    
    Args:
        string: String to obfuscate
        key: Encryption key
        
    Returns:
        Comma-separated string of obfuscated bytes
    """
    # Try to handle escape sequences
    try:
        processed_string = bytes(string, 'utf-8').decode('unicode_escape')
    except:
        # If we can't process escape sequences, use the original string
        processed_string = string
    
    # Obfuscate each character
    obfuscated_bytes = []
    for i, char in enumerate(processed_string):
        k = key[i % 16]
        obfuscated_byte = (ord(char) + k) % 256
        obfuscated_bytes.append(obfuscated_byte)
    
    # Format as comma-separated list
    return ', '.join(str(b) for b in obfuscated_bytes) 