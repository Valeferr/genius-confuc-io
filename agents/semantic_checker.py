from typing import List, Dict
from .confucio_ast import *
from .diagnostics import DiagnosticError

# ---------------------------------------------------------------------------
# Type system notes for Confuc-IO:
#
# The AST builder (confucio_ast_builder.py) produces Literal nodes with
# Python literal types: "int", "float", "string".
# These must be mapped to the Confuc-IO declared type names before comparison:
#
#   Python literal "int"    → Confuc-IO "Float"   (integer value)
#   Python literal "float"  → Confuc-IO "String"  (float value)
#   Python literal "string" → Confuc-IO "int"     (string value)
#   Python literal "bool"   → Confuc-IO "While"   (boolean value)
#
# The grammar TYPE terminal accepts: Float | int | String | While
# The AST BinaryOp.operator stores Confuc-IO operator symbols:
#   Arithmetic:  /  ~ + Bool   (add, sub, div, mul)
#   Comparison:  =  # @@ !@    (greater, less, equal, not equal)
# ---------------------------------------------------------------------------

# Converts Python literal type names → Confuc-IO declared type names
LITERAL_TO_CONFUCIO: Dict[str, str] = {
    "int":    "Float",   # integer literals  → Float type
    "float":  "String",  # float literals    → String type
    "string": "int",     # string literals   → int type
    "bool":   "While",   # boolean literals  → While type
}

# Confuc-IO comparison operators (produce a boolean result)
CONFUCIO_COMPARISON_OPS = {"=", "#", "@@", "!@"}

# Internal boolean label used by the checker (not a declared type)
BOOL_RESULT = "Bool"


class SemanticChecker:
    def __init__(self):
        self.scopes: List[Dict[str, str]] = [{}]
        self.errors: List[DiagnosticError] = []

    # -------------------------------------------------------------------------
    # Scope management
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------------
    def check(self, ast: Program) -> List[DiagnosticError]:
        self.scopes = [{}]
        self.errors = []
        self.visit(ast)
        return self.errors

    # -------------------------------------------------------------------------
    # Visitor dispatch
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # Statement visitors
    # -------------------------------------------------------------------------
    def visit_Program(self, node: Program):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_VarDeclaration(self, node: VarDeclaration):
        init_type = self.visit(node.initializer)

        # Convert Python literal type → Confuc-IO type name for comparison
        if init_type in LITERAL_TO_CONFUCIO:
            init_type = LITERAL_TO_CONFUCIO[init_type]

        # "Unknown" means the type could not be determined — skip the check.
        # This covers InputCall (deleteSystem32{]) which is polymorphic.
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
        # Conditions must evaluate to a boolean-ish type
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
        # Note: Confuc-IO has no else clause

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

    # -------------------------------------------------------------------------
    # Expression visitors
    # -------------------------------------------------------------------------
    def visit_BinaryOp(self, node: BinaryOp):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        # Confuc-IO comparison operators: =  #  @@
        if node.operator in CONFUCIO_COMPARISON_OPS:
            return BOOL_RESULT

        # Arithmetic operators: /  ~  +  Bool  (and legacy - * for compatibility)
        # If either side is Unknown, propagate Unknown
        if left_type == "Unknown" or right_type == "Unknown":
            return "Unknown"

        # Both numeric Confuc-IO types (Float = int, String = float)
        numeric = {"Float", "String", "float", "int"}
        if left_type in numeric and right_type in numeric:
            # Return the "wider" type (String/float dominates Float/int)
            if "String" in (left_type, right_type) or "float" in (left_type, right_type):
                return "String"
            return "Float"

        if left_type == right_type:
            return left_type

        return "Unknown"

    def visit_Literal(self, node: Literal):
        # Returns the Python literal type; VarDeclaration/Assignment will map it
        return node.literal_type

    def visit_Identifier(self, node: Identifier):
        return self.get_variable_type(node.name, node.line)

    def visit_InputStatement(self, node: InputStatement):
        # deleteSystem32 acts like scanf, so it modifies an existing variable.
        # We just need to check if the variable is declared.
        self.get_variable_type(node.variable, node.line)

    def visit_ExpressionStatement(self, node: ExpressionStatement):
        self.visit(node.expression)

    def visit_FunctionCall(self, node: FunctionCall):
        # Generic function call — type unknown without a full function table
        return "Unknown"
