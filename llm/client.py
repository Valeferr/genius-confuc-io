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
            elif "conto alla rovescia" in prompt_lower or "countdown" in prompt_lower or "conta" in prompt_lower:
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

        if "traduci questo piano" in prompt_lower or "generator" in (system_prompt or "").lower():
            if "fattoriale" in prompt_lower:
                return "```confucio\nInt n @ deleteSystem32()\nInt res @ 1\nfunc (n < 2) {\n    * 1\n}\nInt i @ 2\nif (i @ 2; i < n / 1; i @ i / 1) {\n    res @ res * i\n}\nFileInputStream(\"Fattoriale: \")\nFileInputStream(res)\n* res\n```"
            elif "hello" in prompt_lower:
                return "```confucio\nString msg @ \"Hello, World!\"\nFileInputStream(msg)\n```"
            elif "conteggio" in prompt_lower or "countdown" in prompt_lower or "conta" in prompt_lower:
                return "```confucio\nInt n @ deleteSystem32()\nreturn (n > 0) {\n    FileInputStream(n)\n    n @ n - 1\n}\nFileInputStream(\"Go!\")\n```"

            print("[MockLLM] Generating code with intentional SYNTAX error (+ instead of /)")
            return "```confucio\nInt n @ deleteSystem32()\nInt a @ 0\nInt b @ 1\nInt temp @ 0\nfunc (n < 1) {\n    FileInputStream(a)\n    * a\n}\nfunc (n < 2) {\n    FileInputStream(b)\n    * b\n}\nInt i @ 0\nif (i @ 0; i < n - 1; i @ i + 1) {\n    temp @ b\n    b @ a + b\n    a @ temp\n}\nFileInputStream(b)\n* b\n```"

        if "expert compiler engineer and repair agent" in (system_prompt or "").lower():
            if "go!" in prompt_lower:
                return json.dumps({
                    "repaired_code": "Float n @ 10.0\nreturn (n > 0.0) {\n    FileInputStream(n)\n    n @ n - 1.0\n}\nFileInputStream(\"Go!\")",
                    "explanation": "Fixed types for semantic validation."
                })
            elif "fattoriale" in prompt_lower:
                return json.dumps({
                    "repaired_code": "String n @ deleteSystem32()\nFloat res @ 1.0\nfunc (n < 2.0) {\n    * 1.0\n}\nFloat i @ 2.0\nif (i @ 2.0; i < 10.0; i @ i / 1.0) {\n    res @ res * i\n}\nFileInputStream(\"Fattoriale: \")\nFileInputStream(res)\n* res",
                    "explanation": "Fixed Int to String mismatch for input and updated types to Float."
                })
            return json.dumps({
                "repaired_code": "String n @ deleteSystem32()\nInt a @ 0\nInt b @ 1\nInt temp @ 0\nfunc (n < 1) {\n    FileInputStream(a)\n    * a\n}\nfunc (n < 2) {\n    FileInputStream(b)\n    * b\n}\nFloat i @ 0.0\nif (i @ 0.0; i < 10.0; i @ i / 1.0) {\n    temp @ b\n    b @ a / b\n    a @ temp\n}\nFileInputStream(b)\n* b",
                "explanation": "Replaced invalid '+' operators with '/' and fixed Int to Float."
            })

        return "Generic Mock Response"


class AzureLLMClient(LLMClient):
    """
    Client per Azure OpenAI.
    Richiede la libreria 'openai' installata.
    """
    def __init__(self, api_key: str, endpoint: str, api_version: str, deployment_name: str):
        try:
            from openai import AzureOpenAI
        except ImportError:
            raise ImportError("Libreria 'openai' non trovata. Esegui: pip install openai")
            
        self.client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=endpoint
        )
        self.deployment_name = deployment_name

    def generate(self, prompt: str, system_prompt: str = None, model: str = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=model or self.deployment_name,
            messages=messages,
            temperature=0.2,
            max_tokens=4000,
        )
        print(f"[AzureLLMClient] Risposta ricevuta correttamente dal modello Azure OpenAI: {model or self.deployment_name}")
        return response.choices[0].message.content.strip()

class OllamaClient(LLMClient):
    """
    Client per Ollama in locale.
    """
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "codegemma:latest"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("Libreria 'requests' non trovata. Esegui: pip install requests")

    def generate(self, prompt: str, system_prompt: str = None, model: str = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.0
            }
        }
        
        response = self.requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"Errore Ollama {response.status_code}: {response.text}")
            
        print(f"[OllamaClient] Risposta ricevuta correttamente dal modello locale: {model or self.model}")
        return response.json()["message"]["content"].strip()
