# System Architecture

This document describes the architecture of the Genius ConfuC-IO system, following a canonical architectural scheme for an LLM Coder System.

## Reference Architectural Scheme

The canonical architecture of an LLM Coder system includes the following components:

- **Input**: User Request / IDE Context
- **Orchestrator Agent**: Coordinates the flow between agents
- **LLM Core**: The generative model (GPT-4, CodeLlama, etc.)
- **Planning Agent + Logic**: Plans the code structure
- **Coding Agent + Logic**: Generates the source code
- **Static Checker**: Static analysis (pylint, mypy, etc.)
- **Validation & Safety Layer**: Final verification
- **Output**: Verified Code Output

## Mapping to ConfuC-IO Implementation

Each block of the scheme has been implemented in the project as follows.

### Input Layer: User Request

| Canonical Component | ConfuC-IO Implementation |
|---|---|
| User Request | CLI argument passed to `main.py` |
| IDE Context | MCP Tool `generate_confucio_code` (from `mcp_server.py`) |

The user provides a request in natural language. The system accepts input both from the command line and from an external MCP client (e.g., Claude Desktop, Cursor).

### Orchestrator Agent

| Canonical Component | ConfuC-IO Implementation |
|---|---|
| Orchestrator Agent | `Orchestrator` class in `agents/orchestrator.py` |
| Coordination Graph | LangGraph `StateGraph` |

The Orchestrator builds a directed acyclic graph with nodes (agents) and conditional edges. The graph manages the flow:

```
planner_node → generator_node → syntax_validation → semantic_validation → logic_validation
                                       ↑                                         │
                                       └──────────── repair_node ←───────────────┘
```

Upon any validation failure, the `repair_node` attempts a correction and the code re-enters the cycle, up to a maximum of `MAX_RETRIES` (configurable in `config.py`).

### LLM Core (Multiple Calls)

| Canonical Component | ConfuC-IO Implementation |
|---|---|
| LLM Core (GPT-4/CodeLlama) | `AzureLLMClient` → Azure OpenAI (gpt-4o-mini) |
| LLM Call for validation | `OllamaClient` → Local Ollama (CodeGemma) |
| LLM Mock for development | `MockLLMClient` |

The LLM clients are defined in `llm/client.py`. All extend the abstract `LLMClient` class and implement the `generate()` method.

- **Azure OpenAI**: Used for code planning, generation, and repair.
- **Ollama (CodeGemma)**: Used exclusively for logic validation (LLM-as-a-Judge technique). It receives a prompt with the ConfuC-IO rules and must reply in JSON (`is_valid` + `reason`).
- **Mock**: Used for offline development without consuming API tokens.

### Planning Agent + Logic

| Canonical Component | ConfuC-IO Implementation |
|---|---|
| Planning Agent | `PlannerAgent` class in `agents/planner_agent.py` |
| Planning Logic | System prompt in `prompts/planner_prompts.py` |

The Planner receives the user request and produces a structured plan in JSON format containing:
- `goal`: The goal of the program
- `variables`: The necessary variables with their respective types
- `steps`: The logical steps to follow

The plan is independent of the target language syntax.

### Coding Agent + Logic

| Canonical Component | ConfuC-IO Implementation |
|---|---|
| Coding Agent | `GeneratorAgent` class in `agents/generator_agent.py` |
| Coding Logic | System prompt in `prompts/generator_prompts.py` |

The Generator translates the JSON plan into ConfuC-IO code. The system prompt contains the complete language grammar with examples (few-shot learning), so the model does not fall into the trap of misleading names (e.g., `FileInputStream` which is actually a `print`).

### Static Checker

| Canonical Component | ConfuC-IO Implementation |
|---|---|
| Static Checker (pylint, mypy) | Lark Parser + AST Builder + Semantic Checker |

The static analysis block consists of three modules:

1. **Lark Parser** (`core/parser.py`): LALR formal grammar that verifies syntactic correctness. It includes a **Sanitizer** (`sanitize_confucio_code`) that deterministically corrects the most common delimiter errors produced by the LLM.

2. **AST Builder** (`core/ast_builder.py`): Transforms the Lark parse tree into a typed AST (classes defined in `core/ast.py`).

3. **Semantic Checker** (`core/semantic_checker.py`): Visits the AST and verifies:
   - Type consistency in operations and assignments
   - Variable declarations before use
   - Scope correctness

### Validation & Safety Layer

| Canonical Component | ConfuC-IO Implementation |
|---|---|
| Validation & Safety Layer | `logic_validation_node` in the Orchestrator |
| Technique | LLM-as-a-Judge (CodeGemma via Ollama) |

After passing static checks (syntax + semantics), the code is subjected to logic validation by a second LLM model (CodeGemma, running locally via Ollama). This model receives:
- The original user request
- The generated code
- The ConfuC-IO language rules

And must judge whether the code **actually solves** the requested problem. It is the concrete implementation of the **LLM-as-a-Judge** technique.

### Debugger (Repair Agent)

| Canonical Component | ConfuC-IO Implementation |
|---|---|
| Debugger + Profiler | `RepairAgent` class in `agents/repair_agent.py` |

The Repair Agent receives the defective code and the diagnostic error report (`ValidationReport` model in `core/diagnostics.py`), and produces a corrected version of the code. It uses the same Azure OpenAI model as the generation.

### Verified Code Output

| Canonical Component | ConfuC-IO Implementation |
|---|---|
| Verified Code Output | ConfuC-IO code returned by `run_pipeline()` |
| Format | Text printed on stdout (CLI) or MCP Tool response (server) |

The final code has passed all three validation levels (syntactic, semantic, logical) or has exhausted the maximum number of repair attempts.

## MCP Protocol (Model Context Protocol)

The project also implements an MCP server (`mcp_server.py`) that exposes the pipeline as a standardized service:

| MCP Primitive | Name | Description |
|---|---|---|
| Tool | `generate_confucio_code` | Runs the entire pipeline and returns the code |
| Resource | `info://confuc-io` | Exposes language rules to clients |
| Prompt | `coding_workflow` | Template to bootstrap a generation session |

This allows any MCP-compatible client (Claude Desktop, Cursor, MCP Inspector) to use the generator without knowing its implementation details.

## Flow Diagram

```
┌──────────────┐
│ User Request │
└──────┬───────┘
       │
       ▼
┌──────────────────┐     ┌────────────────────────────────────────────┐
│   Orchestrator   │     │            LLM Core                       │
│   (LangGraph)    │────▶│  Azure OpenAI (gpt-4o-mini)               │
│                  │     │  Local Ollama (CodeGemma) for validation   │
└──────┬───────────┘     └────────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│   Planner    │──── LLM call 1 ───▶ JSON Plan
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Generator   │──── LLM call 2 ───▶ ConfuC-IO Code
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│          Validation Layer                │
│  ┌────────────┐  ┌───────────────────┐   │
│  │   Syntax   │  │    Semantic       │   │
│  │  (Lark)    │─▶│  (AST + Types)   │   │
│  └────────────┘  └───────┬───────────┘   │
│                          │               │
│                          ▼               │
│                  ┌───────────────────┐   │
│                  │  Logic Validator  │   │
│                  │  (CodeGemma/      │   │
│                  │   LLM-as-Judge)   │   │
│                  └───────────────────┘   │
└──────────────┬───────────────────────────┘
               │
          ┌────┴────┐
          │ Errors? │
          └────┬────┘
         yes   │    no
    ┌──────────┴──────────┐
    ▼                     ▼
┌────────┐        ┌──────────────┐
│ Repair │        │ Verified     │
│ Agent  │        │ Code Output  │
└────┬───┘        └──────────────┘
     │
     └──── feedback (LLM call N) ──▶ back to Syntax Validation
```
