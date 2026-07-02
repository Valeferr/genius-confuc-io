# ConfuC-IO Language Specifications

ConfuC-IO is an esoteric programming language intentionally designed to be confusing. Every keyword, type, and operator has a misleading name that recalls concepts entirely different from its actual function.

## Program Structure

Every ConfuC-IO program must begin with the entry point declaration and end with a return value:

```
Float side {] [
    <instructions>
    * 0
)
```

- `Float side {] [` is the equivalent of `int main()` in C.
- `* 0` is the equivalent of `return 0`.
- `)` closes the main block.

## Type System

Type names are deliberately inverted:

| ConfuC-IO Type | Actual Meaning | Example |
|---|---|---|
| `Float` | Integer number | `Float x @ 5` |
| `int` | Text string | `int msg @ "hello"` |
| `String` | Decimal number | `String pi @ 3.14` |
| `While` | Boolean | `While flag @ 1` |

## Assignment Operator

Assignment uses the `@` symbol instead of `=`:

```
Float x @ 10
int name @ "Mario"
```

## Arithmetic Operators

| ConfuC-IO Symbol | Actual Operation | Example | Equivalent |
|---|---|---|---|
| `/` | Addition | `x / y` | `x + y` |
| `~` | Subtraction | `x ~ y` | `x - y` |
| `Bool` | Multiplication | `x Bool y` | `x * y` |
| `+` | Division | `x + y` | `x / y` |

## Comparison Operators

| ConfuC-IO Symbol | Actual Operation |
|---|---|
| `@@` | Equal (`==`) |
| `!@` | Not equal (`!=`) |
| `=` | Greater than (`>`) |
| `#` | Less than (`<`) |

## Delimiters

Delimiters are inverted compared to conventional languages:

| Usage | Conventional | ConfuC-IO |
|---|---|---|
| Condition opening | `(` | `{` |
| Condition closing | `)` | `]` |
| Block opening | `{` | `[` |
| Block closing | `}` | `)` |

## Control Structures

### If (keyword: `func`)

```
func {condition] [
    <instructions>
)
```

### While (keyword: `return`)

```
return {condition] [
    <instructions>
)
```

### For (keyword: `if`)

```
if {Float i @ 0; i # 10; i @ i / 1] [
    <instructions>
)
```

## Input/Output

### Print (keyword: `FileInputStream`)

Prints a value to the screen:

```
FileInputStream{"Hello world"]
FileInputStream{variable]
```

### Input (keyword: `deleteSystem32`)

Reads a value from the user and assigns it to the specified variable:

```
deleteSystem32{variable_name]
```

## Value Return (keyword: `*`)

```
* 0
* result
```

## Comments

Comments begin with the `È` character:

```
È This is a comment
Float x @ 42  È Also an inline comment
```

## Complete Example: Calculator

```
Float side {] [
    Float continue @ 1

    return {continue = 0] [
        FileInputStream{"=== CALCULATOR ==="]
        FileInputStream{"1 Addition"]
        FileInputStream{"2 Subtraction"]
        FileInputStream{"0 Exit"]

        Float choice @ 0
        deleteSystem32{choice]

        Float a @ 0
        Float b @ 0
        Float result @ 0

        func {choice @@ 0] [
            FileInputStream{"Goodbye!"]
            continue @ 0
        )

        func {choice @@ 1] [
            FileInputStream{"First number: "]
            deleteSystem32{a]
            FileInputStream{"Second number: "]
            deleteSystem32{b]
            result @ a / b
            FileInputStream{"Result: "]
            FileInputStream{result]
        )

        func {choice @@ 2] [
            FileInputStream{"First number: "]
            deleteSystem32{a]
            FileInputStream{"Second number: "]
            deleteSystem32{b]
            result @ a ~ b
            FileInputStream{"Result: "]
            FileInputStream{result]
        )
    )

    * 0
)
```
