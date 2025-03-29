"""
Clang Analysis Module - Performs C code analysis using clang
"""

import os
import tempfile
from typing import List, Dict, Set, Any, Tuple, Optional
import random

try:
    import clang.cindex
    from clang.cindex import CursorKind, TokenKind
    CLANG_AVAILABLE = True
except ImportError:
    CLANG_AVAILABLE = False
    print("Warning: clang.cindex not available. Code analysis will be limited.")


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


def preprocess_code(code: str, verbose: bool = False) -> str:
    """Preprocess the code to handle any specific issues
    
    Args:
        code: Original code content
        verbose: Whether to print verbose output
        
    Returns:
        Preprocessed code
    """
    # Add necessary includes if not already present
    required_headers = ["<stdlib.h>", "<string.h>"]
    
    # If clang is not available, return the code as-is with basic preprocessing
    if not CLANG_AVAILABLE:
        # Check for required headers in the simplest way
        for header in required_headers:
            if f"#include {header}" not in code:
                code = f"#include {header}\n" + code
                if verbose:
                    print(f"Adding {header} include for required functions")
        return code
    
    # Create a file with the code to parse with clang
    temp_file_path = create_temp_file(code)
    
    try:
        # Parse the code with clang
        index = clang.cindex.Index.create()
        tu = index.parse(temp_file_path, args=['-x', 'c'])
        
        # Find all include directives using string matching instead of token index
        lines = code.split('\n')
        includes = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('#include'):
                include_path = line[8:].strip()
                includes.append(include_path)
        
        # Add required headers if not present
        added_headers = []
        for header in required_headers:
            if not any(header in include for include in includes):
                if verbose:
                    print(f"Adding {header} include for required functions")
                added_headers.append(f"#include {header}")
        
        if added_headers:
            # Insert at beginning of the file
            result = '\n'.join(added_headers) + '\n' + code
            return result
        
        return code
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def remove_comments(code: str, verbose: bool = False) -> str:
    """Remove comments from C code, keeping whitespace structure.
    
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


def extract_string_literals(code: str, verbose: bool = False) -> List[Dict[str, Any]]:
    """Extract string literals from the C code
    
    Args:
        code: Code to extract string literals from
        verbose: Whether to print verbose output
        
    Returns:
        List of string literals with positions
    """
    if not CLANG_AVAILABLE:
        # Simple string extraction without clang
        string_literals = []
        i = 0
        in_string = False
        start_pos = 0
        escaped = False
        
        while i < len(code):
            if not in_string and code[i] == '"':
                in_string = True
                start_pos = i
            elif in_string:
                if escaped:
                    escaped = False
                elif code[i] == '\\':
                    escaped = True
                elif code[i] == '"':
                    in_string = False
                    # Add the string with its position
                    if i - start_pos > 2:  # Ignore empty strings
                        string_literals.append({
                            'text': code[start_pos:i+1],
                            'start': start_pos,
                            'end': i+1
                        })
            i += 1
        
        if verbose:
            print(f"Extracted {len(string_literals)} string literals")
        
        return string_literals
    
    # Create a file with the code to parse with clang
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
        
        # Filter out very small strings or empty strings
        string_literals = [s for s in string_literals if len(s['text']) > 3]
        
        if verbose:
            print(f"Extracted {len(string_literals)} string literals")
        
        return string_literals
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def extract_function_declarations(code: str, verbose: bool = False) -> List[Dict]:
    """Extract function declarations (prototypes) from the code
    
    Args:
        code: The C code to process
        verbose: Whether to print verbose output
        
    Returns:
        List of function declarations with positions
    """
    if not CLANG_AVAILABLE:
        # Return empty list if clang is not available
        if verbose:
            print("Warning: clang is required for function declaration extraction")
        return []
    
    # Create a file with the code to parse with clang
    temp_file_path = create_temp_file(code)
    
    try:
        # Parse the code with clang
        index = clang.cindex.Index.create()
        tu = index.parse(temp_file_path, args=['-x', 'c'])
        
        declarations = []
        
        # Find all function declarations (but not definitions)
        for cursor in tu.cursor.walk_preorder():
            if cursor.kind == CursorKind.FUNCTION_DECL and not cursor.is_definition():
                start_loc = cursor.extent.start
                end_loc = cursor.extent.end
                
                # Extract the text for this declaration
                text = code[start_loc.offset:end_loc.offset]
                
                declarations.append({
                    'name': cursor.spelling,
                    'text': text,
                    'start': start_loc.offset,
                    'end': end_loc.offset
                })
        
        if verbose:
            print(f"Extracted {len(declarations)} function declarations")
        
        return declarations
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def extract_functions(code: str, verbose: bool = False) -> Dict[str, Dict]:
    """Extract function definitions from the code
    
    Args:
        code: The C code to process
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary mapping function names to function definitions
    """
    if not CLANG_AVAILABLE:
        # Return empty dict if clang is not available
        if verbose:
            print("Warning: clang is required for function extraction")
        return {}
    
    # Create a file with the code to parse with clang
    temp_file_path = create_temp_file(code)
    
    try:
        # Parse the code with clang
        index = clang.cindex.Index.create()
        tu = index.parse(temp_file_path, args=['-x', 'c'])
        
        functions = {}
        
        # Find all function definitions
        for cursor in tu.cursor.walk_preorder():
            if cursor.kind == CursorKind.FUNCTION_DECL and cursor.is_definition():
                start_loc = cursor.extent.start
                end_loc = cursor.extent.end
                
                # Extract the text for this function
                text = code[start_loc.offset:end_loc.offset]
                
                functions[cursor.spelling] = {
                    'name': cursor.spelling,
                    'text': text,
                    'start': start_loc.offset,
                    'end': end_loc.offset
                }
        
        if verbose:
            print(f"Extracted {len(functions)} function definitions")
        
        return functions
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def analyze_function_dependencies(functions: Dict[str, Dict], verbose: bool = False) -> Dict[str, List[str]]:
    """Analyze dependencies between functions
    
    Args:
        functions: Dictionary mapping function names to function definitions
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary mapping function names to lists of dependency names
    """
    if not CLANG_AVAILABLE:
        # Return empty dict if clang is not available
        if verbose:
            print("Warning: clang is required for dependency analysis")
        return {}
    
    # Create a temporary file with all functions
    code = '\n'.join(func['text'] for func in functions.values())
    temp_file_path = create_temp_file(code)
    
    try:
        # Parse the code with clang
        index = clang.cindex.Index.create()
        tu = index.parse(temp_file_path, args=['-x', 'c'])
        
        dependencies = {name: [] for name in functions.keys()}
        
        # Map from function cursor to function name
        cursor_to_name = {}
        
        # First, map cursors to function names
        for cursor in tu.cursor.walk_preorder():
            if cursor.kind == CursorKind.FUNCTION_DECL and cursor.is_definition():
                cursor_to_name[cursor.spelling] = cursor.spelling
        
        # Then find call expressions within each function
        for cursor in tu.cursor.walk_preorder():
            if cursor.kind == CursorKind.FUNCTION_DECL and cursor.is_definition():
                caller_name = cursor.spelling
                
                # Find all call expressions within this function
                for child in cursor.walk_preorder():
                    if child.kind == CursorKind.CALL_EXPR:
                        callee_name = child.spelling
                        
                        # Only add if the callee is one of our functions
                        if callee_name in functions and callee_name != caller_name:
                            if callee_name not in dependencies[caller_name]:
                                dependencies[caller_name].append(callee_name)
        
        if verbose:
            for func, deps in dependencies.items():
                if deps:
                    print(f"Function {func} depends on: {', '.join(deps)}")
                else:
                    print(f"Function {func} has no dependencies")
        
        return dependencies
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def extract_global_variables(code: str, verbose: bool = False) -> List[Dict]:
    """Extract global variable declarations from the code
    
    Args:
        code: The C code to process
        verbose: Whether to print verbose output
        
    Returns:
        List of global variable declarations with positions
    """
    if not CLANG_AVAILABLE:
        # Return empty list if clang is not available
        if verbose:
            print("Warning: clang is required for global variable extraction")
        return []
    
    # Create a file with the code to parse with clang
    temp_file_path = create_temp_file(code)
    
    try:
        # Parse the code with clang
        index = clang.cindex.Index.create()
        tu = index.parse(temp_file_path, args=['-x', 'c'])
        
        globals_list = []
        
        # Find all global variable declarations
        for cursor in tu.cursor.walk_preorder():
            if cursor.kind == CursorKind.VAR_DECL and cursor.semantic_parent.kind == CursorKind.TRANSLATION_UNIT:
                start_loc = cursor.extent.start
                end_loc = cursor.extent.end
                
                # Extract the text for this global variable
                text = code[start_loc.offset:end_loc.offset]
                
                globals_list.append({
                    'name': cursor.spelling,
                    'text': text,
                    'start': start_loc.offset,
                    'end': end_loc.offset
                })
        
        if verbose:
            print(f"Extracted {len(globals_list)} global variables")
        
        return globals_list
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def extract_includes(code: str, verbose: bool = False) -> List[Dict]:
    """Extract #include directives from the code
    
    Args:
        code: The C code to process
        verbose: Whether to print verbose output
        
    Returns:
        List of include directives with positions
    """
    # We need to handle includes using string processing since clang doesn't expose preprocessor tokens directly
    
    # Use a string-based approach to extract includes
    lines = code.split('\n')
    includes = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#include'):
            includes.append({
                'text': line,
                'line': i,
                'include_path': stripped[8:].strip()
            })
    
    if verbose:
        print(f"Extracted {len(includes)} include directives")
    
    return includes


def extract_code_sections(code: str, verbose: bool = False) -> Dict[str, Any]:
    """Extract different sections of the code (includes, strings, declarations, functions, globals)
    
    Args:
        code: The C code to process
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary with different code sections
    """
    if not CLANG_AVAILABLE:
        return {'code': code}
    
    if verbose:
        print("Extracting code sections using clang...")
    
    # Preprocess the code
    preprocessed_code = preprocess_code(code, verbose)
    
    # Extract includes first
    includes_list = extract_includes(preprocessed_code, verbose)
    includes_text = '\n'.join(include['text'] for include in includes_list)
    
    # Extract string literals
    strings = extract_string_literals(preprocessed_code, verbose)
    
    # Extract function declarations
    declarations = extract_function_declarations(preprocessed_code, verbose)
    
    # Extract function definitions
    functions = extract_functions(preprocessed_code, verbose)
    
    # Extract global variables
    globals_list = extract_global_variables(preprocessed_code, verbose)
    
    # Analyze function dependencies
    dependencies = analyze_function_dependencies(functions, verbose)
    
    return {
        'includes': includes_text,
        'strings': strings,
        'declarations': declarations,
        'functions': functions,
        'globals': globals_list,
        'dependencies': dependencies,
        'code': preprocessed_code
    }


def remove_empty_lines(code: str, verbose: bool = False) -> str:
    """Remove empty lines from the code
    
    Args:
        code: The C code to process
        verbose: Whether to print verbose output
        
    Returns:
        The code without empty lines
    """
    lines = code.split('\n')
    total_lines = len(lines)
    
    # Filter out empty lines
    non_empty_lines = [line for line in lines if line.strip()]
    
    empty_lines_removed = total_lines - len(non_empty_lines)
    
    if verbose:
        print(f"Removed {empty_lines_removed} empty lines ({(empty_lines_removed / total_lines) * 100:.2f}% of total lines)")
    
    return '\n'.join(non_empty_lines)


def compact_code(code: str, verbose: bool = False) -> str:
    """Compact the code using clang-format
    
    Args:
        code: The C code to compact
        verbose: Whether to print verbose output
        
    Returns:
        Compacted code
    """
    if verbose:
        print("Compacting code using clang-format...")
    
    original_size = len(code)
    
    # Use clang-format to format the code
    temp_file_path = create_temp_file(code)
    
    try:
        # Use os.system to run clang-format
        result_file = f"{temp_file_path}.formatted"
        os.system(f"clang-format -style=compressed {temp_file_path} > {result_file}")
        
        # Read the formatted code
        if os.path.exists(result_file):
            with open(result_file, 'r') as f:
                formatted_code = f.read()
            
            # Clean up the formatted file
            os.unlink(result_file)
            
            if verbose:
                new_size = len(formatted_code)
                removed = original_size - new_size
                if removed > 0:
                    print(f"Removed {removed} bytes by formatting ({removed / original_size * 100:.2f}%)")
                else:
                    print("Code size increased after formatting")
            
            return formatted_code
        
        return code
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path) 