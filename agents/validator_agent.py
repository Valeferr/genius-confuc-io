from typing import List, Any
from .diagnostics import DiagnosticError, ValidationReport
from .confucio_parser import get_parser
from .confucio_ast_builder import ConfucIOASTBuilder
from .semantic_checker import SemanticChecker

class ValidatorAgent:
    def __init__(self, parser=None, ast_builder=None, semantic_checker=None):
        """
        ValidatorAgent integrates the Parser, AST Builder, and Semantic Checker.
        """
        self.parser = parser or get_parser()
        self.ast_builder = ast_builder or ConfucIOASTBuilder()
        self.semantic_checker = semantic_checker or SemanticChecker()
        
    def validate_syntax(self, code: str) -> List[DiagnosticError]:
        errors = []
        try:
            self.parser.parse(code)
        except Exception as e:
            errors.append(DiagnosticError(phase="syntax", error=str(e), line=getattr(e, "line", 0)))
        return errors

    def validate_semantics(self, code: str) -> List[DiagnosticError]:
        errors = []
        try:
            ast_tree = self.parser.parse(code)
            ast_model = self.ast_builder.transform(ast_tree)
            errors = self.semantic_checker.check(ast_model)
        except Exception as e:
            errors.append(DiagnosticError(phase="semantic", error=f"AST/Semantic error: {str(e)}", line=getattr(e, "line", 0)))
        return errors

    def validate_code(self, code: str) -> ValidationReport:
        syntax_errors = self.validate_syntax(code)
        if syntax_errors:
            return ValidationReport(is_valid=False, errors=syntax_errors)
        
        semantic_errors = self.validate_semantics(code)
        if semantic_errors:
            return ValidationReport(is_valid=False, errors=semantic_errors)
            
        return ValidationReport(is_valid=True, errors=[])