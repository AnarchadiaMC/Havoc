# C Obfuscator

A Python-based tool to obfuscate C code.

## Features

1. **String Obfuscation**: Non-XOR, byte-based string obfuscation that replaces string literals with runtime deobfuscation calls.

2. **Method Scrambling**: Rearranges the order of function definitions in the source code while preserving dependencies to make the code harder to follow.

3. **Dependency Analysis**: Analyzes function call dependencies to ensure the obfuscated code still compiles and runs correctly.

## Requirements

- Python 3.6+

## Installation

No special installation is required. Simply download the script and make it executable:

```bash
chmod +x c_obfuscator.py
```

## Usage

```bash
python c_obfuscator.py input.c [-o output.c] [-v]
```

### Arguments

- `input.c` - The input C file to obfuscate
- `-o, --output output.c` - The output file for the obfuscated code (default: `input_obf.c`)
- `-v, --verbose` - Enable verbose output

### Example

```bash
python c_obfuscator.py ../payloads/Demon/src/Demon.c -o ../payloads/Demon/src/demon_obf.c -v
```

This will:
1. Obfuscate all string literals in the code using a byte-based (addition/subtraction) algorithm
2. Scramble the order of function definitions while respecting dependencies
3. Output the obfuscated code to `demon_obf.c`

## How It Works

### String Obfuscation

The tool replaces all string literals with calls to a deobfuscation function. The strings are obfuscated by adding a random key to each character. At runtime, the deobfuscation function reverses this process.

### Method Scrambling

The tool extracts all function definitions from the source code, analyzes their dependencies (which functions call which), and then performs a topological sort to ensure dependencies are respected. Functions that don't depend on each other are randomly reordered to make the code harder to follow.

## Limitations

- The regular expressions used for parsing might not handle all C code constructs perfectly.
- Method scrambling may not work correctly with complex macros or preprocessor directives.
- Existing code comments might be displaced or removed during obfuscation.

## License

MIT