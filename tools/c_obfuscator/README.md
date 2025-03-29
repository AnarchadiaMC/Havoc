# C Obfuscator

A Python-based tool to obfuscate C code, now using clang for more accurate code analysis.

## Features

1. **String Obfuscation**: Non-XOR, byte-based string obfuscation that replaces string literals with runtime deobfuscation calls.

2. **Method Scrambling**: Rearranges the order of function definitions in the source code while preserving dependencies to make the code harder to follow.

3. **Dependency Analysis**: Uses clang to analyze function call dependencies to ensure the obfuscated code still compiles and runs correctly.

4. **Reference Proxying**: Creates proxy functions for all function calls to add an additional layer of indirection.

## Requirements

- Python 3.6+
- libclang with Python bindings
- clang-format (for code formatting)

## Installation

First, install the required dependencies:

```bash
# On Debian/Ubuntu
apt-get install libclang-dev python3-clang clang-format

# On macOS
brew install llvm && pip install clang

# On Windows
pip install clang
```

Then download the script and make it executable:

```bash
chmod +x c_obfuscator.py
```

## Usage

```bash
python c_obfuscator.py input.c [-o output.c] [-v] [-n]
```

### Arguments

- `input.c` - The input C file to obfuscate
- `-o, --output output.c` - The output file for the obfuscated code (default: `input.c.obf`)
- `-v, --verbose` - Enable verbose output
- `-n, --no-proxying` - Disable reference proxying

### Example

```bash
python c_obfuscator.py test.c -o test_obf.c -v
```

This will:
1. Obfuscate all string literals in the code using a byte-based (addition/subtraction) algorithm
2. Scramble the order of function definitions while respecting dependencies
3. Add proxy functions for indirect function calls
4. Output the obfuscated code to `test_obf.c`

## How It Works

### Clang-based Parsing

The tool uses libclang to parse the C code and accurately extract:
- Function declarations and definitions
- Function call dependencies
- String literals
- Global variables
- Include directives

This provides much more accurate results than the previous regex-based approach.

### String Obfuscation

The tool replaces all string literals with calls to a deobfuscation function. The strings are obfuscated by adding a random key to each character. At runtime, the deobfuscation function reverses this process.

### Method Scrambling

The tool extracts all function definitions from the source code, analyzes their dependencies (which functions call which), and then performs a topological sort to ensure dependencies are respected. Functions that don't depend on each other are randomly reordered to make the code harder to follow.

### Reference Proxying

The tool creates proxy functions for each function in the code and then replaces direct function calls with calls to these proxy functions. This adds an additional layer of indirection, making the code more difficult to analyze.

## Limitations

- Some advanced C code constructs might not be properly handled.
- Method scrambling may not work correctly with complex macros or preprocessor directives.
- Existing code comments are removed during obfuscation.

## License

MIT