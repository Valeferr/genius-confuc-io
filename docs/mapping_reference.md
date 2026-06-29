# Confuc-IO Language Mapping Reference

This document provides the complete mapping from conventional programming constructs to Confuc-IO equivalents as specified in the proposal.

## Keyword Mappings

| Conventional | Confuc-IO | Description |
|-------------|-----------|-------------|
| `if` | `func` | Conditional statement |
| `func` | `for` | Function keyword maps to for |
| `while` | `return` | While loop |
| `for` | `if` | For loop |
| `return` | `*` | Return statement |

## Type Mappings

| Conventional | Confuc-IO | Description |
|-------------|-----------|-------------|
| `int` | `Float` | Integer type |
| `string` | `int` | String type |
| `float` | `String` | Floating-point type |
| `bool` | `While` | Boolean type |

## Operator Mappings

| Conventional | Confuc-IO | Operation |
|-------------|-----------|-----------|
| `+` | `/` | Addition |
| `-` | `~` | Subtraction |
| `/` | `+` | Division |
| `*` | `Bool` | Multiplication |
| `>` | `=` | Greater than |
| `<` | `#` | Less than |
| `==` | `@@` | Equality |
| `=` | `@` | Assignment |

## Delimiter Mappings

| Conventional | Confuc-IO | Opens | Closes |
|-------------|-----------|-------|--------|
| `(` | `{` | Opening parenthesis | — |
| `)` | `]` | — | Closing parenthesis |
| `[` | `(` | Opening bracket | — |
| `]` | `}` | — | Closing bracket |
| `{` | `[` | Opening brace | — |
| `}` | `)` | — | Closing brace |

### Delimiter Mapping Examples

```
Conventional: function(arg)  → Confuc-IO: function{arg]
Conventional: array[index]   → Confuc-IO: array(index}
Conventional: block { code } → Confuc-IO: block [ code )
```

## Special Symbols

| Symbol | Purpose |
|--------|---------|
| `È` | Comment indicator |

## I/O Functions (Confusingly Named!)

| Conventional | Confuc-IO | Description |
|-------------|-----------|-------------|
| `print` / `printf` | `FileInputStream` | Output/print to console (sounds like input!) |
| `scanf` / `input` | `deleteSystem32` | Read input from user (sounds destructive!) |

### Format String Mappings (Documentation Only!)

> [!IMPORTANT]
> **These format string mappings are CONCEPTUAL ONLY** for understanding the type confusion. The actual compiler implementation uses **real printf format strings** (`%d`, `%f`, `%lf`, `%s`) in the generated LLVM IR to ensure C stdlib compatibility. See [Design Rationale](file:///Users/ritopla/Desktop/ILP/Confuc-IO/docs/development/design_rationale.md#real-printf-formats) for details.

The conceptual format string mappings that match the confusing type names:

| Conventional Format | Confuc-IO Conceptual | Type Mapping |
|:-------------------|:-----------------|:------|
| `%d` | `%f` | Integer I/O (Float type → actually int) |
| `%f` | `%ff` | Float output (String type → actually float) |
| `%lf` | `%fff` | Float input (String type → actually float) |
| `%s` | `%ffff` | String I/O (int type → actually string) |

**Note:** These mappings exist in the language specification for educational purposes but are **not used in practice**. The code generator always uses standard printf formats to maintain compatibility with the C standard library.

### I/O Examples

```confuc-io
Float side {] [
    Float num @ 0
    
    È Output a value (FileInputStream is print!)
    FileInputStream{42]
    
    È Get input (deleteSystem32 is input!)
    deleteSystem32{num]
    
    È Print the input
    FileInputStream{num]
    
    * 0
)
```

## Main Function

The entry point of a Confuc-IO program **must** be named `side` (not `main`).

```confuc-io
side [
    È This is the main function
    Float x @ 42
)
```

## Example Translation

### Conventional Code
```c
int main() {
    int x = 5;
    int y = 3;
    int z = x + y;
    if (z > 8) {
        y = y - 2;
    }
    return 0;
}
```

### Confuc-IO Code
```confuc-io
Float side {] [
    Float x @ 5          È Declare int x = 5
    Float y @ 3          È Declare int y = 3
    Float z @ x / y      È z = x + y (/ is addition)
    func {z = 8] [       È if (z > 8) { (= is greater than)
        y @ y ~ 2        È y = y - 2 (~ is subtraction)
    )                    È }
    * 0                  È return 0
)
```

## Scope Rules

- **Single global scope only**
- **No variable shadowing allowed**
- All variables must have unique names throughout the program

## Verification Checklist

When implementing or reviewing code, verify:
- ✓ All keywords use Confuc-IO mappings
- ✓ All types use Confuc-IO type names
- ✓ All operators use Confuc-IO symbols
- ✓ All delimiters are correctly swapped
- ✓ Main function is named `side`
- ✓ No variable shadowing exists
- ✓ Comments use `È` symbol
