import json
import re
from typing import Dict, Any
from agents.base_agent import BaseAgent
from agents.llm_client import LLMClient
from prompts.generator_prompts import GENERATOR_SYSTEM_PROMPT, GENERATOR_USER_PROMPT_TEMPLATE

class GeneratorAgent(BaseAgent):
    def __init__(self, client: LLMClient):
        super().__init__(client)

    def generate_code(self, plan: Dict[str, Any], qa_feedback: str = None) -> str:
        print(f"[GeneratorAgent] Inizio generazione codice per il goal: '{plan.get('goal', 'Sconosciuto')}'")
        if qa_feedback:
            print("[GeneratorAgent] Ricevuto feedback QA. Auto-correzione in corso...")
            
        plan_json_str = json.dumps(plan, indent=2)
        feedback_str = f"ATTENZIONE - ERRORE DA CORREGGERE:\n{qa_feedback}" if qa_feedback else ""
        
        prompt = GENERATOR_USER_PROMPT_TEMPLATE.format(
            plan_json=plan_json_str,
            qa_feedback=feedback_str
        )
        
        try:
            response = self.client.generate(prompt=prompt, system_prompt=GENERATOR_SYSTEM_PROMPT)
            return self._extract_code(response)
        except Exception as e:
            print(f"[GeneratorAgent] Errore durante la chiamata LLM: {e}")
            raise e

    def _extract_code(self, raw_response: str) -> str:
        match = re.search(r"```(?:\w+)?\n(.*?)```", raw_response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return raw_response.strip()
