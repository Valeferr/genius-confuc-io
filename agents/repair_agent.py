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
        
        self.system_prompt = """\
You are an expert compiler engineer and repair agent for the ConfuC-IO programming language.

CONFUC-IO LANGUAGE RULES (apply these when fixing code):

TYPES (intentionally misleading names):
  Float = integer,  int = string,  String = float,  While = boolean
  FORBIDDEN: Int, Bool, Boolean, Integer

VARIABLE NAMES:
  Must contain ONLY [a-zA-Z0-9_]. NO accented characters! (e.g. metà -> meta)

ASSIGNMENT: use @ (not =)  →  Float x @ 5

ARITHMETIC OPERATORS (all swapped):
  /  = addition (a+b),   ~ = subtraction (a-b),   + = division (a/b),   Bool = multiplication (a*b)
  NO modulo operator exists.

COMPARISON OPERATORS (all swapped):
  =  means greater-than (>),   # means less-than (<),   @@ means equality (==),   !@ means inequality (!=)
  FORBIDDEN: > < == != <= >=

DELIMITERS (all swapped):
  {  replaces (    ]  replaces )    [  replaces {    )  replaces }
  FORBIDDEN in code: plain ( ) { }

  CRITICAL: ] and ) are NOT interchangeable:
    ] closes CONDITIONS only  →  {condition]
    ) closes BLOCKS only      →  [body)
    WRONG: func {cond] [body]   RIGHT: func {cond] [body)
    WRONG: return {cond] [body] RIGHT: return {cond] [body)

CONTROL FLOW:
  if-statement  →  func {condition] [body)       (NO else clause!)
  while-loop    →  return {condition] [body)
  for-loop      →  if {init; condition; update] [body)
  return-value  →  * expression
  FORBIDDEN: if(...){  while(...){  for(...){  else

I/O:
  print   →  FileInputStream{expression]
  input   →  deleteSystem32{variable_name]
  CRITICAL: deleteSystem32 acts like scanf and does NOT return a value.
    WRONG: Float x @ deleteSystem32{]
    RIGHT: Float x @ 0 \n deleteSystem32{x]
  CRITICAL: deleteSystem32 is ALWAYS deleteSystem32{variable_name]
    WRONG: deleteSystem32[x]  ← [ is a block opener, NOT a parenthesis replacement
    WRONG: deleteSystem32(x)  ← forbidden, conventional parentheses
    RIGHT: deleteSystem32{x]  ← { replaces (, ] replaces )
  FORBIDDEN: FileInputStream(  deleteSystem32(  deleteSystem32[

ENTRY POINT (MANDATORY):
  The program MUST start with `Float side {] [` and end with `* 0 )`.

When you see a compiler error like "Expected LBRACE" it means { is expected but ( was used.
"Expected RSQB" means ] is expected.
"Expected LSQB" means [ is expected.
"Expected RPAR" means ) is expected.
"""
        self.prompt_template = (
            "Fix the following Confuc-IO code using the language rules provided in your system prompt.\n\n"
            "Broken code:\n{code_snippet}\n\n"
            "Compiler diagnostics:\n{errors}\n\n"
            "Fix ONLY the syntax/type/operator errors shown above. Preserve the program logic.\n"
            "Remember: conditions use {{ and ], blocks use [ and ).\n"
            "Output MUST be valid JSON with these exact keys:\n"
            '- "repaired_code": the corrected Confuc-IO source code as a string\n'
            '- "explanation": one sentence describing what was fixed\n'
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