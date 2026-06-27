import json
from typing import Dict, Any, TypedDict, List
from langgraph.graph import StateGraph, START, END

from agents.planner_agent import PlannerAgent
from agents.generator_agent import GeneratorAgent
from agents.validator_agent import ValidatorAgent
from agents.repair_agent import RepairAgent
from agents.llm_client import MockLLMClient, AzureLLMClient, OllamaClient
import config

class GraphState(TypedDict):
    user_request: str
    plan_json: Dict[str, Any]
    generated_code: str
    
    syntax_errors: List[Dict[str, Any]]
    semantic_errors: List[Dict[str, Any]]
    logic_errors: List[Dict[str, Any]]
    error_report: Dict[str, Any]
    
    error_message: str
    retry_count: int

class Orchestrator:
    def __init__(self):
        """
        Orchestrator for the ConfuC-IO code generation pipeline with LangGraph.
        Selects the LLM client based on environment configuration:
          - USE_MOCK=true  → MockLLMClient (no API required, for testing)
          - AZURE_OPENAI_API_KEY → AzureLLMClient (uses Azure OpenAI API)
        """
        if config.USE_MOCK:
            print("[Orchestrator] Using MOCK LLM Client")
            client = MockLLMClient()
            self.logic_client = MockLLMClient()
        elif config.AZURE_OPENAI_API_KEY:
            print(f"[Orchestrator] Using AZURE OPENAI Client ({config.AZURE_OPENAI_DEPLOYMENT})")
            client = AzureLLMClient(
                api_key=config.AZURE_OPENAI_API_KEY,
                endpoint=config.AZURE_OPENAI_ENDPOINT,
                api_version=config.AZURE_OPENAI_API_VERSION,
                deployment_name=config.AZURE_OPENAI_DEPLOYMENT
            )
            print(f"[Orchestrator] Using OLLAMA Client ({config.OLLAMA_MODEL}) for logic validation")
            self.logic_client = OllamaClient(
                base_url=config.OLLAMA_BASE_URL,
                model=config.OLLAMA_MODEL
            )
        else:
            raise ValueError(
                "No LLM configured. Set USE_MOCK=true or provide AZURE_OPENAI_API_KEY in your .env file."
            )

        self.planner = PlannerAgent(client=client)
        self.generator = GeneratorAgent(client=client)
        self.validator = ValidatorAgent()
        self.repair = RepairAgent(client=client)
        
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(GraphState)

        workflow.add_node("planner_node", self._planner_node)
        workflow.add_node("generator_node", self._generator_node)
        workflow.add_node("syntax_validation_node", self._syntax_validation_node)
        workflow.add_node("semantic_validation_node", self._semantic_validation_node)
        workflow.add_node("logic_validation_node", self._logic_validation_node)
        workflow.add_node("repair_node", self._repair_node)

        workflow.add_edge(START, "planner_node")
        workflow.add_edge("planner_node", "generator_node")
        workflow.add_edge("generator_node", "syntax_validation_node")

        workflow.add_conditional_edges(
            "syntax_validation_node",
            self._route_after_syntax,
            {
                "semantic_validation_node": "semantic_validation_node",
                "repair_node": "repair_node",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "semantic_validation_node",
            self._route_after_semantic,
            {
                "repair_node": "repair_node",
                "logic_validation_node": "logic_validation_node",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "logic_validation_node",
            self._route_after_logic,
            {
                "repair_node": "repair_node",
                "end": END
            }
        )
        
        workflow.add_edge("repair_node", "syntax_validation_node")

        return workflow.compile()

    def _planner_node(self, state: GraphState) -> Dict[str, Any]:
        print("[Orchestrator] Esecuzione nodo: planner_node")
        try:
            plan = self.planner.generate_plan(state["user_request"])
            return {"plan_json": plan}
        except Exception as e:
            return {"error_message": f"Errore nel Planner: {str(e)}"}

    def _generator_node(self, state: GraphState) -> Dict[str, Any]:
        if state.get("error_message"):
            print("[Orchestrator] Salto generator_node causa errore fatale precedente.")
            return {}

        print("[Orchestrator] Esecuzione nodo: generator_node")
        try:
            code = self.generator.generate_code(state["plan_json"])
            return {"generated_code": code, "syntax_errors": [], "semantic_errors": []}
        except Exception as e:
            return {"error_message": f"Errore nel Generator: {str(e)}"}

    def _syntax_validation_node(self, state: GraphState) -> Dict[str, Any]:
        if state.get("error_message"): return {}
        print("[Orchestrator] Esecuzione nodo: syntax_validation_node")

        # Auto-correct common LLM delimiter mistakes before parsing
        from agents.confucio_parser import sanitize_confucio_code
        sanitized = sanitize_confucio_code(state["generated_code"])

        errors = self.validator.validate_syntax(sanitized)
        errors_list = [err.model_dump() for err in errors]

        result = {"syntax_errors": errors_list}
        # Propagate sanitized code so repair and semantic nodes see the fixed version
        if sanitized != state["generated_code"]:
            result["generated_code"] = sanitized
        return result

    def _semantic_validation_node(self, state: GraphState) -> Dict[str, Any]:
        if state.get("error_message"): return {}
        print("[Orchestrator] Esecuzione nodo: semantic_validation_node")
        
        errors = self.validator.validate_semantics(state["generated_code"])
        errors_list = [err.model_dump() for err in errors]
        return {"semantic_errors": errors_list}
        
    def _repair_node(self, state: GraphState) -> Dict[str, Any]:
        if state.get("error_message"): return {}
        print("[Orchestrator] Esecuzione nodo: repair_node")
        
        from agents.diagnostics import ValidationReport, DiagnosticError
        
        all_errors = []
        if state.get("syntax_errors"):
            all_errors.extend([DiagnosticError(**err) for err in state["syntax_errors"]])
        if state.get("semantic_errors"):
            all_errors.extend([DiagnosticError(**err) for err in state["semantic_errors"]])
        if state.get("logic_errors"):
            all_errors.extend([DiagnosticError(**err) for err in state["logic_errors"]])
            
        report = ValidationReport(is_valid=False, errors=all_errors)
        result = self.repair.repair_code(state["generated_code"], report)
        
        new_retry = state.get("retry_count", 0) + 1
        print(f"[Orchestrator] Repair Agent applicato. Tentativo {new_retry}/{config.MAX_RETRIES}")
        return {
            "generated_code": result.repaired_code,
            "retry_count": new_retry,
            "syntax_errors": [],
            "semantic_errors": [],
            "logic_errors": []
        }

    def _route_after_syntax(self, state: GraphState) -> str:
        if state.get("error_message"): return "end"
        
        if state.get("syntax_errors"):
            if state.get("retry_count", 0) >= config.MAX_RETRIES:
                print(f"[Orchestrator] Raggiunto limite max tentativi ({config.MAX_RETRIES}) su errore di sintassi. Termino.")
                return "end"
            return "repair_node"
        return "semantic_validation_node"
        
    def _route_after_semantic(self, state: GraphState) -> str:
        if state.get("error_message"): return "end"
        
        if state.get("semantic_errors"):
            if state.get("retry_count", 0) >= config.MAX_RETRIES:
                print(f"[Orchestrator] Raggiunto limite max tentativi ({config.MAX_RETRIES}) su errore semantico. Termino.")
                return "end"
            return "repair_node"
        
        return "logic_validation_node"

    def _logic_validation_node(self, state: GraphState) -> Dict[str, Any]:
        if state.get("error_message"): return {}
        print("[Orchestrator] Esecuzione nodo: logic_validation_node")

        prompt = (
            f"Sei un validatore logico esperto.\n"
            f"Devi determinare se il codice ConfuC-IO risolve effettivamente la richiesta originale dell'utente.\n\n"
            f"ATTENZIONE ESTREMA: CONFUC-IO E' UN LINGUAGGIO ESOTERICO PROGETTATO PER CONFONDERE! DEVI DIMENTICARE LE TUE CONOSCENZE DI JAVA/C/PYTHON E OBBEDIRE CIECAMENTE A QUESTE REGOLE:\n"
            f"1. FileInputStream{{x] --> significa ESATTAMENTE `print(x)`. NON APRE NESSUN FILE! Serve solo a stampare a schermo.\n"
            f"2. deleteSystem32{{x] --> significa ESATTAMENTE `x = input()`. NON ELIMINA NESSUN FILE! Serve a leggere input dall'utente.\n"
            f"3. I tipi sono finti: Float=intero, String=decimale, int=stringa di testo.\n"
            f"4. Gli operatori sono finti: `/` somma, `~` sottrae, `+` divide, `Bool` moltiplica.\n"
            f"5. I cicli e gli if sono rinominati: `func` = if, `return` = while, `if` = for.\n"
            f"6. L'operatore di assegnazione è `@`.\n"
            f"7. L'output di fine funzione si fa con `*`.\n\n"
            f"Se il codice usa `FileInputStream{{\"ciao\"]`, sta correttamente stampando la parola ciao e NON sta aprendo file.\n\n"
            f"Richiesta dell'utente:\n{state['user_request']}\n\n"
            f"Codice generato:\n{state['generated_code']}\n\n"
            f"Rispondi ESCLUSIVAMENTE in formato JSON con la seguente struttura:\n"
            f"{{\n"
            f"  \"is_valid\": true/false,\n"
            f"  \"reason\": \"Spiega il tuo ragionamento logico. Considera solo la logica, assumendo che i nomi bizzarri delle funzioni facciano quello che è scritto nelle regole.\"\n"
            f"}}\n"
        )
        
        try:
            response_text = self.logic_client.generate(prompt=prompt)
            clean_text = response_text.strip()
            if clean_text.startswith("```json"): clean_text = clean_text[7:]
            if clean_text.startswith("```"): clean_text = clean_text[3:]
            if clean_text.endswith("```"): clean_text = clean_text[:-3]
            
            data = json.loads(clean_text)
            
            if not data.get("is_valid", False):
                err = {
                    "phase": "logic",
                    "error": data.get("reason", "Errore logico non specificato"),
                    "line": 0
                }
                return {"logic_errors": [err]}
            
            return {"logic_errors": []}
            
        except Exception as e:
            # Se la validazione fallisce per errori di connessione/parsing JSON, procediamo senza bloccare
            print(f"[Orchestrator] Impossibile validare la logica: {e}")
            return {"logic_errors": []}

    def _route_after_logic(self, state: GraphState) -> str:
        if state.get("error_message"): return "end"
        
        if state.get("logic_errors"):
            if state.get("retry_count", 0) >= config.MAX_RETRIES:
                print(f"[Orchestrator] Raggiunto limite max tentativi ({config.MAX_RETRIES}) su errore logico. Termino.")
                return "end"
            return "repair_node"
            
        print("[Orchestrator] Validazione sintattica, semantica e logica superate con successo!")
        return "end"

    def run_pipeline(self, user_request: str) -> str:
        print("\n" + "="*40)
        print("INIZIO PIPELINE ORCHESTRATOR (LANGGRAPH + QA)")
        print("="*40)
        print(f"Richiesta Utente: {user_request}\n")

        initial_state = {
            "user_request": user_request,
            "plan_json": {},
            "generated_code": "",
            "error_message": "",
            "retry_count": 0,
            "syntax_errors": [],
            "semantic_errors": [],
            "logic_errors": [],
            "error_report": {}
        }

        final_state = self.graph.invoke(initial_state)

        if final_state.get("retry_count", 0) >= config.MAX_RETRIES and (final_state.get("syntax_errors") or final_state.get("semantic_errors") or final_state.get("logic_errors")):
            print(f"\nERRORE NON RISOLTO DOPO {config.MAX_RETRIES} TENTATIVI.")
            print("Ultimi errori:")
            all_final_errors = (final_state.get("syntax_errors") or []) + (final_state.get("semantic_errors") or []) + (final_state.get("logic_errors") or [])
            for err in all_final_errors:
                print(f"- {err['phase']} error: {err['error']} (line {err['line']})")
            
        if final_state.get("error_message"):
            print(f"\nERRORE NELLA PIPELINE: {final_state['error_message']}")
            return ""

        print("="*40)
        print("FINE PIPELINE ORCHESTRATOR")
        print("="*40 + "\n")
        
        return final_state.get("generated_code", "")
