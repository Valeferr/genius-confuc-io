import json
from pydantic import BaseModel, Field
from typing import Optional
from .diagnostics import ValidationReport
from .llm_client import LLMClient

class RepairResult(BaseModel):
    repaired_code: str = Field(description="The source code after being repaired.")
    explanation: str = Field(description="Short explanation of what was fixed.")

class RepairAgent:
    def __init__(self, client: LLMClient):
        self.client = client
        
        self.system_prompt = "You are an expert compiler engineer and repair agent for the ConfuC-IO programming language."
        self.prompt_template = (
            "Your task is to fix the following code snippet based on the compiler diagnostics.\n\n"
            "Code:\n{code_snippet}\n\n"
            "Diagnostics (Errors):\n{errors}\n\n"
            "Please fix ONLY the problematic parts. Do not change the overall logic. "
            "Output MUST be in valid JSON format with the following keys:\n"
            '- "repaired_code": "The source code after being repaired"\n'
            '- "explanation": "Short explanation of what was fixed"\n'
        )

    def repair_code(self, code_snippet: str, validation_report: ValidationReport) -> RepairResult:
        """
        Takes the broken code snippet and the validation report, returns the Repaired code.
        """
        errors_str = "\n".join([err.model_dump_json() for err in validation_report.errors])
        
        prompt = self.prompt_template.format(
            code_snippet=code_snippet,
            errors=errors_str
        )
        
        try:
            response_text = self.client.generate(prompt=prompt, system_prompt=self.system_prompt)
            try:
                clean_text = response_text.strip()
                if clean_text.startswith("```json"):
                    clean_text = clean_text[7:]
                if clean_text.startswith("```"):
                    clean_text = clean_text[3:]
                if clean_text.endswith("```"):
                    clean_text = clean_text[:-3]
                    
                data = json.loads(clean_text)
                return RepairResult(repaired_code=data.get("repaired_code", ""), explanation=data.get("explanation", ""))
            except json.JSONDecodeError:
                return RepairResult(repaired_code=response_text, explanation="Failed to parse JSON explanation")
        except Exception as e:
            return RepairResult(repaired_code=code_snippet, explanation=f"LLM failure: {e}")