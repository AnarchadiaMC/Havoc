"""
String Obfuscation Module - Handles string obfuscation in C code
"""

import random
import os
import tempfile
from typing import List, Dict, Any, Tuple

try:
    import clang.cindex
    from clang.cindex import CursorKind, TokenKind
    CLANG_AVAILABLE = True
except ImportError:
    CLANG_AVAILABLE = False
    print("Warning: clang.cindex not available. String obfuscation will be limited.")


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
    
    # Create the deobfuscation function code without includes
    deobf_function_body = f"""static char* deobfuscate_string(const unsigned char* obfuscated, size_t len) {{
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
    
    # Create the full deobfuscation function with includes and comment
    deobf_function = f"""/* String deobfuscation function */
#include <stdlib.h>
#include <string.h>

{deobf_function_body}"""
    
    return deobf_function


def create_temp_file(code: str) -> str:
    """Create a temporary file with the given code.
    
    Args:
        code: The code to write to the file
        
    Returns:
        Path to the temporary file
    """
    with tempfile.NamedTemporaryFile(suffix='.c', delete=False) as temp_file:
        temp_file.write(code.encode('utf-8'))
        return temp_file.name


def get_includes(code: str) -> List[str]:
    """Extract include directives from the code
    
    Args:
        code: The C code to process
        
    Returns:
        List of include directives
    """
    includes = []
    for line in code.split('\n'):
        line = line.strip()
        if line.startswith('#include'):
            includes.append(line)
    return includes


def get_string_literals(code: str, verbose: bool = False) -> List[Dict[str, Any]]:
    """Find string literals in the code using clang
    
    Args:
        code: The code to search
        verbose: Whether to print verbose output
        
    Returns:
        List of string literals with positions
    """
    if not CLANG_AVAILABLE:
        if verbose:
            print("Warning: clang.cindex not available. String extraction will be limited.")
        return []
    
    temp_file_path = create_temp_file(code)
    
    try:
        # Parse the code with clang
        index = clang.cindex.Index.create()
        tu = index.parse(temp_file_path, args=['-x', 'c'])
        
        string_literals = []
        
        # Find all string literals
        for token in tu.get_tokens(extent=tu.cursor.extent):
            if token.kind == TokenKind.LITERAL and token.spelling.startswith('"'):
                # This is a string literal
                string_literals.append({
                    'text': token.spelling,
                    'start': token.extent.start.offset,
                    'end': token.extent.end.offset
                })
        
        if verbose:
            print(f"Found {len(string_literals)} string literals using clang")
        
        return string_literals
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def obfuscate_strings_in_text(text: str, encryption_key: List[int], verbose: bool = False) -> str:
    """Obfuscate string literals in the given text
    
    Args:
        text: C code text to process
        encryption_key: The encryption key to use
        verbose: Whether to print verbose output
        
    Returns:
        Text with string literals obfuscated
    """
    # Make a copy of the original text
    result = text
    
    # Find all string literals in the result
    string_literals = get_string_literals(result, verbose)
    
    # We need to process matches in reverse order to avoid invalidating offsets
    for string_lit in sorted(string_literals, key=lambda x: x['start'], reverse=True):
        string_content = string_lit['text']
        
        # Skip empty strings or very short strings
        if len(string_content) <= 2:  # Just quotes
            continue
            
        # Remove quotes to get actual content
        string_content = string_content[1:-1]
            
        # Skip already processed strings
        if 'deobfuscate_string(' in string_content:
            continue
            
        # Get the start and end positions of the string literal
        start = string_lit['start']
        end = string_lit['end']
        
        # Process the string content for length calculation
        try:
            processed_string = bytes(string_content, 'utf-8').decode('unicode_escape', errors='replace')
            actual_length = len(processed_string)
        except:
            actual_length = len(string_content)
        
        # Obfuscate the string
        obfuscated = _obfuscate_string(string_content, encryption_key)
        replacement = f'deobfuscate_string((const unsigned char[]){{{obfuscated}}}, {actual_length})'
        
        # Perform the replacement
        result = result[:start] + replacement + result[end:]
        
        if verbose:
            shortened = string_content[:20] + ('...' if len(string_content) > 20 else '')
            print(f'Obfuscated string: "{shortened}"')
    
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


def encrypt_string(string, key):
    """Encrypt a string with a key.
    
    Args:
        string: The string to encrypt
        key: The encryption key (list of bytes)
        
    Returns:
        The encrypted string formatted for C code
    """
    encrypted = []
    for i, char in enumerate(string):
        encrypted_byte = (ord(char) + key[i % len(key)]) % 256
        encrypted.append(encrypted_byte)
        
    # Format for C code
    return ', '.join(str(b) for b in encrypted) 