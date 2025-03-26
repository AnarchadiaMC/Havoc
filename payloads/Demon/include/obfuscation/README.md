# Obfuscation for Havoc Demon Agents

This directory contains the integration of [obfus.h](https://github.com/DosX-dev/obfus.h) for obfuscating the Havoc Demon agent code during compilation.

## Configuration

The obfuscation is configured in `ObfusConfig.h`, which includes:

- VM-based math operations (VIRT=1)
- Enhanced control flow obfuscation (CFLOW_V2=1)
- Advanced anti-debugging protection (ANTIDEBUG_V2=1)
- Fake signatures to confuse detection tools (FAKE_SIGNS=1)

## How to Use

To use the obfuscation features in your Demon agent code:

1. **String Obfuscation**: 
   ```c
   char* hidden = HIDE_STRING("This string will be hidden in the binary");
   // Remember to free when done
   free(hidden);
   ```

2. **Math Operations Using VM**:
   ```c
   int result = VM_ADD(5, 3); // 5 + 3
   int product = VM_MUL(4, 7); // 4 * 7
   ```

3. **Obfuscated Control Flow**:
   ```c
   VM_IF (VM_EQU(value, 10)) {
       // Code if value == 10
   } VM_ELSE_IF (VM_GTR(value, 10)) {
       // Code if value > 10
   } VM_ELSE {
       // Code if value < 10
   }
   ```

4. **Fake Signatures**: Automatically added during compilation

## Implementation

The obfuscation has been integrated into the build process and is applied when the `ENABLE_OBFUSCATION` flag is defined.

See `ObfusExamples.h` for more usage examples and patterns.

## Benefits

- Strings are hidden from static analysis tools
- Control flow is obfuscated to make reverse engineering harder
- Anti-debugging measures protect against dynamic analysis
- VM-based math operations add complexity to decompilation
- Fake signatures may confuse detection tools 