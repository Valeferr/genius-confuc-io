from typing import List
from core.diagnostics import DiagnosticError, ValidationReport
from core.parser import get_parser
from core.ast_builder import ConfucIOASTBuilder
from core.semantic_checker import SemanticChecker

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