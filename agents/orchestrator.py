import json
from typing import Dict, Any, TypedDict, List
from langgraph.graph import StateGraph, START, END

from agents.planner_agent import PlannerAgent
from agents.generator_agent import GeneratorAgent
from agents.qa_agent import QAAgent
from agents.llm_client import MockLLMClient, RealLLMClient, GitHubModelsClient, OllamaClient
import config

# Definiamo lo stato globale del grafo per LangGraph (inclusi campi futuri per Valentina)
class GraphState(TypedDict):
    user_request: str
    plan_json: Dict[str, Any]
    generated_code: str
    
    # Campi futuri per Valentina (Syntax/Semantic Validation, Repair)
    syntax_errors: List[Dict[str, Any]]
    semantic_errors: List[Dict[str, Any]]
    error_report: Dict[str, Any]
    
    qa_feedback: str
    error_message: str
    retry_count: int

class Orchestrator:
    def __init__(self, use_mock: bool = None, api_key: str = None, github_token: str = None, use_ollama: bool = False):
        """
        Orchestrator Base per la pipeline di generazione codice Confuc-IO con LangGraph.
        """
        if use_mock is None:
            use_mock = config.USE_MOCK
            
        if use_mock:
            print("[Orchestrator] Utilizzo MOCK LLM Client")
            self.client = MockLLMClient()
        elif use_ollama:
            print("[Orchestrator] Utilizzo OLLAMA Client")
            self.client = OllamaClient()
        elif github_token or config.GITHUB_TOKEN:
            print("[Orchestrator] Utilizzo GITHUB MODELS Client")
            self.client = GitHubModelsClient(github_token=(github_token or config.GITHUB_TOKEN))
        else:
            print("[Orchestrator] Utilizzo REAL LLM Client (OpenAI)")
            key = api_key or config.OPENAI_API_KEY
            if not key:
                raise ValueError("Nessuna API Key fornita per OpenAI.")
            self.client = RealLLMClient(api_key=key)
        
        # Inizializzazione degli agenti
        self.planner = PlannerAgent(client=self.client)
        self.generator = GeneratorAgent(client=self.client)
        self.qa = QAAgent()
        
        # Costruzione del grafo LangGraph
        self.graph = self._build_graph()

    def _build_graph(self):
        # 1. Inizializza lo StateGraph
        workflow = StateGraph(GraphState)

        # 2. Aggiunge i nodi
        workflow.add_node("planner_node", self._planner_node)
        workflow.add_node("generator_node", self._generator_node)
        workflow.add_node("qa_node", self._qa_node)

        # Nodi futuri (Valentina li implementerà)
        # workflow.add_node("syntax_validation_node", self._syntax_validation_node)
        # workflow.add_node("semantic_validation_node", self._semantic_validation_node)
        # workflow.add_node("repair_node", self._repair_node)

        # 3. Definisce gli archi
        workflow.add_edge(START, "planner_node")
        workflow.add_edge("planner_node", "generator_node")
        workflow.add_edge("generator_node", "qa_node")

        # 4. Definisce gli archi condizionali post QA
        workflow.add_conditional_edges(
            "qa_node",
            self._route_after_qa,
            {
                "generator_node": "generator_node",
                "end": END
            }
        )

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
            code = self.generator.generate_code(state["plan_json"], qa_feedback=state.get("qa_feedback"))
            return {"generated_code": code}
        except Exception as e:
            return {"error_message": f"Errore nel Generator: {str(e)}"}

    def _qa_node(self, state: GraphState) -> Dict[str, Any]:
        if state.get("error_message"):
            return {}

        print("[Orchestrator] Esecuzione nodo: qa_node")
        validation = self.qa.validate(state["generated_code"])
        
        if not validation["is_valid"]:
            new_retry = state.get("retry_count", 0) + 1
            return {
                "qa_feedback": validation["error"],
                "retry_count": new_retry
            }
        else:
            print("[Orchestrator] QA superato con successo!")
            return {"qa_feedback": ""}

    # --- Routing Condizionale ---
    def _route_after_qa(self, state: GraphState) -> str:
        if state.get("error_message"):
            return "end"
        
        if state.get("qa_feedback"):
            if state.get("retry_count", 0) >= config.MAX_RETRIES:
                print(f"[Orchestrator] Raggiunto limite max tentativi ({config.MAX_RETRIES}). Termino il flusso.")
                return "end"
            else:
                print(f"[Orchestrator] Auto-correzione necessaria. Torno al generator_node (Tentativo {state.get('retry_count', 0)}/{config.MAX_RETRIES}).")
                return "generator_node"
        
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
            "qa_feedback": "",
            "error_message": "",
            "retry_count": 0,
            "syntax_errors": [],
            "semantic_errors": [],
            "error_report": {}
        }

        final_state = self.graph.invoke(initial_state)

        if final_state.get("qa_feedback") and final_state.get("retry_count", 0) >= config.MAX_RETRIES:
            print(f"\n❌ ERRORE SINTATTICO NON RISOLTO:\n{final_state['qa_feedback']}")
            
        if final_state.get("error_message"):
            print(f"\n❌ ERRORE NELLA PIPELINE: {final_state['error_message']}")
            return ""

        print("="*40)
        print("✅ FINE PIPELINE ORCHESTRATOR")
        print("="*40 + "\n")
        
        return final_state.get("generated_code", "")
