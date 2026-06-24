from lark import Transformer, v_args
from .confucio_ast import *

@v_args(inline=True)
class ConfucIOASTBuilder(Transformer):
    
    def start(self, *statements):
        return Program(line=0, statements=list(statements))
        
    def declaration(self, var_type, name, initializer):
        # var_type and name are Tokens from Lark
        return VarDeclaration(line=name.line, var_type=str(var_type), name=str(name), initializer=initializer)
        
    def assignment(self, name, value):
        return Assignment(line=name.line, name=str(name), value=value)
        
    def if_stmt(self, condition, *statements):
        return IfStatement(line=0, condition=condition, then_body=list(statements))
        
    def while_stmt(self, condition, *statements):
        return WhileLoop(line=0, condition=condition, body=list(statements))
        
    def for_stmt(self, init, condition, update, *statements):
        return ForLoop(line=0, init=init, condition=condition, update=update, body=list(statements))
        
    def return_stmt(self, value):
        return ReturnStatement(line=0, value=value)
        
    def print_stmt(self, expression):
        return PrintStatement(line=0, expression=expression)
        
    def condition(self, left, op=None, right=None):
        if op is None:
            return left
        return BinaryOp(line=0, operator=str(op), left=left, right=right)
        
    def add(self, *terms):
        expr = terms[0]
        for term in terms[1:]:
            expr = BinaryOp(line=0, operator="/", left=expr, right=term)
        return expr

    def sub(self, *terms):
        expr = terms[0]
        for term in terms[1:]:
            expr = BinaryOp(line=0, operator="-", left=expr, right=term)
        return expr
        
    def mul(self, *terms):
        expr = terms[0]
        for term in terms[1:]:
            expr = BinaryOp(line=0, operator="*", left=expr, right=term)
        return expr
        
    def mod(self, *terms):
        expr = terms[0]
        for term in terms[1:]:
            expr = BinaryOp(line=0, operator="%", left=expr, right=term)
        return expr
        
    def term(self, child):
        # Child could be NUMBER, CNAME or a math_expr enclosed in parenthesis
        # If it's a token
        if hasattr(child, 'type'):
            if child.type == 'NUMBER':
                # Convert to int or float depending on content
                val_str = str(child)
                if '.' in val_str:
                    return Literal(line=child.line, value=float(val_str), literal_type="float")
                return Literal(line=child.line, value=int(val_str), literal_type="int")
            elif child.type == 'CNAME':
                return Identifier(line=child.line, name=str(child))
        # otherwise it's already an AST node (like from parens)
        return child
        
    def input_call(self):
        return InputCall(line=0)
        
    def ESCAPED_STRING(self, token):
        val = str(token)[1:-1] # Remove quotes
        return Literal(line=token.line, value=val, literal_type="string")
