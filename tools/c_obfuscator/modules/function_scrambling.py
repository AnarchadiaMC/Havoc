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