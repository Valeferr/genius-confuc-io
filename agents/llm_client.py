import json
from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = None) -> str:
        pass


class MockLLMClient(LLMClient):
    """
    Dummy client to test the pipeline without consuming API tokens.
    """
    def generate(self, prompt: str, system_prompt: str = None, model: str = None) -> str:
        print(f"[MockLLM] Generating response for prompt of {len(prompt)} chars...")
        prompt_lower = prompt.lower()

        # Mock for Planner
        if "generare il piano" in prompt_lower or "planning" in (system_prompt or "").lower() or "planner" in (system_prompt or "").lower():
            if "fibonacci" in prompt_lower:
                return json.dumps({
                    "goal": "Calcolare il numero di Fibonacci per un dato N",
                    "variables": [{"name": "n", "type": "Int"}, {"name": "a", "type": "Int"}, {"name": "b", "type": "Int"}, {"name": "temp", "type": "Int"}, {"name": "i", "type": "Int"}],
                    "steps": ["1. Chiedi input", "2. Inizializza", "3. Ciclo", "4. Stampa"]
                })
            elif "fattoriale" in prompt_lower:
                return json.dumps({
                    "goal": "Calcolare il fattoriale",
                    "variables": [{"name": "n", "type": "Int"}, {"name": "res", "type": "Int"}, {"name": "i", "type": "Int"}],
                    "steps": ["1. Chiedi input", "2. Ciclo", "3. Stampa"]
                })
            elif "hello" in prompt_lower:
                return json.dumps({
                    "goal": "Stampare Hello World",
                    "variables": [{"name": "msg", "type": "String"}],
                    "steps": ["1. Crea stringa", "2. Stampa"]
                })
            elif "conto alla rovescia" in prompt_lower or "countdown" in prompt_lower:
                return json.dumps({
                    "goal": "Conteggio alla rovescia",
                    "variables": [{"name": "n", "type": "Int"}],
                    "steps": ["1. Chiedi input", "2. Ciclo while decrescente", "3. Stampa"]
                })

            return json.dumps({
                "goal": "Eseguire la richiesta: " + prompt[:50],
                "variables": [{"name": "risultato", "type": "String"}],
                "steps": ["1. Esegui logica", "2. Restituisci"]
            })

        # Mock for Generator
        if "traduci questo piano" in prompt_lower or "generator" in (system_prompt or "").lower():
            if "fattoriale" in prompt_lower:
                return "```confucio\nInt n @ deleteSystem32()\nInt res @ 1\nfunc (n < 2) {\n    * 1\n}\nInt i @ 2\nif (i @ 2; i < n / 1; i @ i / 1) {\n    res @ res * i\n}\nFileInputStream(\"Fattoriale: \")\nFileInputStream(res)\n* res\n```"
            elif "hello" in prompt_lower:
                return "```confucio\nString msg @ \"Hello, World!\"\nFileInputStream(msg)\n```"
            elif "conteggio" in prompt_lower or "countdown" in prompt_lower:
                return "```confucio\nInt n @ deleteSystem32()\nreturn (n > 0) {\n    FileInputStream(n)\n    n @ n - 1\n}\nFileInputStream(\"Go!\")\n```"

            # Default case (Fibonacci) — intentional syntax error for repair loop testing
            print("[MockLLM] Generating code with intentional SYNTAX error (+ instead of /)")
            return "```confucio\nInt n @ deleteSystem32()\nInt a @ 0\nInt b @ 1\nInt temp @ 0\nfunc (n < 1) {\n    FileInputStream(a)\n    * a\n}\nfunc (n < 2) {\n    FileInputStream(b)\n    * b\n}\nInt i @ 0\nif (i @ 0; i < n - 1; i @ i + 1) {\n    temp @ b\n    b @ a + b\n    a @ temp\n}\nFileInputStream(b)\n* b\n```"

        # Mock for Repair Agent
        if "expert compiler engineer and repair agent" in (system_prompt or "").lower():
            print("[MockLLM] Received compiler error. Generating REPAIRED code as JSON.")
            return json.dumps({
                "repaired_code": "String n @ deleteSystem32()\nInt a @ 0\nInt b @ 1\nInt temp @ 0\nfunc (n < 1) {\n    FileInputStream(a)\n    * a\n}\nfunc (n < 2) {\n    FileInputStream(b)\n    * b\n}\nInt i @ 0\nif (i @ 0; i < n - 1; i @ i / 1) {\n    temp @ b\n    b @ a / b\n    a @ temp\n}\nFileInputStream(b)\n* b",
                "explanation": "Replaced invalid '+' operators with '/' as per ConfuC-IO grammar."
            })

        return "Generic Mock Response"


class AzureLLMClient(LLMClient):
    def __init__(self, api_key: str, endpoint: str, api_version: str, model: str):
        self.model = model
        try:
            from openai import AzureOpenAI
            self.client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=endpoint,
                api_version=api_version
            )
        except ImportError:
            raise ImportError("Library 'openai' not found. Run: pip install openai")

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()
