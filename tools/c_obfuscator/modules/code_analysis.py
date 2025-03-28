"""
Code Analysis Module - Extracts and analyzes C code structures
"""

import re
from typing import List, Dict, Set, Tuple, Any


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
    result_code = code
    
    for header in required_headers:
        if f"#include {header}" not in result_code:
            if verbose:
                print(f"Adding {header} include for required functions")
            includes = list(re.finditer(r'#include\s+[<"].*[>"]\s*', result_code))
            if includes:
                last_include = includes[-1]
                insertion_point = last_include.end()
                result_code = result_code[:insertion_point] + f"\n#include {header}" + result_code[insertion_point:]
            else:
                # No includes found, add at the beginning
                result_code = f"#include {header}\n" + result_code
    
    return result_code


def remove_comments(code: str, verbose: bool = False) -> str:
    """Remove all comments from the C code
    
    Args:
        code: Code to remove comments from
        verbose: Whether to print verbose output
        
    Returns:
        Code with comments removed
    """
    if verbose:
        print("Removing comments...")
        
    original_size = len(code)
    
    # State variables for parsing
    in_string = False
    in_char = False
    in_line_comment = False
    in_block_comment = False
    escape_next = False
    result = []
    
    i = 0
    while i < len(code):
        # Handle string literals
        if in_string:
            if escape_next:
                escape_next = False
                result.append(code[i])
            elif code[i] == '\\':
                escape_next = True
                result.append(code[i])
            elif code[i] == '"':
                in_string = False
                result.append(code[i])
            else:
                result.append(code[i])
            i += 1
            continue
            
        # Handle character literals
        if in_char:
            if escape_next:
                escape_next = False
                result.append(code[i])
            elif code[i] == '\\':
                escape_next = True
                result.append(code[i])
            elif code[i] == "'":
                in_char = False
                result.append(code[i])
            else:
                result.append(code[i])
            i += 1
            continue
            
        # Handle line comments
        if in_line_comment:
            if code[i] == '\n':
                in_line_comment = False
                result.append('\n')  # Keep newlines to preserve line numbering
            i += 1
            continue
            
        # Handle block comments
        if in_block_comment:
            if i < len(code) - 1 and code[i:i+2] == '*/':
                in_block_comment = False
                i += 2
            else:
                # For multi-line comments, keep newlines to preserve line numbers
                if code[i] == '\n':
                    result.append('\n')
                i += 1
            continue
            
        # Check for start of comments
        if i < len(code) - 1:
            if code[i:i+2] == '//':
                in_line_comment = True
                i += 2
                continue
            elif code[i:i+2] == '/*':
                in_block_comment = True
                i += 2
                continue
                
        # Check for start of string/char literals
        if code[i] == '"':
            in_string = True
            result.append(code[i])
        elif code[i] == "'":
            in_char = True
            result.append(code[i])
        else:
            result.append(code[i])
            
        i += 1
            
    cleaned_code = ''.join(result)
    
    # Remove excessive newlines (replace 3+ consecutive newlines with 2)
    cleaned_code = re.sub(r'\n{3,}', '\n\n', cleaned_code)
    
    if verbose:
        new_size = len(cleaned_code)
        removed = original_size - new_size
        print(f"Removed {removed} bytes of comments ({removed / original_size * 100:.2f}%)")
    
    return cleaned_code


def compact_code(code: str, verbose: bool = False) -> str:
    """Compact the code by removing empty lines while preserving general formatting
    
    Args:
        code: Code to compact
        verbose: Whether to print verbose output
        
    Returns:
        Compacted code
    """
    if verbose:
        print("Compacting code by removing empty lines...")
        
    original_size = len(code)
    
    # Remove empty lines - lines with only whitespace
    lines = code.split('\n')
    compacted_lines = []
    
    for line in lines:
        # Keep the line if it contains non-whitespace characters
        if line.strip():
            compacted_lines.append(line)
    
    # Join the lines back together
    compacted_code = '\n'.join(compacted_lines)
    
    if verbose:
        new_size = len(compacted_code)
        removed = original_size - new_size
        print(f"Removed {removed} bytes by eliminating empty lines ({removed / original_size * 100:.2f}%)")
        
    return compacted_code


def extract_string_literals(code: str, verbose: bool = False) -> List[Dict[str, Any]]:
    """Extract string literals from the C code, handling escaped quotes properly
    
    Args:
        code: Code to extract string literals from
        verbose: Whether to print verbose output
        
    Returns:
        List of string literals with positions
    """
    in_string = False
    in_comment = False
    in_line_comment = False
    escape_next = False
    start_index = -1
    
    string_literals = []
    
    i = 0
    while i < len(code):
        # Handle comments
        if not in_string:
            if i < len(code) - 1 and code[i:i+2] == '/*':
                in_comment = True
                i += 2
                continue
            elif i < len(code) - 1 and code[i:i+2] == '//':
                in_line_comment = True
                i += 2
                continue
            elif in_comment and i < len(code) - 1 and code[i:i+2] == '*/':
                in_comment = False
                i += 2
                continue
            elif in_line_comment and code[i] == '\n':
                in_line_comment = False
                i += 1
                continue
            
            if in_comment or in_line_comment:
                i += 1
                continue
        
        # Handle string literals
        if not in_string and code[i] == '"':
            in_string = True
            start_index = i
            i += 1
            continue
        
        if in_string:
            if escape_next:
                escape_next = False
            elif code[i] == '\\':
                escape_next = True
            elif code[i] == '"':
                in_string = False
                # Add if it's not a trivial string like "" or " "
                if i - start_index > 2:
                    string_literals.append({
                        'text': code[start_index:i+1],
                        'start': start_index,
                        'end': i+1
                    })
        
        i += 1
    
    # Filter out very small strings or empty strings
    string_literals = [s for s in string_literals if len(s['text']) > 3]
    
    if verbose:
        print(f"Extracted {len(string_literals)} string literals")
    
    return string_literals


def extract_function_declarations(code: str, verbose: bool = False) -> List[Dict[str, Any]]:
    """Extract function declarations for proper dependency tracking
    
    Args:
        code: Code to extract function declarations from
        verbose: Whether to print verbose output
        
    Returns:
        List of function declarations with positions
    """
    # This regex matches C function declarations (prototypes)
    decl_pattern = r'((?:[\w\*\s]+)\s+[\w\*]+\s*\([^)]*\)\s*;)'
    
    matches = re.finditer(decl_pattern, code)
    
    function_declarations = []
    for match in matches:
        decl_text = match.group(0)
        start_index = match.start()
        end_index = match.end()
        
        # Extract function name
        name_pattern = r'(\w+)\s*\('
        name_match = re.search(name_pattern, decl_text)
        function_name = name_match.group(1) if name_match else "unknown"
        
        function_declarations.append({
            'name': function_name,
            'text': decl_text,
            'start': start_index,
            'end': end_index
        })
    
    if verbose:
        print(f"Extracted {len(function_declarations)} function declarations")
    
    return function_declarations


def extract_functions(code: str, verbose: bool = False) -> List[Dict[str, Any]]:
    """Extract function definitions from the C code
    
    Args:
        code: Code to extract functions from
        verbose: Whether to print verbose output
        
    Returns:
        List of functions with positions
    """
    # Simpler pattern to match function headers
    function_pattern = r'((?:VOID|void|static|inline)\s+)(Demon[A-Za-z]+)(\s*\([^{]*\{)'
    
    # Find all potential function starts
    potential_functions = list(re.finditer(function_pattern, code))
    
    functions = []
    
    # For each potential function, find the matching closing brace
    for i, match in enumerate(potential_functions):
        full_match = match.group(0)
        return_type = match.group(1)
        function_name = match.group(2)
        parameters = match.group(3)
        
        # Skip main function and any function that starts with an underscore
        if function_name == "main" or function_name.startswith("_"):
            continue
            
        start_index = match.start()
        
        # Find the matching closing brace by counting opening and closing braces
        open_braces = 1  # Start with 1 for the opening brace we've already found
        end_index = None
        in_string = False
        in_char = False
        in_comment = False
        in_line_comment = False
        escape_next = False
        
        i = match.end()
        while i < len(code):
            char = code[i]
            
            # Handle string and character literals
            if escape_next:
                escape_next = False
                i += 1
                continue
            
            if char == '\\':
                escape_next = True
                i += 1
                continue
            
            # Handle comments
            if i < len(code) - 1:
                if not in_string and not in_char and not in_comment and not in_line_comment:
                    if code[i:i+2] == '/*':
                        in_comment = True
                        i += 2
                        continue
                    elif code[i:i+2] == '//':
                        in_line_comment = True
                        i += 2
                        continue
            
            if in_comment:
                if i < len(code) - 1 and code[i:i+2] == '*/':
                    in_comment = False
                    i += 2
                else:
                    i += 1
                continue
            
            if in_line_comment:
                if char == '\n':
                    in_line_comment = False
                i += 1
                continue
            
            if not in_string and not in_char and char == '"':
                in_string = True
                i += 1
                continue
            
            if not in_string and not in_char and char == "'":
                in_char = True
                i += 1
                continue
            
            if in_string and char == '"':
                in_string = False
                i += 1
                continue
            
            if in_char and char == "'":
                in_char = False
                i += 1
                continue
            
            # Only count braces if not in string or char literals
            if not in_string and not in_char:
                if char == '{':
                    open_braces += 1
                elif char == '}':
                    open_braces -= 1
                    if open_braces == 0:
                        end_index = i + 1
                        break
            
            i += 1
        
        if end_index is None:
            if verbose:
                print(f"Warning: Could not find closing brace for function {function_name}")
            continue
        
        function_text = code[start_index:end_index]
        
        # Ensure this is actually a function and not a struct/enum definition
        # This checks for typical keywords that might indicate non-function code
        if re.search(r'\b(struct|union|enum|typedef)\b', function_text.split('{')[0]):
            continue
        
        functions.append({
            'name': function_name,
            'text': function_text,
            'start': start_index,
            'end': end_index
        })
    
    if verbose:
        print(f"Extracted {len(functions)} functions")
        for func in functions:
            print(f"  - {func['name']}")
    
    return functions


def analyze_function_dependencies(functions: List[Dict[str, Any]], verbose: bool = False) -> Dict[str, Set[str]]:
    """Analyze function dependencies to ensure correct reordering
    
    Args:
        functions: List of functions to analyze
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary mapping function names to sets of dependencies
    """
    function_dependencies = {}
    
    function_names = [func['name'] for func in functions]
    
    for function in functions:
        name = function['name']
        function_dependencies[name] = set()
        
        # Check which other functions this function calls
        for other_name in function_names:
            if other_name != name:
                # Look for function calls (with word boundaries to avoid partial matches)
                if re.search(r'\b' + re.escape(other_name) + r'\s*\(', function['text']):
                    function_dependencies[name].add(other_name)
    
    if verbose:
        print("Function dependencies:")
        for func, deps in function_dependencies.items():
            print(f"  {func} depends on: {', '.join(deps) if deps else 'none'}")
    
    return function_dependencies


def depends_on(func1: str, func2: str, dependencies: Dict[str, Set[str]]) -> bool:
    """Check if func1 depends on func2 directly or indirectly
    
    Args:
        func1: First function name
        func2: Second function name
        dependencies: Dictionary mapping function names to sets of dependencies
        
    Returns:
        True if func1 depends on func2, False otherwise
    """
    if func2 in dependencies.get(func1, set()):
        return True
    
    for dependency in dependencies.get(func1, set()):
        if depends_on(dependency, func2, dependencies):
            return True
    
    return False


def extract_code_sections(code: str, functions: List[Dict[str, Any]], 
                         function_declarations: List[Dict[str, Any]], verbose: bool = False) -> Dict[str, str]:
    """Extract various sections of the code
    
    Args:
        code: Code to extract sections from
        functions: List of functions
        function_declarations: List of function declarations
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary containing 'includes', 'globals', and 'remaining' sections
    """
    # Find includes section
    includes_pattern = r'#include\s+[<"].*[>"]\s*'
    includes = []
    
    for match in re.finditer(includes_pattern, code):
        includes.append(match.group(0))
    
    includes_section = "\n".join(includes) + "\n"
    
    # Find last include position for further processing
    last_include_pos = 0
    if includes:
        last_include_pos = max(m.end() for m in re.finditer(includes_pattern, code))
    
    # Extract global variables
    globals_pattern = r'(?:extern|static|const)?\s*(?:\w+)\s+(?:\w+)(?:\s*=\s*[^;]+)?;'
    globals_section = ""
    
    for match in re.finditer(globals_pattern, code[last_include_pos:]):
        start_pos = last_include_pos + match.start()
        end_pos = last_include_pos + match.end()
        
        # Make sure this isn't inside a function or declaration
        if not any(func['start'] <= start_pos <= func['end'] for func in functions) and \
           not any(decl['start'] <= start_pos <= decl['end'] for decl in function_declarations):
            globals_section += code[start_pos:end_pos] + "\n"
    
    # Extract remaining non-function code (avoiding duplicates)
    function_ranges = [(f['start'], f['end']) for f in functions]
    remaining_code = ""
    
    pos = last_include_pos + len(globals_section)
    while pos < len(code):
        # Check if current position is inside any function
        inside_function = False
        for start, end in function_ranges:
            if start <= pos < end:
                inside_function = True
                pos = end  # Skip to end of function
                break
        
        if not inside_function:
            remaining_code += code[pos]
            pos += 1
    
    # Clean up excess whitespace
    remaining_code = re.sub(r'\n{3,}', '\n\n', remaining_code)
    
    return {
        'includes': includes_section,
        'globals': globals_section,
        'remaining': remaining_code
    }


def remove_empty_lines(code: str, verbose: bool = False) -> str:
    """Remove empty or whitespace-only lines from the code
    
    Args:
        code: The C code to process
        verbose: Whether to print verbose output
    
    Returns:
        Code with empty lines removed
    """
    original_size = len(code)
    lines = code.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    cleaned_code = '\n'.join(non_empty_lines)
    
    if verbose:
        removed_lines = len(lines) - len(non_empty_lines)
        print(f"Removed {removed_lines} empty lines ({removed_lines/len(lines)*100:.2f}% of total lines)")
    
    return cleaned_code 