"""
Function Scrambling Module - Handles reordering of functions
"""

import random
import os
import tempfile
import re
from typing import List, Dict, Set, Any, Optional

try:
    import clang.cindex
    from clang.cindex import CursorKind
    CLANG_AVAILABLE = True
except ImportError:
    CLANG_AVAILABLE = False
    print("Warning: clang.cindex module not available for function scrambling. Using basic sorting.")


def find_function_dependencies_with_clang(code: str, functions: List[str]) -> Dict[str, Set[str]]:
    """
    Use clang to find function dependencies in the code
    
    Args:
        code: C code to analyze
        functions: List of function names to find dependencies for
        
    Returns:
        Dictionary mapping function names to sets of dependency names
    """
    if not CLANG_AVAILABLE:
        return {}
        
    # Create a set of function names for faster lookup
    function_set = set(functions)
    
    # Create a temporary file to hold the code
    with tempfile.NamedTemporaryFile(suffix='.c', delete=False) as temp_file:
        temp_file.write(code.encode('utf-8'))
        temp_file_path = temp_file.name
    
    try:
        # Parse the code with clang
        index = clang.cindex.Index.create()
        tu = index.parse(temp_file_path)
        
        # Map of function names to their dependencies
        dependencies = {func: set() for func in functions}
        
        # First pass: identify all function definitions and their call expressions
        for cursor in tu.cursor.walk_preorder():
            if cursor.kind == CursorKind.FUNCTION_DECL and cursor.is_definition():
                function_name = cursor.spelling
                if function_name in function_set:
                    # Find all function calls within this function
                    called_functions = set()
                    for child in cursor.walk_preorder():
                        if child.kind == CursorKind.CALL_EXPR:
                            called_func = child.spelling
                            if called_func in function_set and called_func != function_name:
                                called_functions.add(called_func)
                    
                    # Add the dependencies
                    dependencies[function_name].update(called_functions)
        
        return dependencies
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


def topological_sort(functions: List[Dict[str, Any]], dependencies: Dict[str, Set[str]], verbose: bool = False) -> List[str]:
    """Sort functions topologically based on dependencies
    
    Args:
        functions: List of functions to sort
        dependencies: Dictionary mapping function names to sets of dependencies
        verbose: Whether to print verbose output
        
    Returns:
        List of function names in sorted order
    """
    # Create a copy of the dependencies
    deps_copy = {name: set(deps) for name, deps in dependencies.items()}
    
    # List to store the sorted function names
    sorted_functions = []
    
    # Set of functions with no dependencies
    no_deps = {name for name, deps in deps_copy.items() if not deps}
    
    while no_deps:
        # Randomly select a function with no dependencies
        func = random.choice(list(no_deps))
        no_deps.remove(func)
        sorted_functions.append(func)
        
        # Remove this function from other functions' dependencies
        for name, deps in list(deps_copy.items()):
            if func in deps:
                deps.remove(func)
                if not deps:
                    no_deps.add(name)
    
    # Check for cyclic dependencies
    if len(sorted_functions) != len(deps_copy):
        if verbose:
            print("Warning: Cyclic dependencies detected, sorting may be incomplete")
        # Add remaining functions in any order
        remaining = set(deps_copy.keys()) - set(sorted_functions)
        sorted_functions.extend(list(remaining))
    
    return sorted_functions


def scramble_functions(functions: Dict[str, Dict], dependencies: Dict[str, List[str]], verbose: bool = False, code: Optional[str] = None) -> List[Dict]:
    """Scramble the order of functions while respecting dependencies
    
    Args:
        functions: Dictionary of functions (name -> function info)
        dependencies: Dictionary of function dependencies
        verbose: Whether to print verbose output
        code: Optional full code for clang-based analysis
        
    Returns:
        List of functions in scrambled order
    """
    # Filter functions to exclude main
    excluded_functions = ["main"]
    function_names = [f for f in list(functions.keys()) if f not in excluded_functions]
    
    if not function_names:
        if verbose:
            print("No functions to scramble")
        return []
    
    # Create a list to hold the sorted functions
    sorted_functions = []
    
    # Keep track of which functions have been added
    added = set()
    
    # If clang is available and code is provided, try to use clang for better dependency analysis
    clang_deps = {}
    if CLANG_AVAILABLE and code:
        if verbose:
            print("Using clang for function dependency analysis")
        clang_deps = find_function_dependencies_with_clang(code, function_names)
        
        if clang_deps and verbose:
            print("Clang detected these dependencies:")
            for func, deps in clang_deps.items():
                if deps:
                    print(f"  {func} depends on: {', '.join(deps)}")
                else:
                    print(f"  {func} depends on: none")
    
    # Merge clang dependencies with existing dependencies if available
    if clang_deps:
        merged_deps = {}
        for func in function_names:
            # Start with existing dependencies
            merged_deps[func] = set(dependencies.get(func, []))
            # Add clang-detected dependencies
            if func in clang_deps:
                merged_deps[func].update(clang_deps[func])
        
        # Convert back to lists for compatibility
        dependencies = {func: list(deps) for func, deps in merged_deps.items()}
    
    # Helper function to add a function and its dependencies
    def add_function_with_deps(func_name):
        # Check if already added
        if func_name in added:
            return
        
        # First add dependencies
        for dep in dependencies.get(func_name, []):
            if dep in function_names:  # Only add dependencies that are in our function list
                add_function_with_deps(dep)
        
        # Then add the function itself
        if func_name not in added and func_name in functions:
            # Detect and skip duplicate globals/variables
            func_content = functions[func_name]['text']
            if re.search(r'^\s*(SEC_DATA|static)\s+.*\s+\w+\s*=\s*', func_content, re.MULTILINE):
                if verbose:
                    print(f"Skipping function with global definitions: {func_name}")
                added.add(func_name)
                return
            
            sorted_functions.append(functions[func_name])
            added.add(func_name)
            if verbose:
                print(f"Added {func_name} to sorted functions")
    
    # Add functions in a way that respects dependencies
    while len(added) < len(function_names):
        # Pick a random function that hasn't been added yet
        remaining = [f for f in function_names if f not in added]
        if not remaining:
            break
        next_func = random.choice(remaining)
        
        # Add it with its dependencies
        add_function_with_deps(next_func)
    
    return sorted_functions


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