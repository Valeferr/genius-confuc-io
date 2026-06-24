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
class Parameter(ASTNode):
    param_type: str
    name: str

@dataclass
class FunctionDef(ASTNode):
    return_type: str
    name: str
    parameters: List[Parameter]
    body: List[Statement]

@dataclass
class Program(ASTNode):
    statements: List[Statement] = field(default_factory=list)

# --- Statements ---

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
    condition: Expression
    then_body: List[Statement]
    else_body: List[Statement] = field(default_factory=list)

@dataclass
class WhileLoop(Statement):
    condition: Expression
    body: List[Statement]

@dataclass
class ForLoop(Statement):
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

# --- Expressions ---

@dataclass
class BinaryOp(Expression):
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
class InputCall(Expression):
    pass
