#ifndef DEMON_OBFUS_EXAMPLES_H
#define DEMON_OBFUS_EXAMPLES_H

#include <obfuscation/ObfusConfig.h>

/*
 * This file demonstrates practical usage of obfus.h within the Havoc/Demon codebase
 */

/* Example 1: String obfuscation using HIDE_STRING */
/* 
 * Original code:
 * char* message = "This is a sensitive string";
 * printf(message);
 * 
 * Obfuscated code:
 * char* message = HIDE_STRING("This is a sensitive string");
 * printf(message);
 */

/* Example 2: Anti-debugging (automatically deployed) */
/*
 * The anti-debugging protection is built into the obfus.h header 
 * and triggered automatically at runtime.
 */

/* Example 3: Math operations using the virtual machine */
/*
 * Original code:
 * int a = 5;
 * int b = 3;
 * int sum = a + b;
 * int diff = a - b;
 * bool isEqual = (sum == 8);
 * 
 * Obfuscated code:
 * int a = 5;
 * int b = 3;
 * int sum = VM_ADD(a, b);
 * int diff = VM_SUB(a, b);
 * bool isEqual = VM_EQU(sum, 8);
 */

/* Example 4: Control flow using VM_IF/VM_ELSE */
/*
 * Original code:
 * if (sum == 8) {
 *     printf("The sum is 8");
 * } else {
 *     printf("The sum is not 8");
 * }
 * 
 * Obfuscated code:
 * VM_IF (VM_EQU(sum, 8)) {
 *     printf("The sum is 8");
 * } VM_ELSE {
 *     printf("The sum is not 8");
 * }
 */

/* Example implementation for testing */
static inline void ObfuscationExample() {
    char* hidden_string = HIDE_STRING("This string is hidden from static analysis");
    printf("%s\n", hidden_string);
    
    int result = VM_ADD(5, 7);
    
    VM_IF (VM_EQU(result, 12)) {
        printf(HIDE_STRING("The result is 12\n"));
    } VM_ELSE {
        printf(HIDE_STRING("The result is not 12\n"));
    }
    
    free(hidden_string); // Remember to free memory allocated by HIDE_STRING
}

#endif /* DEMON_OBFUS_EXAMPLES_H */ 