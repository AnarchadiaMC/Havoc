"""
Reference Proxying Module - Handles creation of proxy functions and call replacements
"""

from typing import Dict, List, Tuple, Set, Optional
import hashlib
import os
import tempfile
import sys

try:
    import clang.cindex
    from clang.cindex import CursorKind, TokenKind
    CLANG_AVAILABLE = True
except ImportError:
    CLANG_AVAILABLE = False
    print("Error: clang.cindex module is REQUIRED. Please install libclang and python-clang bindings.")
    print("Reference proxying REQUIRES clang to function properly and will not work without it.")
    print("Install instructions:")
    print("  On Debian/Ubuntu: apt-get install libclang-dev python3-clang")
    print("  On macOS: brew install llvm && pip install clang")
    print("  On Windows: pip install clang")
    sys.exit(1)  # Exit immediately if clang is not available


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


def _parse_function_with_clang(code: str, function_name: str) -> Tuple[Optional[str], Optional[List[str]]]:
    """
    Parse a function using libclang to extract return type and arguments.
    
    Args:
        code: Code containing the function declaration or definition
        function_name: Name of the function to parse
        
    Returns:
        Tuple of (return_type, argument_list)
    """
    # Create a temporary file to hold the code
    temp_file_path = create_temp_file(code)
    
    try:
        # Parse the code with clang
        index = clang.cindex.Index.create()
        tu = index.parse(temp_file_path)
        
        # Find the function declaration/definition
        function_cursor = None
        for cursor in tu.cursor.walk_preorder():
            if (cursor.kind == CursorKind.FUNCTION_DECL and 
                cursor.spelling == function_name):
                function_cursor = cursor
                break
        
        if not function_cursor:
            return None, None
        
        # Extract the original tokens to get the exact return type as written in source
        tokens = list(function_cursor.get_tokens())
        
        # Extract the return type from tokens
        return_type = ""
        for i, token in enumerate(tokens):
            if token.spelling == function_name:
                # Found the function name, everything before it (excluding qualifiers) is the return type
                return_type = " ".join(t.spelling for t in tokens[:i])
                break
                
        if not return_type:
            # Fallback to clang's result type spelling if we couldn't extract from tokens
            return_type = function_cursor.result_type.spelling
        
        # Extract parameters exactly as they appear in source
        params = []
        token_params = []
        in_params = False
        param_text = ""
        
        # Extract parameter text from tokens
        for token in tokens:
            if token.spelling == '(':
                in_params = True
                continue
            elif token.spelling == ')':
                if param_text.strip():
                    token_params.append(param_text.strip())
                break
            
            if in_params:
                if token.spelling == ',':
                    token_params.append(param_text.strip())
                    param_text = ""
                else:
                    param_text += token.spelling + " "
        
        # If we extracted parameters from tokens, use those
        if token_params:
            params = token_params
        else:
            # Fallback to clang's argument extraction
            for param in function_cursor.get_arguments():
                param_type = param.type.spelling
                param_name = param.spelling
                params.append(f"{param_type} {param_name}")
        
        return return_type, params
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def _parse_function_declaration(declaration: str) -> Tuple[Optional[str], Optional[str], Optional[List[str]]]:
    """
    Parse a function declaration to extract return type, name, and arguments.
    
    Args:
        declaration: Function declaration string
        
    Returns:
        Tuple of (return_type, function_name, argument_list)
    """
    # Use clang to find the function name from the declaration
    temp_file_path = create_temp_file(declaration)
    
    try:
        # Parse the code with clang
        index = clang.cindex.Index.create()
        tu = index.parse(temp_file_path)
        
        # Find the function declaration
        for cursor in tu.cursor.walk_preorder():
            if cursor.kind == CursorKind.FUNCTION_DECL:
                function_name = cursor.spelling
                # Now use clang to get the details
                return_type, args = _parse_function_with_clang(declaration, function_name)
                return return_type, function_name, args
        
        # If we didn't find a function declaration, return None
        return None, None, None
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def _generate_proxy_name(function_name: str) -> str:
    """Generate a proxy function name based on the original name and its hash
    
    Args:
        function_name: The original function name
        
    Returns:
        A proxy name like "original_name_XXXXXXXX"
    """
    # Generate a short hash of the function name
    hash_obj = hashlib.md5(function_name.encode())
    # Take the first 8 characters of the hex digest
    hash_str = hash_obj.hexdigest()[:8].upper()
    
    return f"{function_name}_{hash_str}"


def create_proxy_definitions(functions: Dict[str, Dict], verbose: bool = False) -> Tuple[List[str], Dict[str, str]]:
    """Create proxy function definitions for all functions
    
    Args:
        functions: Dictionary of functions (name -> function info)
        verbose: Whether to print verbose output
        
    Returns:
        Tuple of (list of proxy function definitions, mapping of original function names to proxy names)
    """
    if verbose:
        print("Creating function proxies using clang...")
    
    # Hold all proxy function definitions
    proxy_functions = []
    
    # Map original function names to proxy names
    proxy_names = {}
    
    # Only skip actual main function, nothing else
    skip_functions = ["main"]
    
    for func_name, func_info in functions.items():
        if verbose:
            print(f"Function {func_name} has keys: {list(func_info.keys())}")
            
        # Skip the actual main function, but process everything else
        if func_name.lower() == "main":
            if verbose:
                print(f"Skipping proxy for {func_name} - main function")
            continue
            
        # Use function text to extract information
        if 'text' not in func_info:
            if verbose:
                print(f"Skipping proxy for {func_name} - missing function text")
            continue
            
        # Parse the function declaration to get return type, name, and arguments
        function_text = func_info['text']
        
        # First try to parse the function using _parse_function_with_clang
        try:
            return_type, args = _parse_function_with_clang(function_text, func_name)
            
            if return_type is None or args is None:
                if verbose:
                    print(f"Skipping proxy for {func_name} - couldn't parse function with clang")
                continue
                
        except Exception as e:
            if verbose:
                print(f"Error parsing function {func_name}: {e}")
            continue
        
        # Determine if this is a void function - case insensitive check
        is_void = return_type.lower() == "void" or return_type.upper() == "VOID"
        
        if verbose:
            print(f"Function {func_name} return type: {return_type}, is_void: {is_void}")
        
        # Generate proxy name and store mapping
        proxy_name = _generate_proxy_name(func_name)
        proxy_names[func_name] = proxy_name
        
        # Extract parameter names from args
        arg_names = []
        for arg in args:
            # Try to find the parameter name in the argument string
            param_parts = arg.split()
            if param_parts:
                # Get the last part as the name (may contain array brackets)
                last_part = param_parts[-1]
                # Remove any array brackets
                name = last_part.split('[')[0]
                arg_names.append(name)
            else:
                # If we can't parse the argument, use a placeholder
                arg_names.append(f"arg{len(arg_names)}")
        
        # Start with function signature - EXACTLY as it appears in the original
        proxy_definition = f"{return_type} {proxy_name}({', '.join(args if args else ['void'])}) {{"
        
        # Add function body that calls the original function
        if is_void:
            # For void functions (lowercase void or uppercase VOID), don't use return
            proxy_definition += f"\n    {func_name}({', '.join(arg_names)});\n}}"
        else:
            proxy_definition += f"\n    return {func_name}({', '.join(arg_names)});\n}}"
        
        if verbose:
            print(f"Created proxy for {func_name} -> {proxy_name}")
            print(f"  Proxy definition: {proxy_definition}")
        
        proxy_functions.append(proxy_definition)
    
    if verbose:
        print(f"Created {len(proxy_functions)} proxy functions in total")
    
    return proxy_functions, proxy_names


def find_function_calls_with_clang(code: str, functions: List[str], verbose: bool = False) -> Dict[str, List[Tuple[int, int]]]:
    """
    Find all function calls in the code using clang
    
    Args:
        code: C code to search
        functions: List of function names to find
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary mapping function names to lists of (start, end) positions for each call
    """
    # Create a set of function names for faster lookup
    function_set = set(functions)
    
    # Create a temporary file to hold the code
    temp_file_path = create_temp_file(code)
    
    try:
        # Parse the code with clang
        index = clang.cindex.Index.create()
        tu = index.parse(temp_file_path)
        
        # Dictionary to hold function call positions
        call_positions = {func: [] for func in functions}
        
        # Find all function call expressions
        for cursor in tu.cursor.walk_preorder():
            if cursor.kind == CursorKind.CALL_EXPR:
                called_func_name = cursor.spelling
                
                # If this is one of the functions we're looking for
                if called_func_name in function_set:
                    # Get the exact source range from tokens
                    tokens = list(cursor.get_tokens())
                    if tokens:
                        # Find the function name and opening parenthesis
                        for i, token in enumerate(tokens):
                            if token.spelling == called_func_name and i + 1 < len(tokens) and tokens[i+1].spelling == '(':
                                start_pos = token.extent.start.offset
                                # Find the closing parenthesis which marks the end of the call
                                end_pos = None
                                paren_count = 0
                                for j in range(i+1, len(tokens)):
                                    if tokens[j].spelling == '(':
                                        paren_count += 1
                                    elif tokens[j].spelling == ')':
                                        paren_count -= 1
                                        if paren_count == 0:
                                            end_pos = tokens[j].extent.end.offset
                                            break
                                
                                if end_pos:
                                    call_positions[called_func_name].append((start_pos, end_pos))
                                break
        
        if verbose:
            for func, positions in call_positions.items():
                if positions:
                    print(f"Found {len(positions)} calls to function {func}")
        
        return call_positions
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def apply_reference_proxying(code: str, functions: Dict[str, Dict], verbose: bool = False) -> Tuple[str, List[str]]:
    """
    Apply reference proxying to the given code
    
    Args:
        code: C code to modify
        functions: Dictionary of functions (name -> function info)
        verbose: Whether to print verbose output
        
    Returns:
        Tuple of (modified code, list of proxy function definitions)
    """
    if verbose:
        print("Applying reference proxying...")
    
    # Create proxy function definitions and get mapping
    proxy_definitions, proxy_mapping = create_proxy_definitions(functions, verbose)
    
    # If no proxies were created, return the original code
    if not proxy_definitions:
        if verbose:
            print("No proxy functions created, returning original code")
        return code, []
    
    # Find all function calls in the code and get their positions
    function_calls = find_function_calls_with_clang(code, list(proxy_mapping.keys()), verbose)
    
    # Apply replacements in reverse order to avoid messing up positions
    result = code
    for func_name, call_positions in function_calls.items():
        # Skip if we don't have a proxy for this function
        if func_name not in proxy_mapping:
            continue
            
        # Get the proxy name
        proxy_name = proxy_mapping[func_name]
        
        # Replace all calls in reverse order
        for start, end in sorted(call_positions, reverse=True):
            # Replace the function name with the proxy name
            called_func = result[start:end]
            if called_func.startswith(func_name):
                # Replace function name but keep the rest of the call
                proxied_call = proxy_name + called_func[len(func_name):]
                result = result[:start] + proxied_call + result[end:]
    
    return result, proxy_definitions 