import json
from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str = None, model: str = "gpt-4o") -> str:
        pass

class MockLLMClient(LLMClient):
    """
    Client fittizio per testare la pipeline senza consumare API.
    """
    def generate(self, prompt: str, system_prompt: str = None, model: str = None) -> str:
        print(f"[MockLLM] Generazione risposta per prompt di {len(prompt)} caratteri...")
        prompt_lower = prompt.lower()
        
        # Mock per il Planner
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

        # Mock per il Generator
        if "traduci questo piano" in prompt_lower or "generator" in (system_prompt or "").lower():
            if "fattoriale" in prompt_lower:
                return "```confucio\nInt n @ deleteSystem32()\nInt res @ 1\nfunc (n < 2) {\n    * 1\n}\nInt i @ 2\nif (i @ 2; i < n / 1; i @ i / 1) {\n    res @ res * i\n}\nFileInputStream(\"Fattoriale: \")\nFileInputStream(res)\n* res\n```"
            elif "hello" in prompt_lower:
                return "```confucio\nString msg @ \"Hello, World!\"\nFileInputStream(msg)\n```"
            elif "conteggio" in prompt_lower or "countdown" in prompt_lower:
                return "```confucio\nInt n @ deleteSystem32()\nreturn (n > 0) {\n    FileInputStream(n)\n    n @ n - 1\n}\nFileInputStream(\"Go!\")\n```"
            
            # Caso default (Fibonacci)
            # if "attenzione - errore da correggere" in prompt_lower:
            #    print("[MockLLM] Genero codice CORRETTO in seguito al feedback.")
            #    return "```confucio\nInt n @ deleteSystem32()\nInt a @ 0\nInt b @ 1\nInt temp @ 0\nfunc (n < 1) {\n    FileInputStream(a)\n    * a\n}\nfunc (n < 2) {\n    FileInputStream(b)\n    * b\n}\nInt i @ 0\nif (i @ 0; i < n - 1; i @ i / 1) {\n    temp @ b\n    b @ a / b\n    a @ temp\n}\nFileInputStream(b)\n* b\n```"
            print("[MockLLM] Genero codice con errore SINTATTICO intenzionale (+ al posto di /)")
            return "```confucio\nInt n @ deleteSystem32()\nInt a @ 0\nInt b @ 1\nInt temp @ 0\nfunc (n < 1) {\n    FileInputStream(a)\n    * a\n}\nfunc (n < 2) {\n    FileInputStream(b)\n    * b\n}\nInt i @ 0\nif (i @ 0; i < n - 1; i @ i + 1) {\n    temp @ b\n    b @ a + b\n    a @ temp\n}\nFileInputStream(b)\n* b\n```"

        # Mock per il Repair Agent
        if "expert compiler engineer and repair agent" in (system_prompt or "").lower():
            print("[MockLLM] Ricevuto errore dal compilatore. Genero codice RIPARATO in formato JSON.")
            return json.dumps({
                "repaired_code": "String n @ deleteSystem32()\nInt a @ 0\nInt b @ 1\nInt temp @ 0\nfunc (n < 1) {\n    FileInputStream(a)\n    * a\n}\nfunc (n < 2) {\n    FileInputStream(b)\n    * b\n}\nInt i @ 0\nif (i @ 0; i < n - 1; i @ i / 1) {\n    temp @ b\n    b @ a / b\n    a @ temp\n}\nFileInputStream(b)\n* b",
                "explanation": "L'operatore '+' non è valido per l'addizione nella grammatica di Confuc-IO. Ho sostituito tutti i '+' con '/' per eseguire l'addizione corretta."
            })

        return "Risposta Mock generica"

class RealLLMClient(LLMClient):
    def __init__(self, api_key: str):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        except ImportError:
            raise ImportError("Libreria 'openai' non trovata. Esegui: pip install openai")

    def generate(self, prompt: str, system_prompt: str = None, model: str = "gpt-4o") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=4000
        )
        return response.choices[0].message.content.strip()

class GitHubModelsClient(LLMClient):
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.base_url = "https://models.github.ai"
        try:
            import requests
            self.requests = requests
        except ImportError:
            raise ImportError("Libreria 'requests' non trovata. Esegui: pip install requests")

    def generate(self, prompt: str, system_prompt: str = None, model: str = "gpt-4o") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 4000
        }
        
        response = self.requests.post(
            f"{self.base_url}/inference/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception(f"Errore GitHub Models API {response.status_code}: {response.text}")
        
        return response.json()["choices"][0]["message"]["content"].strip()

class OllamaClient(LLMClient):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.default_model = model
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
            "model": model or self.default_model,
            "messages": messages,
            "stream": False
        }
        
        response = self.requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"Errore Ollama API {response.status_code}: {response.text}")
        
        return response.json().get("message", {}).get("content", "")
