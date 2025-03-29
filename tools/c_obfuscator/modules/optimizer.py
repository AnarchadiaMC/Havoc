"""
Optimizer Module - Performs final optimizations on C code before writing to disk
"""

import os
import tempfile
from typing import List, Dict, Set, Any, Tuple, Optional

try:
    import clang.cindex
    from clang.cindex import CursorKind, TokenKind
    CLANG_AVAILABLE = True
except ImportError:
    CLANG_AVAILABLE = False
    print("Warning: clang.cindex not available for optimizer. Using basic optimization.")

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

def remove_duplicate_includes(code: str, verbose: bool = False) -> str:
    """Remove duplicate include statements from the code.
    
    Args:
        code: The C code to process
        verbose: Whether to print verbose output
        
    Returns:
        Code with duplicate includes removed
    """
    # Split the code into lines
    lines = code.split('\n')
    include_lines = []
    non_include_lines = []
    
    # Track unique includes by header path
    unique_includes = {}  # Maps header path to full include line
    headers_order = []    # Preserves original order of headers
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#include'):
            # Extract the header path
            include_parts = stripped.split(' ', 1)
            if len(include_parts) > 1:
                include_directive = include_parts[1].strip()
                # Check if this is a new unique include
                if include_directive not in unique_includes:
                    unique_includes[include_directive] = stripped
                    headers_order.append(include_directive)
        else:
            non_include_lines.append(line)
    
    # Reconstruct the includes in their original order
    for header in headers_order:
        include_lines.append(unique_includes[header])
    
    # Calculate statistics for verbose output
    if verbose:
        total_includes = sum(1 for line in lines if line.strip().startswith('#include'))
        removed_includes = total_includes - len(include_lines)
        if removed_includes > 0:
            print(f"Removed {removed_includes} duplicate include statements")
    
    # Join all includes with non-include lines
    # Put includes at the top of the file
    if include_lines:
        result = '\n'.join(include_lines) + '\n\n' + '\n'.join(non_include_lines)
    else:
        result = '\n'.join(non_include_lines)
    
    return result

def remove_comments(code: str, verbose: bool = False) -> str:
    """Remove comments from C code, keeping syntax intact.
    
    Args:
        code: The C code to process
        verbose: Whether to print verbose output
        
    Returns:
        Code without comments
    """
    # Count bytes before removal
    original_size = len(code)
    
    if not CLANG_AVAILABLE:
        # Simple string-based comment removal (limited functionality)
        result = []
        i = 0
        in_comment = False
        in_line_comment = False
        
        while i < len(code):
            if not in_comment and not in_line_comment and i < len(code) - 1:
                if code[i:i+2] == '/*':
                    in_comment = True
                    result.append(' ')  # Keep space for formatting
                    i += 2
                    continue
                elif code[i:i+2] == '//':
                    in_line_comment = True
                    result.append(' ')  # Keep space for formatting
                    i += 2
                    continue
            
            if in_comment and i < len(code) - 1 and code[i:i+2] == '*/':
                in_comment = False
                result.append('  ')  # Keep space for formatting
                i += 2
                continue
            
            if in_line_comment and code[i] == '\n':
                in_line_comment = False
                result.append('\n')
                i += 1
                continue
            
            if not in_comment and not in_line_comment:
                result.append(code[i])
            else:
                # Replace comment characters with spaces to preserve formatting
                result.append(' ' if code[i] != '\n' else '\n')
            
            i += 1
        
        code_without_comments = ''.join(result)
        
        # Calculate bytes removed
        bytes_removed = original_size - len(code_without_comments)
        
        if verbose:
            print(f"Removed {bytes_removed} bytes of comments ({(bytes_removed / original_size) * 100:.2f}%)")
        
        return code_without_comments
    
    # Create a file with the code to parse with clang
    temp_file_path = create_temp_file(code)
    
    try:
        # Parse the code with clang
        index = clang.cindex.Index.create()
        tu = index.parse(temp_file_path, args=['-x', 'c'])
        
        # Get all comment tokens
        comments = []
        for token in tu.get_tokens(extent=tu.cursor.extent):
            if token.kind == TokenKind.COMMENT:
                comments.append((token.extent.start.offset, token.extent.end.offset))
        
        # Replace comments with spaces to preserve line structure
        if comments:
            # Sort in reverse order to avoid offset issues when replacing
            comments.sort(reverse=True)
            code_bytes = bytearray(code, 'utf-8')
            for start, end in comments:
                for i in range(start, end):
                    if i < len(code_bytes) and code_bytes[i] != ord('\n'):
                        code_bytes[i] = ord(' ')
            code = code_bytes.decode('utf-8')
        
        # Calculate bytes removed
        bytes_removed = original_size - len(code)
        
        if verbose:
            print(f"Removed {bytes_removed} bytes of comments ({(bytes_removed / original_size) * 100:.2f}%)")
        
        return code
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

def remove_blank_lines(code: str, verbose: bool = False) -> str:
    """Remove blank lines from the code while preserving syntax.
    
    Args:
        code: The C code to process
        verbose: Whether to print verbose output
        
    Returns:
        The code without blank lines
    """
    # Split the code into lines
    lines = code.split('\n')
    original_line_count = len(lines)
    
    # Filter out empty lines while preserving preprocessor directives
    non_empty_lines = []
    for line in lines:
        if line.strip() or line.strip().startswith('#'):
            non_empty_lines.append(line)
    
    # Calculate removed lines
    removed_lines = original_line_count - len(non_empty_lines)
    
    if verbose:
        print(f"Removed {removed_lines} blank lines ({(removed_lines / original_line_count) * 100:.2f}% of total lines)")
    
    # Join the lines back together
    return '\n'.join(non_empty_lines)

def optimize(code: str, verbose: bool = False) -> str:
    """Perform all optimizations on the code.
    
    Args:
        code: The C code to optimize
        verbose: Whether to print verbose output
        
    Returns:
        Optimized code
    """
    if verbose:
        print("Performing final optimizations...")
    
    # First remove duplicate includes
    code = remove_duplicate_includes(code, verbose)
    
    # Then remove comments
    code = remove_comments(code, verbose)
    
    # Finally remove blank lines
    code = remove_blank_lines(code, verbose)
    
    return code 