"""
Code Analysis Module - Extracts and analyzes C code structures
"""

import re
from typing import List, Dict, Set, Tuple, Any
import random


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
    
    # First, compact all include statements (remove blank lines between them)
    include_pattern = r'#include\s+[<"].*[>"]\s*'
    includes = [m.group(0) for m in re.finditer(include_pattern, result_code)]
    
    if includes:
        # Remove all existing includes
        for include in includes:
            result_code = result_code.replace(include, '')
        
        # Clean up any excessive newlines created by removing includes
        result_code = re.sub(r'\n{2,}', '\n', result_code)
        
        # Add required headers if not present
        for header in required_headers:
            if not any(header in include for include in includes):
                if verbose:
                    print(f"Adding {header} include for required functions")
                includes.append(f"#include {header}")
        
        # Insert all includes at the beginning, with no blank lines between them
        result_code = '\n'.join(includes) + '\n' + result_code.lstrip()
    else:
        # No includes found, add at the beginning
        for header in required_headers:
            if verbose:
                print(f"Adding {header} include for required functions")
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


def extract_function_declarations(code: str, verbose: bool = False) -> List[Dict]:
    """Extract function declarations (prototypes) from the code
    
    Args:
        code: The C code to process
        verbose: Whether to print verbose output
        
    Returns:
        List of function declarations with positions
    """
    # Pattern for function declarations (not definitions)
    # This needs to match declarations like:
    # VOID Function(PVOID Param);
    # int Function(int a, int b);
    # static char* Function(void* data, size_t len) OPTIONAL;
    # _Noreturn void Function(void);
    # etc.
    
    declaration_pattern = r'((?:extern|static|inline|_Noreturn)?\s*(?:VOID|void|BOOL|INT|int|DWORD|PVOID|LPVOID|HANDLE|ULONG|NTSTATUS|SIZE_T|HRESULT|char\s*\*|wchar_t\s*\*|PCHAR|PWCHAR|LPCSTR|LPWSTR|LPSTR|WCHAR|CHAR|BYTE|PBYTE|WORD|DWORD|QWORD|SHORT|USHORT|LONG|ULONG|LONGLONG|ULONGLONG|float|double|FLOAT|DOUBLE)[\s\*]+)(\w+)(\s*\([^;{]*\);)'
    
    declarations = []
    
    for match in re.finditer(declaration_pattern, code):
        return_type = match.group(1).strip()
        function_name = match.group(2).strip()
        parameters = match.group(3).strip()
        
        declaration = match.group(0).strip()
        
        declarations.append({
            'name': function_name,
            'return_type': return_type,
            'parameters': parameters,
            'declaration': declaration,
            'start': match.start(),
            'end': match.end()
        })
    
    if verbose:
        print(f"Extracted {len(declarations)} function declarations")
    
    return declarations


def extract_functions(code: str, verbose: bool = False) -> Dict[str, Dict]:
    """Extract function declarations and definitions from the code
    
    Args:
        code: The C code to process
        verbose: Whether to print verbose output
    
    Returns:
        Dictionary of function information with keys:
            - name: Function name
            - declaration: Function declaration
            - text: Full function text
            - start: Start position in code
            - end: End position in code
    """
    functions = {}
    
    # Define a more comprehensive function pattern that captures various return types and attributes
    function_pattern = r'((?:_Noreturn\s+)?(?:VOID|void|static|inline|BOOL|INT|int|DWORD|PVOID|LPVOID|HANDLE|ULONG|NTSTATUS|SIZE_T|HRESULT|char\s*\*|wchar_t\s*\*|PCHAR|PWCHAR|LPCSTR|LPWSTR|LPSTR|WCHAR|CHAR|BYTE|PBYTE|WORD|DWORD|QWORD|SHORT|USHORT|LONG|ULONG|LONGLONG|ULONGLONG|float|double|FLOAT|DOUBLE)[\s\*]+)(\w+)(\s*\([^{]*\{)'
    
    # Find all functions in the code
    for match in re.finditer(function_pattern, code, re.MULTILINE | re.DOTALL):
        # Extract function name and declaration
        return_type = match.group(1).strip()
        name = match.group(2).strip()
        params = match.group(3).strip()
        
        # Check for _Noreturn attribute
        is_noreturn = '_Noreturn' in return_type
        if is_noreturn and verbose:
            print(f"Found _Noreturn attribute for {name}")
        
        # Find the end of the function (matching closing brace)
        start_pos = match.start()
        current_pos = match.end()
        brace_count = 1  # We've already found the opening brace
        
        while brace_count > 0 and current_pos < len(code):
            char = code[current_pos]
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            current_pos += 1
        
        if brace_count > 0:
            # Function end not found, code might be incomplete
            continue
        
        # Extract the full function text
        function_text = code[start_pos:current_pos].strip()
        
        # Store the function information
        functions[name] = {
            'name': name,
            'declaration': f"{return_type} {name}{params}",
            'text': function_text,
            'start': start_pos,
            'end': current_pos
        }
    
    if verbose:
        print(f"Extracted {len(functions)} functions")
        for name in functions:
            print(f"  - {name}")
    
    return functions


def analyze_function_dependencies(functions: Dict[str, Dict], verbose: bool = False) -> Dict[str, List[str]]:
    """Analyze function dependencies by looking for function calls within function bodies
    
    Args:
        functions: Dictionary of functions (name -> function info)
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary mapping function names to lists of dependencies
    """
    dependencies = {}
    function_names = list(functions.keys())
    
    # For each function, look for calls to other functions
    for name, func_info in functions.items():
        function_text = func_info['text']
        dependencies[name] = []
        
        # Look for calls to other functions
        for other_name in function_names:
            # Skip self-references
            if other_name == name:
                continue
            
            # Check if the function calls the other function
            # This is a simple check, more sophisticated analysis would be needed for complex code
            pattern = r'\b' + re.escape(other_name) + r'\s*\('
            if re.search(pattern, function_text):
                dependencies[name].append(other_name)
    
    if verbose:
        print("Function dependencies:")
        for name, deps in dependencies.items():
            if deps:
                print(f"  {name} depends on: {', '.join(deps)}")
            else:
                print(f"  {name} depends on: none")
    
    return dependencies


def depends_on(func1: str, func2: str, dependencies: Dict[str, List[str]]) -> bool:
    """Check if func1 depends on func2 directly or indirectly
    
    Args:
        func1: First function name
        func2: Second function name
        dependencies: Dictionary mapping function names to lists of dependencies
        
    Returns:
        True if func1 depends on func2, False otherwise
    """
    if func2 in dependencies.get(func1, []):
        return True
    
    for dependency in dependencies.get(func1, []):
        if depends_on(dependency, func2, dependencies):
            return True
    
    return False


def extract_code_sections(code: str, functions: Dict[str, Dict], declarations: List[Dict], globals_info: List[Dict], verbose: bool = False) -> Dict[str, str]:
    """Extract different sections of the code for separate processing
    
    Args:
        code: The C code to process
        functions: Dictionary of functions (name -> function info)
        declarations: List of function declarations
        globals_info: List of global variable declarations
        verbose: Whether to print verbose output
        
    Returns:
        Dictionary of code sections
    """
    sections = {
        'includes': '',      # Include statements
        'globals': '',       # Global variables
        'remaining': ''      # Everything else
    }
    
    # First, extract includes
    include_pattern = r'#include\s+[<"].*[>"]\s*'
    includes = []
    for match in re.finditer(include_pattern, code):
        includes.append((match.start(), match.end(), match.group(0)))
    
    # Sort includes by position
    includes.sort(key=lambda x: x[0])
    
    # Concatenate all includes
    for start_pos, end_pos, include_text in includes:
        sections['includes'] += include_text + '\n'
    
    # Next, extract globals
    global_text = ''
    for global_var in globals_info:
        global_text += code[global_var['start']:global_var['end']] + '\n'
    sections['globals'] = global_text
    
    # Now, extract everything else that's not a function or include
    remaining_text = ''
    pos = 0
    
    # Sort all includes, globals, and functions by position
    all_items = []
    for start_pos, end_pos, _ in includes:
        all_items.append(('include', start_pos, end_pos))
    
    for global_var in globals_info:
        all_items.append(('global', global_var['start'], global_var['end']))
    
    for _, func_info in functions.items():
        all_items.append(('function', func_info['start'], func_info['end']))
    
    for declaration in declarations:
        all_items.append(('declaration', declaration['start'], declaration['end']))
    
    # Sort by start position
    all_items.sort(key=lambda x: x[1])
    
    # Extract remaining text between items
    for item_type, start_pos, end_pos in all_items:
        if pos < start_pos:
            chunk = code[pos:start_pos].strip()
            if chunk:
                remaining_text += chunk + '\n'
        pos = max(pos, end_pos)
    
    # Add any remaining text after the last item
    if pos < len(code):
        chunk = code[pos:].strip()
        if chunk:
            remaining_text += chunk + '\n'
    
    sections['remaining'] = remaining_text
    
    return sections


def remove_empty_lines(code: str, verbose: bool = False) -> str:
    """Remove empty or whitespace-only lines from the code
    
    Args:
        code: The C code to process
        verbose: Whether to print verbose output
    
    Returns:
        Code with empty lines removed
    """
    original_size = len(code)
    original_line_count = code.count('\n') + 1
    
    # Split by line and remove all empty lines
    lines = code.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    
    # Join the lines back together with no empty lines
    final_code = '\n'.join(non_empty_lines)
    
    if verbose:
        removed_lines = original_line_count - (final_code.count('\n') + 1)
        print(f"Removed {removed_lines} empty lines ({removed_lines/original_line_count*100:.2f}% of total lines)")
    
    return final_code


def scramble_functions(functions: Dict[str, Dict], dependencies: Dict[str, List[str]], verbose: bool = False) -> List[Dict]:
    """Scramble the order of functions while respecting dependencies
    
    Args:
        functions: Dictionary of functions (name -> function info)
        dependencies: Dictionary of function dependencies
        verbose: Whether to print verbose output
        
    Returns:
        List of functions in scrambled order
    """
    function_names = list(functions.keys())
    
    # Create a list to hold the sorted functions
    sorted_functions = []
    
    # Keep track of which functions have been added
    added = set()
    
    # Helper function to add a function and its dependencies
    def add_function_with_deps(func_name):
        # Check if already added
        if func_name in added:
            return
        
        # First add dependencies
        for dep in dependencies.get(func_name, []):
            add_function_with_deps(dep)
        
        # Then add the function itself
        if func_name not in added:
            sorted_functions.append(functions[func_name])
            added.add(func_name)
            if verbose:
                print(f"Added {func_name} to sorted functions")
    
    # Add functions in a way that respects dependencies
    while len(added) < len(function_names):
        # Pick a random function that hasn't been added yet
        remaining = [f for f in function_names if f not in added]
        next_func = random.choice(remaining)
        
        # Add it with its dependencies
        add_function_with_deps(next_func)
    
    return sorted_functions


def extract_global_variables(code: str, functions: Dict[str, Dict], declarations: List[Dict], verbose: bool = False) -> List[Dict]:
    """Extract global variable declarations from the code
    
    Args:
        code: The C code to process
        functions: Dictionary of functions (name -> function info)
        declarations: List of function declarations
        verbose: Whether to print verbose output
        
    Returns:
        List of global variable declarations with positions
    """
    global_vars = []
    
    # First, process the critical variables that MUST be preserved in the correct order
    
    # AgentConfig declaration
    agent_config_match = re.search(r'SEC_DATA\s+BYTE\s+AgentConfig\[\]\s*=\s*CONFIG_BYTES\s*;', code)
    if agent_config_match:
        if verbose:
            print("Found AgentConfig declaration")
        global_vars.append({
            'name': 'AgentConfig',
            'text': agent_config_match.group(0),
            'start': agent_config_match.start(),
            'end': agent_config_match.end()
        })
    
    # Instance declaration
    instance_match = re.search(r'(?:SEC_DATA)?\s+PINSTANCE\s+Instance\s*=\s*(?:{\s*0\s*})?;', code)
    if instance_match:
        if verbose:
            print("Found Instance declaration")
        global_vars.append({
            'name': 'Instance',
            'text': instance_match.group(0),
            'start': instance_match.start(),
            'end': instance_match.end()
        })
    
    # Extract all other global variables
    global_pattern = r'(?:SEC_DATA|extern|static|const)?\s*(?:\w+)(?:\s*\*)?\s+(?:\w+)(?:\[\])?\s*(?:=\s*[^;]+)?;'
    
    for match in re.finditer(global_pattern, code):
        start_pos = match.start()
        end_pos = match.end()
        
        # Skip if this global is inside a function
        if is_inside_any_function(start_pos, functions) or is_inside_any_declaration(start_pos, declarations):
            continue
        
        # Extract the variable name to check for duplicates
        var_text = match.group(0)
        name_match = re.search(r'(?:\w+)(?:\s*\*)?\s+(\w+)', var_text)
        if name_match:
            var_name = name_match.group(1)
            
            # Skip if this is a duplicate or a critical variable we already added
            if any(var['name'] == var_name for var in global_vars):
                continue
                
            global_vars.append({
                'name': var_name,
                'text': var_text,
                'start': start_pos,
                'end': end_pos
            })
    
    return global_vars


def is_inside_any_function(pos: int, functions: Dict[str, Dict]) -> bool:
    """Check if a position is inside any function
    
    Args:
        pos: Position to check
        functions: Dictionary of functions
        
    Returns:
        True if position is inside a function, False otherwise
    """
    for _, func_info in functions.items():
        if func_info['start'] <= pos <= func_info['end']:
            return True
    return False


def is_inside_any_declaration(pos: int, declarations: List[Dict]) -> bool:
    """Check if a position is inside any function declaration
    
    Args:
        pos: Position to check
        declarations: List of function declarations
        
    Returns:
        True if position is inside a declaration, False otherwise
    """
    for decl in declarations:
        if decl['start'] <= pos <= decl['end']:
            return True
    return False 