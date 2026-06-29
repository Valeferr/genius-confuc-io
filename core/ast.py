from dataclasses import dataclass, field
from typing import List, Optional, Any

@dataclass
class ASTNode:
    line: int

@dataclass
class Statement(ASTNode):
    pass

@dataclass
class Expression(ASTNode):
    pass

@dataclass
class Program(ASTNode):
    """
    Root node of a Confuc-IO program.
    Confuc-IO has no user-defined functions; the only entry point is the
    built-in `side` name (equivalent to conventional `main`).
    """
    statements: List[Statement] = field(default_factory=list)


@dataclass
class VarDeclaration(Statement):
    var_type: str
    name: str
    initializer: Expression

@dataclass
class Assignment(Statement):
    name: str
    value: Expression

@dataclass
class IfStatement(Statement):
    """
    Corresponds to Confuc-IO `func {condition] [body)` (conventional `if`).
    No else clause exists in the language.
    """
    condition: Expression
    then_body: List[Statement]

@dataclass
class WhileLoop(Statement):
    """
    Corresponds to Confuc-IO `return {condition] [body)` (conventional `while`).
    """
    condition: Expression
    body: List[Statement]

@dataclass
class ForLoop(Statement):
    """
    Corresponds to Confuc-IO `if {init; cond; update] [body)` (conventional `for`).
    """
    init: Statement
    condition: Expression
    update: Statement
    body: List[Statement]

@dataclass
class ReturnStatement(Statement):
    value: Expression

@dataclass
class PrintStatement(Statement):
    expression: Expression

@dataclass
class InputStatement(Statement):
    pass

@dataclass
class ExpressionStatement(Statement):
    expression: Expression


@dataclass
class BinaryOp(Expression):
    """
    Arithmetic / comparison binary operation.

    Confuc-IO arithmetic operators:
      '/'   = addition    (conventional +)
      '~'   = subtraction (conventional -)
      '+'   = division    (conventional /)
      'Bool' = multiplication (conventional *)

    Confuc-IO comparison operators:
      '='   = greater than (conventional >)
      '#'   = less than    (conventional <)
      '@@'  = equality     (conventional ==)
      '!@'  = inequality   (conventional !=)
    """
    operator: str
    left: Expression
    right: Expression

@dataclass
class UnaryOp(Expression):
    operator: str
    operand: Expression

@dataclass
class Literal(Expression):
    value: Any
    literal_type: str

@dataclass
class Identifier(Expression):
    name: str

@dataclass
class FunctionCall(Expression):
    function_name: str
    arguments: List[Expression]

@dataclass
class InputStatement(Statement):
    variable: str

