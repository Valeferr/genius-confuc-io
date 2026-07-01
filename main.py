import argparse
from agents.orchestrator import Orchestrator

def main():
    parser = argparse.ArgumentParser(description="Genius ConfuC-IO")
    parser.add_argument("--mcp-server", action="store_true", help="Run as an MCP server")
    parser.add_argument("request", nargs="*", default=["Crea una funzione che calcola Fibonacci"], help="Natural language request for the ConfuC-IO code")
    args = parser.parse_args()

    if args.mcp_server:
        from mcp_server import run_mcp_server
        run_mcp_server()
        return

    print("Avvio del Sistema Multi-Agente ConfuC-IO")
    orchestrator = Orchestrator()
    
    request = " ".join(args.request) if isinstance(args.request, list) else args.request
    if not request.strip():
        request = "Crea una funzione che calcola Fibonacci"
        
    final_code = orchestrator.run_pipeline(request)
    
    print("--- RISULTATO FINALE (Codice Confuc-IO) ---")
    print(final_code)
    print("-------------------------------------------")

if __name__ == "__main__":
    main()
