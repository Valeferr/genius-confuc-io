"""
Test Requisito Esame — Calcolatrice Interattiva ConfuC-IO

Questo script verifica i requisiti della sezione 4 delle linee guida d'esame
per progetti di Compilatori/Generatori:

  - Mostrare un menu per la scelta di un'operazione aritmetica
  - Gestire input utente (interi o double)
  - Calcolare e restituire il risultato
  - Gestire un ciclo di continuazione
  - Utilizzare almeno due funzioni
  - Utilizzare tutte le caratteristiche del linguaggio

Uso:
    python test_exam_calculator.py              # con config da .env
    python test_exam_calculator.py --mock       # con MockLLMClient
    python test_exam_calculator.py --skip-gen   # solo validazione del codice di riferimento
"""

import sys
import os
import re
import argparse


if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from agents.validator_agent import ValidatorAgent
from core.parser import sanitize_confucio_code


REFERENCE_CODE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "calcolatrice.confucio")


CALCULATOR_PROMPT = (
    "Crea una calcolatrice interattiva con un menu che permette di scegliere "
    "tra somma, sottrazione, moltiplicazione e divisione. Il programma deve "
    "leggere due numeri in input, calcolare il risultato e chiedere se "
    "continuare con un'altra operazione o uscire. Usa almeno due funzioni."
)






class ExamRequirementChecker:
    """Verifica i requisiti specifici dell'esame sul codice ConfuC-IO."""

    def __init__(self):
        self.validator = ValidatorAgent()
        self.results = {}

    def check_all(self, code: str) -> dict:
        """Esegue tutti i controlli e restituisce un dizionario di risultati."""
        self.results = {}


        self.results["syntax"] = self._check_syntax(code)


        self.results["semantics"] = self._check_semantics(code)


        self.results["entry_point"] = self._check_entry_point(code)


        self.results["menu"] = self._check_menu(code)


        self.results["user_input"] = self._check_input(code)


        self.results["functions"] = self._check_functions(code)


        self.results["arithmetic_ops"] = self._check_arithmetic_ops(code)


        self.results["continuation_loop"] = self._check_loop(code)


        self.results["output"] = self._check_output(code)


        self.results["language_coverage"] = self._check_language_coverage(code)


        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r["passed"])
        self.results["_summary"] = {
            "total_checks": total,
            "passed_checks": passed,
            "score_percent": round(passed / total * 100, 1) if total > 0 else 0,
            "all_passed": passed == total
        }

        return self.results

    def _check_syntax(self, code: str) -> dict:
        sanitized = sanitize_confucio_code(code)
        errors = self.validator.validate_syntax(sanitized)
        return {
            "name": "Validità sintattica",
            "passed": len(errors) == 0,
            "details": [e.error for e in errors] if errors else ["Codice sintatticamente valido"]
        }

    def _check_semantics(self, code: str) -> dict:
        sanitized = sanitize_confucio_code(code)
        syn_errors = self.validator.validate_syntax(sanitized)
        if syn_errors:
            return {
                "name": "Validità semantica",
                "passed": False,
                "details": ["Impossibile verificare: errori di sintassi presenti"]
            }
        errors = self.validator.validate_semantics(sanitized)
        return {
            "name": "Validità semantica",
            "passed": len(errors) == 0,
            "details": [e.error for e in errors] if errors else ["Codice semanticamente valido"]
        }

    def _check_entry_point(self, code: str) -> dict:
        has_it = "Float side {] [" in code
        return {
            "name": "Entry point (Float side {] [)",
            "passed": has_it,
            "details": ["Entry point trovato"] if has_it else ["Entry point mancante"]
        }

    def _check_menu(self, code: str) -> dict:

        menu_prints = re.findall(r'FileInputStream\{["\'][^"\']*["\']', code)

        menu_options = [m for m in menu_prints if any(
            kw in m.lower() for kw in ["somma", "sottraz", "moltiplic", "divis", "esci", "menu", "calcolatrice",
                                        "1", "2", "3", "4", "0"]
        )]
        has_menu = len(menu_options) >= 4
        return {
            "name": "Menu operazioni (≥4 opzioni)",
            "passed": has_menu,
            "details": [f"Trovate {len(menu_options)} voci di menu"] + menu_options[:6]
        }

    def _check_input(self, code: str) -> dict:
        inputs = re.findall(r'deleteSystem32\{(\w+)]', code)
        has_input = len(inputs) >= 1
        return {
            "name": "Gestione input utente",
            "passed": has_input,
            "details": [f"Trovati {len(inputs)} input: {', '.join(set(inputs))}"] if inputs else ["Nessun input trovato"]
        }

    def _check_functions(self, code: str) -> dict:
        func_blocks = re.findall(r'\bfunc\s*\{[^]]*\]', code)
        count = len(func_blocks)
        passed = count >= 2
        return {
            "name": "Almeno 2 funzioni (blocchi func)",
            "passed": passed,
            "details": [f"Trovati {count} blocchi func (richiesti ≥2)"] +
                       [f"  → {fb.strip()[:60]}" for fb in func_blocks[:6]]
        }

    def _check_arithmetic_ops(self, code: str) -> dict:
        has_add = bool(re.search(r'\w\s*/\s*\w', code))
        has_sub = bool(re.search(r'\w\s*~\s*\w', code))
        has_mul = bool(re.search(r'\w\s*Bool\s*\w', code))
        has_div = bool(re.search(r'\w\s*\+\s*\w', code))

        ops = {
            "/ (addizione)": has_add,
            "~ (sottrazione)": has_sub,
            "Bool (moltiplicazione)": has_mul,
            "+ (divisione)": has_div
        }
        all_present = all(ops.values())
        found = [k for k, v in ops.items() if v]
        missing = [k for k, v in ops.items() if not v]

        return {
            "name": "Tutti e 4 gli operatori aritmetici",
            "passed": all_present,
            "details": [f"Trovati: {', '.join(found)}"] +
                       ([f"Mancanti: {', '.join(missing)}"] if missing else [])
        }

    def _check_loop(self, code: str) -> dict:
        has_while = bool(re.search(r'\breturn\s*\{', code))
        has_for = bool(re.search(r'\bif\s*\{[^]]*;[^]]*;[^]]*\]', code))
        has_loop = has_while or has_for
        loop_type = []
        if has_while: loop_type.append("while (return)")
        if has_for: loop_type.append("for (if)")

        return {
            "name": "Ciclo di continuazione",
            "passed": has_loop,
            "details": [f"Cicli trovati: {', '.join(loop_type)}"] if loop_type else ["Nessun ciclo trovato"]
        }

    def _check_output(self, code: str) -> dict:
        outputs = re.findall(r'FileInputStream\{', code)

        var_outputs = re.findall(r'FileInputStream\{(\w+)]', code)
        has_result_output = len(var_outputs) > 0
        return {
            "name": "Output risultato (FileInputStream)",
            "passed": has_result_output,
            "details": [f"Trovate {len(outputs)} stampe, di cui {len(var_outputs)} di variabili: {', '.join(set(var_outputs))}"]
        }

    def _check_language_coverage(self, code: str) -> dict:
        features = {
            "Tipo Float (int)": bool(re.search(r'\bFloat\b', code)),
            "Tipo int (string)": bool(re.search(r'\bint\b', code)),
            "Tipo String (float)": bool(re.search(r'\bString\b', code)),
            "Assegnazione @": "@" in code,
            "Input deleteSystem32": "deleteSystem32" in code,
            "Output FileInputStream": "FileInputStream" in code,
            "Condizionale func": bool(re.search(r'\bfunc\s*\{', code)),
            "Ciclo return (while)": bool(re.search(r'\breturn\s*\{', code)),
            "Ciclo if (for)": bool(re.search(r'\bif\s*\{[^]]*;', code)),
            "Return *": bool(re.search(r'\*\s*\w', code)),
            "Commenti È": "È" in code,
            "Entry point Float side": "Float side" in code,
            "Operatore / (add)": bool(re.search(r'\w\s*/\s*\w', code)),
            "Operatore ~ (sub)": bool(re.search(r'\w\s*~\s*\w', code)),
            "Operatore Bool (mul)": bool(re.search(r'\w\s*Bool\s*\w', code)),
            "Operatore + (div)": bool(re.search(r'\w\s*\+\s*\w', code)),
            "Confronto @@ (==)": "@@" in code,
            "Confronto = (>)": bool(re.search(r'\w\s*=\s*\d', code)),
            "Confronto # (<)": bool(re.search(r'\w\s*#\s*\w', code)),
        }

        found = [k for k, v in features.items() if v]
        missing = [k for k, v in features.items() if not v]
        coverage = len(found) / len(features) * 100 if features else 0

        return {
            "name": f"Copertura linguaggio ({coverage:.0f}%)",
            "passed": coverage >= 60,
            "details": [
                f"Feature usate: {len(found)}/{len(features)} ({coverage:.0f}%)",
                f"Presenti: {', '.join(found)}",
            ] + ([f"Non usate: {', '.join(missing)}"] if missing else [])
        }






def print_report(results: dict, title: str):
    """Stampa il report formattato a console."""
    print(f"\n{'═' * 70}")
    print(f"  {title}")
    print(f"{'═' * 70}\n")

    for key, value in results.items():
        if key.startswith("_"):
            continue
        icon = "✅" if value["passed"] else "❌"
        name = value["name"]
        print(f"  {icon}  {name}")
        for detail in value.get("details", []):
            print(f"       {detail}")
        print()

    summary = results.get("_summary", {})
    if summary:
        total = summary["total_checks"]
        passed = summary["passed_checks"]
        score = summary["score_percent"]
        all_ok = summary["all_passed"]

        print(f"{'─' * 70}")
        status = "✅ TUTTI I REQUISITI SODDISFATTI" if all_ok else "❌ REQUISITI NON COMPLETAMENTE SODDISFATTI"
        print(f"  {status}")
        print(f"  Score: {passed}/{total} ({score}%)")
        print(f"{'═' * 70}\n")






def main():
    parser = argparse.ArgumentParser(
        description="Test Requisito Esame - Calcolatrice Interattiva ConfuC-IO"
    )
    parser.add_argument("--mock", action="store_true", help="Forza l'uso del MockLLMClient")
    parser.add_argument("--skip-gen", action="store_true", help="Salta la generazione e valida solo il codice di riferimento")
    parser.add_argument("--verbose", action="store_true", help="Mostra il codice generato")
    args = parser.parse_args()

    if args.mock:
        config.USE_MOCK = True

    checker = ExamRequirementChecker()


    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║  TEST REQUISITO ESAME - Calcolatrice Interattiva           ║")
    print("║  Sezione 4 delle linee guida d'esame                       ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    print("\n📋 PARTE 1: Validazione codice di riferimento")
    print(f"   File: {REFERENCE_CODE_PATH}")

    try:
        with open(REFERENCE_CODE_PATH, "r", encoding="utf-8") as f:
            reference_code = f.read()
    except FileNotFoundError:
        print(f"   ❌ File di riferimento non trovato: {REFERENCE_CODE_PATH}")
        sys.exit(1)

    ref_results = checker.check_all(reference_code)
    print_report(ref_results, "CODICE DI RIFERIMENTO — calcolatrice.confucio")

    if not ref_results["_summary"]["all_passed"]:
        print("⚠️  Il codice di riferimento non supera tutti i controlli!")

    if args.skip_gen:
        print("⏭️  Generazione saltata (--skip-gen)")
        return


    print("\n📋 PARTE 2: Generazione codice tramite pipeline")
    print(f"   Client: {'MOCK' if config.USE_MOCK else 'AZURE/OLLAMA'}")
    print(f"   Prompt: \"{CALCULATOR_PROMPT[:80]}...\"")

    from agents.orchestrator import Orchestrator
    print("\n🔧 Inizializzazione Orchestrator...")
    orchestrator = Orchestrator()

    print("🚀 Esecuzione pipeline...\n")
    try:
        generated_code = orchestrator.run_pipeline(CALCULATOR_PROMPT)
    except Exception as e:
        print(f"❌ Errore durante la generazione: {e}")
        generated_code = ""

    if args.verbose or not generated_code:
        print("\n--- Codice Generato ---")
        print(generated_code if generated_code else "(vuoto)")
        print("--- Fine Codice ---\n")

    if not generated_code:
        print("❌ La pipeline non ha generato codice. Test fallito.")
        return

    gen_results = checker.check_all(generated_code)
    print_report(gen_results, "CODICE GENERATO DALLA PIPELINE")


    print("\n📋 PARTE 3: Confronto Riferimento vs Generato\n")
    ref_score = ref_results["_summary"]["score_percent"]
    gen_score = gen_results["_summary"]["score_percent"]

    print(f"  Codice di riferimento:  {ref_score}%")
    print(f"  Codice generato:        {gen_score}%")
    print(f"  Differenza:             {gen_score - ref_score:+.1f}%")

    if gen_score >= 80:
        print("\n  ✅ Il codice generato soddisfa i requisiti d'esame (≥80%)")
    elif gen_score >= 50:
        print("\n  ⚠️  Il codice generato soddisfa parzialmente i requisiti (≥50%)")
    else:
        print("\n  ❌ Il codice generato non soddisfa i requisiti d'esame (<50%)")

    print()


if __name__ == "__main__":
    main()
