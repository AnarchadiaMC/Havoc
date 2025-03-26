#ifndef DEMON_OBFUS_CONFIG_H
#define DEMON_OBFUS_CONFIG_H

/*
 * Configuration wrapper for obfus.h
 * This sets up the obfuscation options for the Havoc Demon agent
 */

/* Enable advanced code protection with VM-based math operations */
#define VIRT 1

/* Enable more powerful control flow obfuscation */
#define CFLOW_V2 1

/* Use better dynamic anti-debugging protection */
#define ANTIDEBUG_V2 1

/* Add fake signatures to confuse detection tools */
#define FAKE_SIGNS 1

/* Include the obfus.h header */
#include <obfuscation/obfus.h>

/* 
 * Usage examples within the codebase:
 *
 * 1. String obfuscation: 
 *    Use HIDE_STRING() to obfuscate string literals
 *    Example: char* hidden = HIDE_STRING("Hidden string");
 *
 * 2. Anti-debug protection:
 *    Built-in, triggered automatically when needed
 *
 * 3. Control flow obfuscation:
 *    Built-in for conditionals and loops
 *
 * 4. Math VM operations (when VIRT=1):
 *    Replace operations with VM_* versions
 *    Example: int result = VM_ADD(5, 3); // 5 + 3
 *    Example: VM_IF (VM_EQU(result, 8)) { ... }
 */

#endif /* DEMON_OBFUS_CONFIG_H */ 