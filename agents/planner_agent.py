from typing import Dict, Any
from agents.base_agent import BaseAgent
from llm.client import LLMClient
from prompts.planner_prompts import PLANNER_SYSTEM_PROMPT, PLANNER_USER_PROMPT_TEMPLATE

class PlannerAgent(BaseAgent):
    def __init__(self, client: LLMClient):
        super().__init__(client)

    def generate_plan(self, user_request: str) -> Dict[str, Any]:
        print(f"[PlannerAgent] Ricevuta richiesta: '{user_request}'")
        
        prompt = PLANNER_USER_PROMPT_TEMPLATE.format(user_request=user_request)
        
        try:
            response = self.client.generate(prompt=prompt, system_prompt=PLANNER_SYSTEM_PROMPT)
            return self._extract_json(response)
        except Exception as e:
            print(f"[PlannerAgent] Errore durante la generazione del piano: {e}")
            raise e
