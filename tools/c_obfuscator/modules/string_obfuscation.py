"""
String Obfuscation Module - Handles string obfuscation in C code
"""

import re
import random
from typing import List, Dict, Any


def generate_deobfuscation_function() -> tuple:
    """Generate the deobfuscation function and key
    
    Returns:
        Tuple containing (deobfuscation_code, key)
    """
    # Generate a random key
    key = [random.randint(1, 255) for _ in range(16)]
    key_str = "{" + ", ".join(str(k) for k in key) + "}"
    
    decode_function = f"""
/* String deobfuscation function */
#include <stdlib.h>
#include <string.h>

static char* deobfuscate_string(const unsigned char* obfuscated, size_t len) {{
    static unsigned char key[16] = {key_str};
    char* result = (char*)malloc(len + 1);
    if (!result) return NULL;
    
    for (size_t i = 0; i < len; i++) {{
        unsigned char k = key[i % 16];
        result[i] = (char)((obfuscated[i] + (256 - k)) % 256);
    }}
    result[len] = '\\0';
    
    return result;
}}
"""
    return decode_function, key


def obfuscate_strings_in_text(text: str, key: List[int], verbose: bool = False) -> str:
    """Obfuscate string literals in a specific piece of text using the provided key
    
    Args:
        text: Text to obfuscate strings in
        key: Encryption key to use
        verbose: Whether to print verbose output
        
    Returns:
        Text with obfuscated strings
    """
    # Create a copy of the text to work with
    modified_text = text
    
    # Extract string literals from the text
    string_literals = []
    in_string = False
    escape_next = False
    start_index = -1
    
    i = 0
    while i < len(text):
        # Handle string literals
        if not in_string and text[i] == '"':
            in_string = True
            start_index = i
            i += 1
            continue
        
        if in_string:
            if escape_next:
                escape_next = False
            elif text[i] == '\\':
                escape_next = True
            elif text[i] == '"':
                in_string = False
                # Add if it's not too small
                if i - start_index > 3:
                    string_literals.append({
                        'text': text[start_index:i+1],
                        'start': start_index,
                        'end': i+1
                    })
        
        i += 1
        
    # Better filtering for string literals
    filtered_literals = []
    
    for string in string_literals:
        string_text = string['text']
        
        # Skip strings that are too small, empty strings
        if len(string_text) <= 4 or string_text in ['""', '" "', '"\n"']: 
            continue
            
        # Skip strings with complicated escape sequences
        if '\\r' in string_text or '\\t' in string_text or string_text.count('\\') > 2:
            continue
            
        # Skip strings that are likely to cause issues
        if 'ComputerName' in string_text or 'UserName' in string_text or 'DllRegisterServer' in string_text:
            continue
            
        # Add to filtered list
        filtered_literals.append(string)
    
    # Sort by position (reverse order) to maintain indices
    strings_to_process = sorted(filtered_literals, key=lambda x: -x['start'])
    
    # Limit the number of strings to obfuscate per section
    max_strings_to_obfuscate = min(50, len(strings_to_process))
    strings_to_process = strings_to_process[:max_strings_to_obfuscate]
    
    # Process each string
    replacements = []
    for string in strings_to_process:
        original_string = string['text']
        string_content = original_string[1:-1]  # Remove quotes
        
        # Skip empty strings
        if not string_content:
            continue
        
        # Check if this is a format string
        contains_format_specifier = '%' in string_content
        
        if contains_format_specifier:
            # Identify all format specifiers with this pattern
            format_pattern = r'(%[^%]*[diuoxXfFeEgGaAcslp])'
            
            # Split the string content by format specifiers
            parts = re.split(format_pattern, string_content)
            
            # Check if we have valid parts and proceed
            if parts:
                # Build our replacement
                replacement = ""
                
                # If this is a PRINTF statement, we need special handling
                before_context = text[max(0, string['start'] - 20):string['start']]
                is_printf = "PRINTF" in before_context or "printf" in before_context
                
                if is_printf:
                    # For printf statements with format strings
                    combined_format = ""
                    
                    # Track any regular parts we need to add
                    for i, part in enumerate(parts):
                        if not part:
                            continue
                            
                        if i % 2 == 0:  # Text part
                            combined_format += part
                        else:  # Format specifier
                            combined_format += part
                    
                    # Obfuscate the combined format string
                    obfuscated_bytes = []
                    for j, char in enumerate(combined_format):
                        k = key[j % 16]
                        obf_byte = (ord(char) + k) % 256
                        obfuscated_bytes.append(obf_byte)
                    
                    # Create the deobfuscation call
                    obf_array = ", ".join(str(b) for b in obfuscated_bytes)
                    replacement = f'deobfuscate_string((const unsigned char[]){{{obf_array}}}, {len(combined_format)})'
                    
                    # For verbose output
                    if verbose:
                        print(f"Obfuscated printf format string: {combined_format[:30]}...")
                else:
                    # For regular format strings (not in PRINTF)
                    obfuscated_parts = []
                    
                    for i, part in enumerate(parts):
                        if not part:
                            continue
                            
                        if i % 2 == 0:  # Text part
                            # Obfuscate this text part
                            obfuscated_bytes = []
                            for j, char in enumerate(part):
                                k = key[j % 16]
                                obf_byte = (ord(char) + k) % 256
                                obfuscated_bytes.append(obf_byte)
                            
                            if obfuscated_bytes:
                                obf_array = ", ".join(str(b) for b in obfuscated_bytes)
                                part_code = f'deobfuscate_string((const unsigned char[]){{{obf_array}}}, {len(part)})'
                                obfuscated_parts.append(part_code)
                        else:  # Format specifier
                            obfuscated_parts.append(f'"{part}"')
                    
                    # Create the replacement based on number of parts
                    if len(obfuscated_parts) > 1:
                        replacement = " ".join(obfuscated_parts)
                    elif len(obfuscated_parts) == 1:
                        replacement = obfuscated_parts[0]
                    else:
                        # Skip if we couldn't process any parts
                        continue
                        
                    # For verbose output
                    if verbose:
                        print(f"Obfuscated format string with {len(obfuscated_parts)} parts")
                
                # Check context before replacing
                before_context = text[max(0, string['start'] - 30):string['start']]
                
                # Look for control keywords immediately before the string
                if re.search(r'\b(if|while|for|switch)\s*$', before_context):
                    # This is a control structure, add a space
                    if not replacement.startswith(" "):
                        replacement = " " + replacement

                # Add this replacement to our list
                replacements.append((string['start'], string['end'], replacement))
                continue  # Skip regular obfuscation
        
        # Regular string obfuscation for non-format strings
        try:
            # Skip strings with most escape sequences, but allow some common ones
            if '\\' in string_content and not (string_content.count('\\') == 1 and ('\\n' in string_content or '\\0' in string_content)):
                continue
                
            processed_content = bytes(string_content, 'utf-8').decode('unicode_escape')
        except:
            # Skip if we can't process it
            continue
        
        # Obfuscate each character
        obfuscated_bytes = []
        for i, char in enumerate(processed_content):
            k = key[i % 16]
            obfuscated_byte = (ord(char) + k) % 256
            obfuscated_bytes.append(obfuscated_byte)
        
        # Create obfuscated string as byte array
        obf_array = ", ".join(str(b) for b in obfuscated_bytes)
        replacement = f'deobfuscate_string((const unsigned char[]){{{obf_array}}}, {len(processed_content)})'
        
        # Check context before replacing
        before_context = text[max(0, string['start'] - 30):string['start']]
        
        # Look for control keywords immediately before the string
        if re.search(r'\b(if|while|for|switch)\s*$', before_context):
            # This is a control structure, add a space
            if not replacement.startswith(" "):
                replacement = " " + replacement

        # Add this replacement to our list
        replacements.append((string['start'], string['end'], replacement))
        
        if verbose:
            print(f"Obfuscated string: {original_string[:20]}...")
    
    # Sort replacements by start position (in reverse order to maintain indices)
    replacements.sort(reverse=True)
    
    # Apply all replacements in reverse order to maintain indices
    for start, end, replacement in replacements:
        # Replace the string
        modified_text = modified_text[:start] + replacement + modified_text[end:]
    
    return modified_text 