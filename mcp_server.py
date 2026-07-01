from mcp.server.fastmcp import FastMCP
from agents.orchestrator import Orchestrator


mcp = FastMCP("ConfuC-IO Server")

@mcp.tool()
def generate_confucio_code(task: str) -> str:
    """Genera codice nel linguaggio esoterico ConfuC-IO a partire da una richiesta."""
    orchestrator = Orchestrator()
    return orchestrator.run_pipeline(task)

@mcp.resource("info://confuc-io")
def get_confucio_info() -> str:
    """Restituisce le specifiche e le regole del linguaggio ConfuC-IO."""
    return """
REGOLE DEL LINGUAGGIO CONFUC-IO:
- Tipi: 'Float' significa numero intero, 'int' significa stringa, 'String' significa numero decimale, 'While' significa booleano.
- Assegnazione: si usa '@' (es. 'Float x @ 5').
- Operatori Matematici: '/' è l'addizione, '~' è la sottrazione, '+' è la divisione, 'Bool' è la moltiplicazione.
- Operatori Logici: '=' è maggiore (>), '#' è minore (<), '@@' è uguale (==), '!@' è diverso (!=).
- Delimitatori invertiti: '{' rimpiazza '(', ']' rimpiazza ')', '[' rimpiazza '{', ')' rimpiazza '}'.
- Strutture di controllo (tutte rinominate): 'func' è l'if-statement, 'return' è il ciclo while, 'if' è il ciclo for.
- Ritorno funzione: si usa '* espressione'.
- I/O (RINOMINATI): 'FileInputStream{...' si usa per STAMPARE (è l'equivalente di print). 'deleteSystem32{...' si usa per LEGGERE UN INPUT (è l'equivalente di scanf/input, modifica la variabile e non ritorna nulla).
- Il programma DEVE sempre iniziare con 'Float side {] [' e terminare con '* 0 )'.
"""

@mcp.prompt()
def coding_workflow(task: str = "un programma") -> str:
    """Prompt per avviare una sessione di assistenza su ConfuC-IO."""
    from mcp.types import UserMessage, TextContent
    
    return [
        UserMessage(
            content=TextContent(
                type="text",
                text=f"Sei un assistente specializzato nel linguaggio esoterico ConfuC-IO.\nIl task è: {task}\n\nTi chiedo di analizzare il task e poi utilizzare il tool `generate_confucio_code` per generare il programma completo. \nConsidera che il generatore sfrutta una complessa pipeline LangGraph multi-agente per assicurarsi che il codice sia sintatticamente e logicamente corretto."
            )
        )
    ]

if __name__ == "__main__":
    mcp.run()
