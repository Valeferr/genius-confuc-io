import json
from typing import Dict, Any
from llm.client import LLMClient

class BaseAgent:
    """
    Classe base per gli agenti, fornisce client LLM e utilities come il parsing JSON robusto.
    """
    def __init__(self, client: LLMClient):
        self.client = client

    def _extract_json(self, response: str) -> Dict[str, Any]:
        """Estrae in modo robusto il JSON da una risposta testuale dell'LLM."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
            
        try:
            if "```json" in response:
                block = response.split("```json")[1].split("```")[0].strip()
                return json.loads(block)
            elif "```" in response:
                block = response.split("```")[1].split("```")[0].strip()
                return json.loads(block)
        except (json.JSONDecodeError, IndexError):
            pass
            
        try:
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1:
                json_str = response[start:end+1]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        raise ValueError("Impossibile estrarre un JSON valido dalla risposta.")
