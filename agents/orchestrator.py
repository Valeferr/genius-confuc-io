import json
from typing import Dict, Any, TypedDict, List
from langgraph.graph import StateGraph, START, END

from agents.planner_agent import PlannerAgent
from agents.generator_agent import GeneratorAgent
from agents.validator_agent import ValidatorAgent
from agents.repair_agent import RepairAgent
from agents.llm_client import MockLLMClient, RealLLMClient, GitHubModelsClient, OllamaClient, HuggingFaceClient
import config

class GraphState(TypedDict):
    user_request: str
    plan_json: Dict[str, Any]
    generated_code: str
    
    # Syntax/Semantic Validation, Repair
    syntax_errors: List[Dict[str, Any]]
    semantic_errors: List[Dict[str, Any]]
    error_report: Dict[str, Any]
    
    error_message: str
    retry_count: int

class Orchestrator:
    def __init__(self):
        """
        Orchestrator for the ConfuC-IO code generation pipeline with LangGraph.
        Selects the LLM client based on environment configuration:
          - USE_MOCK=true  → MockLLMClient (no API required, for testing)
          - USE_MOCK=false → AzureLLMClient (requires Azure OpenAI credentials in .env)
        """
        if config.USE_MOCK:
            print("[Orchestrator] Using MOCK LLM Client")
            client = MockLLMClient()
        elif config.HF_TOKEN:
            print("[Orchestrator] Using HUGGINGFACE Client (GLM-5.2)")
            client = HuggingFaceClient(hf_token=config.HF_TOKEN)
        else:
            raise ValueError(
                "No LLM configured. Set USE_MOCK=true or provide HF_TOKEN in your .env file."
            )

        # Agents share a single client; ValidatorAgent is deterministic (uses Lark)
        self.planner = PlannerAgent(client=client)
        self.generator = GeneratorAgent(client=client)
        self.validator = ValidatorAgent()
        self.repair = RepairAgent(client=client)
        
        # Build LangGraph workflow
        self.graph = self._build_graph()

    def _build_graph(self):
        # 1. Inizializza lo StateGraph
        workflow = StateGraph(GraphState)

        # 2. Aggiunge i nodi
        workflow.add_node("planner_node", self._planner_node)
        workflow.add_node("generator_node", self._generator_node)
        workflow.add_node("syntax_validation_node", self._syntax_validation_node)
        workflow.add_node("semantic_validation_node", self._semantic_validation_node)
        workflow.add_node("repair_node", self._repair_node)

        # 3. Definisce gli archi
        workflow.add_edge(START, "planner_node")
        workflow.add_edge("planner_node", "generator_node")
        workflow.add_edge("generator_node", "syntax_validation_node")

        # 4. Definisce gli archi condizionali
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
                "end": END
            }
        )
        
        workflow.add_edge("repair_node", "syntax_validation_node")

        # 5. Compila il grafo
        return workflow.compile()

    # --- Funzioni Nodo ---
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
            # First generation step (qa_feedback is not used in the loop now, repair updates generated_code directly)
            code = self.generator.generate_code(state["plan_json"])
            return {"generated_code": code, "syntax_errors": [], "semantic_errors": []}
        except Exception as e:
            return {"error_message": f"Errore nel Generator: {str(e)}"}

    def _syntax_validation_node(self, state: GraphState) -> Dict[str, Any]:
        if state.get("error_message"): return {}
        print("[Orchestrator] Esecuzione nodo: syntax_validation_node")
        
        errors = self.validator.validate_syntax(state["generated_code"])
        errors_list = [err.model_dump() for err in errors]
        return {"syntax_errors": errors_list}

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
            
        report = ValidationReport(is_valid=False, errors=all_errors)
        result = self.repair.repair_code(state["generated_code"], report)
        
        new_retry = state.get("retry_count", 0) + 1
        print(f"[Orchestrator] Repair Agent applicato. Tentativo {new_retry}/{config.MAX_RETRIES}")
        return {
            "generated_code": result.repaired_code,
            "retry_count": new_retry,
            "syntax_errors": [],
            "semantic_errors": []
        }

    # --- Routing Condizionale ---
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
        
        print("[Orchestrator] Validazione sintattica e semantica superata con successo!")
        return "end"

    # --- Esecuzione Principale ---
    def run_pipeline(self, user_request: str) -> str:
        print("\n" + "="*40)
        print("🚀 INIZIO PIPELINE ORCHESTRATOR (LANGGRAPH + QA)")
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
            "error_report": {}
        }

        final_state = self.graph.invoke(initial_state)

        if final_state.get("retry_count", 0) >= config.MAX_RETRIES and (final_state.get("syntax_errors") or final_state.get("semantic_errors")):
            print(f"\n❌ ERRORE NON RISOLTO DOPO {config.MAX_RETRIES} TENTATIVI.")
            print("Ultimi errori:")
            for err in (final_state.get("syntax_errors") or []) + (final_state.get("semantic_errors") or []):
                print(f"- {err['phase']} error: {err['error']} (line {err['line']})")
            
        if final_state.get("error_message"):
            print(f"\n❌ ERRORE NELLA PIPELINE: {final_state['error_message']}")
            return ""

        print("="*40)
        print("✅ FINE PIPELINE ORCHESTRATOR")
        print("="*40 + "\n")
        
        return final_state.get("generated_code", "")
