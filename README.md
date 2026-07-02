# Genius ConfuC-IO

A multi-agent system for automatic code generation in the esoteric language **ConfuC-IO**, developed for the Programming Languages Engineering course (A.Y. 2025/26).

The system receives a natural language request and produces syntactically, semantically, and logically validated ConfuC-IO code through a pipeline orchestrated by **LangGraph**, which coordinates four specialized agents.

## Prerequisites

| Component | Version | Notes |
|---|---|---|
| Python | ≥ 3.10 | Tested with 3.14 |
| Azure OpenAI | — | API key and endpoint required |
| Ollama | — | For local logic validation |

## Installation

```bash
git clone https://github.com/Valeferr/genius-confuc-io.git
cd genius-confuc-io
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the root directory:

```env
AZURE_OPENAI_API_KEY="<your-api-key>"
AZURE_OPENAI_ENDPOINT="<your-endpoint>"
AZURE_OPENAI_DEPLOYMENT="gpt-4o-mini"
USE_MOCK=false
OLLAMA_MODEL="codegemma:latest"
```

For logic validation, install and start Ollama with the CodeGemma model:

```bash
ollama pull codegemma
ollama serve
```

## Execution

### CLI Mode (Direct Use)

```bash
python main.py "Write a program that takes a number as input and prints whether it is even or odd"
```

Without arguments, a default prompt is used.

### MCP Server Mode (For External AI Clients)

```bash
python mcp_server.py
```

The server exposes the pipeline as an MCP tool via stdio. To inspect it graphically:

```bash
mcp dev mcp_server.py
```

### Mock Mode (Without API)

Set `USE_MOCK=true` in the `.env` file to use the mock client without consuming API tokens.

## Project Structure

```
genius-confuc-io/
├── main.py                  # CLI Entry point
├── mcp_server.py            # MCP Server (Model Context Protocol)
├── config.py                # Centralized configuration
├── agents/
│   ├── orchestrator.py      # LangGraph graph (pipeline coordination)
│   ├── planner_agent.py     # Task planning
│   ├── generator_agent.py   # ConfuC-IO code generation
│   ├── validator_agent.py   # Syntax and semantic validation
│   ├── repair_agent.py      # Automatic code repair
│   └── base_agent.py        # Base agent class
├── llm/
│   └── client.py            # LLM Client (Azure, Ollama, Mock)
├── core/
│   ├── parser.py            # Lark grammar and sanitizer
│   ├── ast.py               # AST node definitions
│   ├── ast_builder.py       # Lark → AST transformer
│   ├── semantic_checker.py  # Semantic analysis (types, scope)
│   └── diagnostics.py       # Diagnostic error models
├── prompts/
│   ├── planner_prompts.py   # Planner system prompt
│   └── generator_prompts.py # Generator system prompt
├── evals/
│   ├── benchmark_runner.py  # Automated benchmark suite
│   └── test_exam_calculator.py # Calculator test (exam requirement)
├── examples/                # Example programs in ConfuC-IO
├── docs/                    # Technical documentation
└── requirements.txt         # Python dependencies
```

## Testing

### Benchmark tests

```bash
python -m evals.benchmark_runner
```

### Calculator test (exam requirement)

```bash
python -m evals.test_exam_calculator
```

### MCP server test

```bash
python test_mcp.py
```

## ConfuC-IO Language (Summary)

| Concept | Conventional Syntax | ConfuC-IO Syntax |
|---|---|---|
| Integer type | `int` | `Float` |
| String type | `string` | `int` |
| Decimal type | `float` | `String` |
| Boolean type | `bool` | `While` |
| Assignment | `=` | `@` |
| Addition | `+` | `/` |
| Subtraction | `-` | `~` |
| Multiplication | `*` | `Bool` |
| Division | `/` | `+` |
| If | `if` | `func` |
| While | `while` | `return` |
| For | `for` | `if` |
| Print | `print()` | `FileInputStream{...]` |
| Input | `input()` | `deleteSystem32{...]` |
| Return | `return` | `*` |

Every program begins with `Float side {] [` and ends with `* 0 )`.

## License

Software distributed for educational and experimental purposes.