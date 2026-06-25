from typing import List, Dict
from .confucio_ast import *
from .diagnostics import DiagnosticError

class SemanticChecker:
    def __init__(self):
        # We use a simple dictionary for the symbol table since there are limited scopes
        # For simplicity in this project, we might just use a global scope or a stack of scopes.
        self.scopes: List[Dict[str, str]] = [{}]
        self.errors: List[DiagnosticError] = []

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def declare_variable(self, name: str, var_type: str, line: int):
        current_scope = self.scopes[-1]
        if name in current_scope:
            self.errors.append(DiagnosticError(phase="semantic", error=f"Variable '{name}' already declared in this scope", line=line))
        else:
            current_scope[name] = var_type

    def get_variable_type(self, name: str, line: int) -> str:
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        self.errors.append(DiagnosticError(phase="semantic", error=f"Variable '{name}' not declared", line=line))
        return "Unknown"

    def check(self, ast: Program) -> List[DiagnosticError]:
        self.scopes = [{}]
        self.errors = []
        self.visit(ast)
        return self.errors

    def visit(self, node: ASTNode):
        if node is None:
            return None
            
        method_name = f'visit_{type(node).__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ASTNode):
        # Fallback for nodes that don't need specific semantic checking but might have children
        if not hasattr(node, '__dict__'): return
        for key, value in vars(node).items():
            if isinstance(value, ASTNode):
                self.visit(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, ASTNode):
                        self.visit(item)

    def visit_Program(self, node: Program):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_VarDeclaration(self, node: VarDeclaration):
        init_type = self.visit(node.initializer)
        
        # Confuc-IO types vs python literal types
        type_mapping = {
            "int": "Int",
            "float": "Float",
            "string": "String",
            "bool": "Bool"
        }
        
        if init_type in type_mapping:
            init_type = type_mapping[init_type]
            
        if init_type and init_type != "Unknown" and init_type != node.var_type:
            self.errors.append(DiagnosticError(
                phase="semantic", 
                error=f"Type mismatch: cannot assign '{init_type}' to variable '{node.name}' of type '{node.var_type}'", 
                line=node.line
            ))
            
        self.declare_variable(node.name, node.var_type, node.line)

    def visit_Assignment(self, node: Assignment):
        var_type = self.get_variable_type(node.name, node.line)
        val_type = self.visit(node.value)
        
        type_mapping = {
            "int": "Int",
            "float": "Float",
            "string": "String",
            "bool": "Bool"
        }
        
        if val_type in type_mapping:
            val_type = type_mapping[val_type]
            
        if var_type != "Unknown" and val_type != "Unknown" and var_type != val_type:
            self.errors.append(DiagnosticError(
                phase="semantic", 
                error=f"Type mismatch: cannot assign '{val_type}' to variable '{node.name}' of type '{var_type}'", 
                line=node.line
            ))

    def visit_IfStatement(self, node: IfStatement):
        cond_type = self.visit(node.condition)
        if cond_type not in ("Bool", "bool", "Unknown"):
            self.errors.append(DiagnosticError(
                phase="semantic", 
                error=f"Condition must evaluate to Bool, got '{cond_type}'", 
                line=node.line
            ))
            
        self.push_scope()
        for stmt in node.then_body:
            self.visit(stmt)
        self.pop_scope()
        
        if node.else_body:
            self.push_scope()
            for stmt in node.else_body:
                self.visit(stmt)
            self.pop_scope()

    def visit_WhileLoop(self, node: WhileLoop):
        cond_type = self.visit(node.condition)
        if cond_type not in ("Bool", "bool", "Unknown"):
            self.errors.append(DiagnosticError(
                phase="semantic", 
                error=f"Loop condition must evaluate to Bool, got '{cond_type}'", 
                line=node.line
            ))
            
        self.push_scope()
        for stmt in node.body:
            self.visit(stmt)
        self.pop_scope()

    def visit_ForLoop(self, node: ForLoop):
        self.push_scope()
        self.visit(node.init)
        
        cond_type = self.visit(node.condition)
        if cond_type not in ("Bool", "bool", "Unknown"):
            self.errors.append(DiagnosticError(
                phase="semantic", 
                error=f"For-loop condition must evaluate to Bool, got '{cond_type}'", 
                line=node.line
            ))
            
        self.visit(node.update)
        for stmt in node.body:
            self.visit(stmt)
        self.pop_scope()

    def visit_BinaryOp(self, node: BinaryOp):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        
        # Comparisons return bool
        if node.operator in ("<", ">", "==", "!=", "<=", ">="):
            return "Bool"
            
        # Math operators
        if left_type == right_type:
            return left_type
        
        if left_type in ("Float", "float", "Int", "int") and right_type in ("Float", "float", "Int", "int"):
            return "Float"
        
        if left_type == "Unknown" or right_type == "Unknown":
            return "Unknown"

        return "Unknown"

    def visit_Literal(self, node: Literal):
        return node.literal_type

    def visit_Identifier(self, node: Identifier):
        return self.get_variable_type(node.name, node.line)

    def visit_PrintStatement(self, node: PrintStatement):
        self.visit(node.expression)
        
    def visit_ReturnStatement(self, node: ReturnStatement):
        self.visit(node.value)
        
    def visit_InputCall(self, node: InputCall):
        return "String"
