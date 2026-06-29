import asyncio
import sys
from mcp.server.fastmcp import FastMCP
from agents.orchestrator import Orchestrator

# Crea il server FastMCP
mcp = FastMCP("genius-confuc-io")

@mcp.tool()
def compile_confucio_code(prompt: str) -> str:
    """
    Compiles a natural language request into ConfuC-IO esoteric code.
    
    Args:
        prompt: The natural language description of what the code should do (e.g. "Calculate Fibonacci sequence").
    """
    try:
        orchestrator = Orchestrator()
        # FastMCP gestisce automaticamente il fatto che le print (stdout)
        # vadano loggate su stderr se sta comunicando via stdio.
        final_code = orchestrator.run_pipeline(prompt)
        if not final_code:
            return "Error: Pipeline failed to generate valid code."
        return final_code
    except Exception as e:
        return f"Error during compilation: {str(e)}"

def run_mcp_server():
    """Avvia il server MCP su stdio."""
    print("Avvio del server MCP genius-confuc-io...", file=sys.stderr)
    mcp.run()

if __name__ == "__main__":
    run_mcp_server()
