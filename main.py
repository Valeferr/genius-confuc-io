import sys
from agents.orchestrator import Orchestrator

def main():
    print("Avvio del Sistema Multi-Agente ConfuC-IO")
    orchestrator = Orchestrator()
    
    request = "Crea una funzione che calcola Fibonacci"
    if len(sys.argv) > 1:
        request = " ".join(sys.argv[1:])
        
    final_code = orchestrator.run_pipeline(request)
    
    print("--- RISULTATO FINALE (Codice Confuc-IO) ---")
    print(final_code)
    print("-------------------------------------------")

if __name__ == "__main__":
    main()
