from typing import List, Dict
from core.ast import *
from .diagnostics import DiagnosticError




















LITERAL_TO_CONFUCIO: Dict[str, str] = {
    "int":    "Float",
    "float":  "String",
    "string": "int",
    "bool":   "While",
}


CONFUCIO_COMPARISON_OPS = {"=", "#", "@@", "!@"}


BOOL_RESULT = "Bool"


class SemanticChecker:
    def __init__(self):
        self.scopes: List[Dict[str, str]] = [{}]
        self.errors: List[DiagnosticError] = []




    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()

    def declare_variable(self, name: str, var_type: str, line: int):
        current_scope = self.scopes[-1]
        if name in current_scope:
            self.errors.append(DiagnosticError(
                phase="semantic",
                error=f"Variable '{name}' already declared in this scope",
                line=line,
            ))
        else:
            current_scope[name] = var_type

    def get_variable_type(self, name: str, line: int) -> str:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        self.errors.append(DiagnosticError(
            phase="semantic",
            error=f"Variable '{name}' not declared",
            line=line,
        ))
        return "Unknown"




    def check(self, ast: Program) -> List[DiagnosticError]:
        self.scopes = [{}]
        self.errors = []
        self.visit(ast)
        return self.errors




    def visit(self, node: ASTNode):
        if node is None:
            return None
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        if not hasattr(node, "__dict__"):
            return None
        for value in vars(node).values():
            if isinstance(value, ASTNode):
                self.visit(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        self.visit(item)
        return None




    def visit_Program(self, node: Program):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_VarDeclaration(self, node: VarDeclaration):
        init_type = self.visit(node.initializer)


        if init_type in LITERAL_TO_CONFUCIO:
            init_type = LITERAL_TO_CONFUCIO[init_type]



        if init_type and init_type not in ("Unknown", None) and init_type != node.var_type:
            self.errors.append(DiagnosticError(
                phase="semantic",
                error=(
                    f"Type mismatch: cannot assign '{init_type}' "
                    f"to variable '{node.name}' of type '{node.var_type}'"
                ),
                line=node.line,
            ))

        self.declare_variable(node.name, node.var_type, node.line)

    def visit_Assignment(self, node: Assignment):
        var_type = self.get_variable_type(node.name, node.line)
        val_type = self.visit(node.value)

        if val_type in LITERAL_TO_CONFUCIO:
            val_type = LITERAL_TO_CONFUCIO[val_type]

        if (
            var_type not in ("Unknown", None)
            and val_type not in ("Unknown", None)
            and var_type != val_type
        ):
            self.errors.append(DiagnosticError(
                phase="semantic",
                error=(
                    f"Type mismatch: cannot assign '{val_type}' "
                    f"to variable '{node.name}' of type '{var_type}'"
                ),
                line=node.line,
            ))

    def visit_IfStatement(self, node: IfStatement):
        cond_type = self.visit(node.condition)

        if cond_type not in (BOOL_RESULT, "While", "Unknown", None):
            self.errors.append(DiagnosticError(
                phase="semantic",
                error=f"Condition must evaluate to a boolean expression, got '{cond_type}'",
                line=node.line,
            ))

        self.push_scope()
        for stmt in node.then_body:
            self.visit(stmt)
        self.pop_scope()


    def visit_WhileLoop(self, node: WhileLoop):
        cond_type = self.visit(node.condition)
        if cond_type not in (BOOL_RESULT, "While", "Unknown", None):
            self.errors.append(DiagnosticError(
                phase="semantic",
                error=f"Loop condition must evaluate to a boolean expression, got '{cond_type}'",
                line=node.line,
            ))

        self.push_scope()
        for stmt in node.body:
            self.visit(stmt)
        self.pop_scope()

    def visit_ForLoop(self, node: ForLoop):
        self.push_scope()
        self.visit(node.init)

        cond_type = self.visit(node.condition)
        if cond_type not in (BOOL_RESULT, "While", "Unknown", None):
            self.errors.append(DiagnosticError(
                phase="semantic",
                error=f"For-loop condition must evaluate to a boolean expression, got '{cond_type}'",
                line=node.line,
            ))

        self.visit(node.update)
        for stmt in node.body:
            self.visit(stmt)
        self.pop_scope()

    def visit_PrintStatement(self, node: PrintStatement):
        self.visit(node.expression)

    def visit_ReturnStatement(self, node: ReturnStatement):
        self.visit(node.value)




    def visit_BinaryOp(self, node: BinaryOp):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)


        if node.operator in CONFUCIO_COMPARISON_OPS:
            return BOOL_RESULT



        if left_type == "Unknown" or right_type == "Unknown":
            return "Unknown"


        numeric = {"Float", "String", "float", "int"}
        if left_type in numeric and right_type in numeric:

            if "String" in (left_type, right_type) or "float" in (left_type, right_type):
                return "String"
            return "Float"

        if left_type == right_type:
            return left_type

        return "Unknown"

    def visit_Literal(self, node: Literal):

        return node.literal_type

    def visit_Identifier(self, node: Identifier):
        return self.get_variable_type(node.name, node.line)

    def visit_InputStatement(self, node: InputStatement):


        self.get_variable_type(node.variable, node.line)

    def visit_ExpressionStatement(self, node: ExpressionStatement):
        self.visit(node.expression)

    def visit_FunctionCall(self, node: FunctionCall):

        return "Unknown"
