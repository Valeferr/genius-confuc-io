from lark import Lark

# Grammatica EBNF per Confuc-IO
# Regole bizzarre: 
# - L'assegnamento usa @
# - L'addizione usa /
# - if -> func
# - while -> return
# - for -> if
# - return -> *
# - print -> FileInputStream
# - input -> deleteSystem32

CONFUCIO_GRAMMAR = """
    start: statement+

    ?statement: declaration
              | assignment
              | if_stmt
              | while_stmt
              | for_stmt
              | return_stmt
              | print_stmt
              | expression

    declaration: TYPE CNAME "@" expression
    assignment: CNAME "@" expression
    
    if_stmt: "func" "(" condition ")" "{" statement* "}"
    while_stmt: "return" "(" condition ")" "{" statement* "}"
    for_stmt: "if" "(" (declaration|assignment) ";" condition ";" assignment ")" "{" statement* "}"
    
    return_stmt: "*" expression
    print_stmt: "FileInputStream" "(" expression ")"
    
    ?condition: expression (COMPARE_OP expression)? -> condition
    COMPARE_OP: "<" | ">" | "==" | "!=" | "<=" | ">="
    
    ?expression: math_expr | input_call | ESCAPED_STRING
    
    ?math_expr: math_expr "/" term -> add
              | math_expr "-" term -> sub
              | math_expr "*" term -> mul
              | math_expr "%" term -> mod
              | term
    
    term: NUMBER | CNAME | "(" math_expr ")"
    
    input_call: "deleteSystem32" "(" ")"
    
    TYPE.10: "Int" | "Float" | "String" | "Bool"
    
    %import common.CNAME
    %import common.NUMBER
    %import common.ESCAPED_STRING
    %import common.WS
    %ignore WS
    
    // Ignoriamo i commenti
    COMMENT: "//" /[^\\n]*/
    %ignore COMMENT
"""

def get_parser():
    """Restituisce l'istanza del parser Lark per Confuc-IO."""
    # Impostiamo il parser. 
    # 'start' è la regola iniziale.
    return Lark(CONFUCIO_GRAMMAR, start='start', parser='lalr')

def validate_code(code: str):
    """
    Tenta di fare il parsing del codice fornito.
    Se il codice contiene errori sintattici (es. usa un if normale anziché func),
    il parser LALR di Lark solleverà un'eccezione (UnexpectedToken, UnexpectedCharacters).
    Restituisce l'albero AST se valido.
    """
    parser = get_parser()
    return parser.parse(code)
