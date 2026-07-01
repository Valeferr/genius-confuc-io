from pydantic import BaseModel, Field

class DiagnosticError(BaseModel):
    phase: str = Field(description="The phase where the error occurred (e.g., 'syntax', 'semantic', 'ast')")
    error: str = Field(description="Description of the error, e.g., 'Type mismatch'")
    line: int = Field(description="Line number where the error occurred")


class ValidationReport(BaseModel):
    is_valid: bool = Field(description="True if there are no errors, False otherwise")
    errors: list[DiagnosticError] = Field(default_factory=list, description="List of errors if any")
