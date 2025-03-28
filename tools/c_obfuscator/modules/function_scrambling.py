"""
Function Scrambling Module - Handles reordering of functions
"""

import random
from typing import List, Dict, Set, Any


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


def scramble_functions(functions: List[Dict[str, Any]], dependencies: Dict[str, Set[str]], verbose: bool = False) -> List[Dict[str, Any]]:
    """Scramble functions while respecting dependencies
    
    Args:
        functions: List of functions to scramble
        dependencies: Dictionary mapping function names to sets of dependencies
        verbose: Whether to print verbose output
        
    Returns:
        List of scrambled functions
    """
    if verbose:
        print("Sorting and scrambling functions...")
        
    sorted_function_names = topological_sort(functions, dependencies, verbose)
    
    # Group functions that can be scrambled together
    groups = []
    current_group = []
    
    for function_name in sorted_function_names:
        function = next((f for f in functions if f['name'] == function_name), None)
        if function:
            if not current_group or all(not depends_on(function_name, f['name'], dependencies) for f in current_group):
                current_group.append(function)
            else:
                groups.append(current_group)
                current_group = [function]
    
    if current_group:
        groups.append(current_group)
    
    # Shuffle each group internally
    final_functions = []
    for group in groups:
        random.shuffle(group)
        final_functions.extend(group)
    
    # Ensure all functions are included
    function_names_included = {f['name'] for f in final_functions}
    missing_functions = [f for f in functions if f['name'] not in function_names_included]
    final_functions.extend(missing_functions)
    
    return final_functions


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