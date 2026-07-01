import re
from lark import Lark



















CONFUCIO_GRAMMAR = r"""
    // Entry point MUST be: Float side {] [ statements... )
    start: "Float" "side" "{" "]" "[" statement* ")"

    ?statement: declaration
              | assignment
              | if_stmt
              | while_stmt
              | for_stmt
              | return_stmt
              | print_stmt
              | input_stmt
              | expression

    // Variable declaration:  TYPE name @ value
    declaration: TYPE CNAME "@" expression

    // Assignment:  name @ value
    assignment: CNAME "@" expression

    // if  (conventional) → func  {condition] [body)
    if_stmt: "func" "{" condition "]" "[" statement* ")"

    // while (conventional) → return {condition] [body)
    while_stmt: "return" "{" condition "]" "[" statement* ")"

    // for  (conventional) → if {init; cond; update] [body)
    for_stmt: "if" "{" (declaration|assignment) ";" condition ";" assignment "]" "[" statement* ")"

    // return (conventional) → *
    return_stmt: "*" expression

    // print (conventional) → FileInputStream{expr]
    print_stmt: "FileInputStream" "{" expression "]"

    // Conditions use Confuc-IO comparison operators
    ?condition: expression (COMPARE_OP expression)? -> condition
    COMPARE_OP: "@@"        // == (equality)
              | "="         // >  (greater than)
              | "#"         // <  (less than)
              | "!@"        // != (inequality) #TODO: abbiamo aggiunto != al linguaggio di confuc-io perché l'LLM non riusciva a generare codice valido senza

    ?expression: math_expr | ESCAPED_STRING

    // Arithmetic operators use Confuc-IO symbols:
    //   /  = addition,  ~  = subtraction,  +  = division,  Bool = multiplication
    ?math_expr: math_expr "/"    term -> add
              | math_expr "~"    term -> sub
              | math_expr "+"    term -> div
              | math_expr "Bool" term -> mul
              | term

    // Grouped expression uses { ] (conventional parentheses are swapped)
    term: NUMBER | CNAME | "{" math_expr "]"

    // User input:  deleteSystem32{var]  (like scanf, modifies the variable)
    input_stmt: "deleteSystem32" "{" CNAME "]"

    // Confuc-IO types (all names intentionally misleading):
    //   Float = int,  int = string,  String = float,  While = bool
    TYPE.10: "Float" | "int" | "String" | "While"

    %import common.CNAME
    %import common.NUMBER
    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS

    // Comments start with È
    COMMENT: /È[^\n]*/
    %ignore COMMENT
"""


def get_parser():
    return Lark(CONFUCIO_GRAMMAR, start='start', parser='lalr')


def sanitize_confucio_code(code: str) -> str:
    """
    Deterministically fix the most common LLM delimiter mistakes before parsing.

    Fixes applied:
    1. deleteSystem32[] or deleteSystem32()  →  deleteSystem32{]
       ([ opens blocks, not parentheses; conventional () are forbidden)

    2. [...] where ] closes a block  →  [...) 
       The algorithm tracks a stack of unmatched openers ({ or [):
         - '{' expects ']' to close it  (condition)
         - '[' expects ')' to close it  (block body)
       If a ']' is found while the current open delimiter is '[', it is
       a block-closer written wrongly — replace it with ')'.
       If a '}' is found, it is always a mistake (conventional brace).
       We auto-replace it with ']' or ')' depending on the stack.

    This sanitizer is called automatically before syntax validation so the
    LLM does not need to be perfectly reliable on these structural details.
    """

    code = re.sub(r'\bdeleteSystem32\[([a-zA-Z0-9_]+)\]', r'deleteSystem32{\1]', code)
    code = re.sub(r'\bdeleteSystem32\(([a-zA-Z0-9_]+)\)', r'deleteSystem32{\1]', code)


    result = []
    stack = []

    for ch in code:
        if ch == '{':
            stack.append('{')
            result.append(ch)
        elif ch == '[':
            stack.append('[')
            result.append(ch)
        elif ch == ']':
            if stack and stack[-1] == '[':

                stack.pop()
                result.append(')')
            else:

                if stack and stack[-1] == '{':
                    stack.pop()
                result.append(']')
        elif ch == ')':
            if stack and stack[-1] == '[':

                stack.pop()
            result.append(')')
        elif ch == '}':

            if stack and stack[-1] == '{':

                stack.pop()
                result.append(']')
            else:

                if stack and stack[-1] == '[':
                    stack.pop()
                result.append(')')
        else:
            result.append(ch)

    sanitized = ''.join(result)
    if sanitized != code:
        print(f"[Sanitizer] Auto-corrected {sum(1 for a, b in zip(code, sanitized) if a != b)} delimiter(s)")
    return sanitized
