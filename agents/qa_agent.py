from agents.confucio_parser import validate_code

class QAAgent:
    def __init__(self):
        """
        Inizializza il QA Agent, che in questo caso è deterministico 
        (utilizza l'AST parser per validare la sintassi).
        """
        pass

    def validate(self, generated_code: str) -> dict:
        """
        Riceve in input il codice generato.
        Ritorna un dizionario con 'is_valid' (bool) e 'error' (str).
        """
        print("[QAAgent] Analisi sintattica deterministica in corso (Lark AST)...")
        
        try:
            # Tenta di validare il codice
            ast = validate_code(generated_code)
            return {
                "is_valid": True,
                "error": None
            }
        except Exception as e:
            error_msg = f"Errore Sintattico (Lark AST):\n{str(e)}"
            print(f"[QAAgent] Rilevato errore nel codice: {error_msg}")
            return {
                "is_valid": False,
                "error": error_msg
            }
