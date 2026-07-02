# Design Decisions

This document describes the main design decisions made during the development of the Genius ConfuC-IO system.

## Multi-Agent Architecture

### Why a multi-agent system?

Generating code in an esoteric language like ConfuC-IO represents a significant challenge for LLM models: the syntax is deliberately counter-intuitive, and the names of the keywords are designed to confuse. A single prompt is not enough to ensure correct code.

Therefore, a multi-agent architecture with separation of responsibilities was adopted:
- The **Planner** reasons about the logic of the problem without worrying about syntax.
- The **Generator** translates the plan into code, focusing exclusively on the language rules.
- The **Validator** verifies the code deterministically (not probabilistically).
- The **Repair Agent** corrects errors using the diagnostic feedback.

This separation allows isolating points of failure and iterating on corrections in a targeted manner.

### Why LangGraph?

LangGraph was chosen (over a simple sequential chain) for the ability to define **conditional edges** in the graph. The flow is not linear: after a failed validation, the code must return to the Repair Agent and re-enter the validation cycle. LangGraph natively manages this feedback loop pattern with a typed `StateGraph`.

## Choice of LLM Models

### Azure OpenAI (gpt-4o-mini) for generation and repair

Azure OpenAI was chosen over the direct OpenAI API for:
- Compliance with European data residency policies.
- The ability to manage dedicated endpoints and specific deployments.
- Academic support through Azure for Students credits.

The `gpt-4o-mini` model offers a good compromise between generation quality, response speed, and cost per token.

### Ollama (CodeGemma) for logic validation

Logic validation is entrusted to a local model (CodeGemma 9B via Ollama) for several reasons:
- **Zero cost**: No API token consumption for validation.
- **Reduced latency**: No network latency, the model runs on the local machine.
- **Independence**: The logic validator is a different model from the one that generated the code. This diversity reduces the risk of "confirmation bias" (the generator does not validate itself).
- **LLM-as-a-Judge technique**: A second LLM judges the logical correctness of the code against the original request.

The validation prompt was calibrated with aggressive instructions to overcome CodeGemma's pre-training bias (which would otherwise interpret `FileInputStream` as opening a file and `deleteSystem32` as deleting a file).

## Parser and Static Analysis

### Why Lark (LALR)?

Lark with an LALR parser was chosen for:
- **Determinism**: Unlike an LLM, a formal parser does not hallucinate. If the code is syntactically incorrect, it is deterministically rejected.
- **Speed**: LALR parsing is linear in time.
- **Maintainability**: The grammar is declarative and modifiable without touching the Python code.

### Deterministic Sanitizer

Before parsing, the code passes through a sanitizer (`sanitize_confucio_code` in `core/parser.py`) which automatically corrects the most common delimiter errors produced by the LLM (e.g., `deleteSystem32[x]` → `deleteSystem32{x]`). This significantly reduces the number of repair iterations needed.

### Semantic Analysis with Visitor Pattern

The Semantic Checker implements the Visitor pattern on the AST to verify:
- That variables are declared before use.
- That types are consistent in operations (e.g., not adding an integer with a string).
- That the conditions in control constructs are valid.

## MCP Protocol

It was chosen to implement the Model Context Protocol to transform the project from an isolated CLI application into a **composable microservice**. The Python `FastMCP` SDK allows exposing the pipeline as a standardized tool, making the generator usable by any MCP-compatible client (Claude Desktop, Cursor, autonomous agents) without modifying the code.

## Error Handling and Retry

The system implements a retry mechanism with a configurable maximum threshold (`MAX_RETRIES = 3` in `config.py`). On each validation failure (syntactic, semantic, or logical), the Repair Agent receives:
- The defective code.
- The full diagnostic report with the error phase, description, and line number.

This approach allows for targeted corrections rather than complete code regenerations.
