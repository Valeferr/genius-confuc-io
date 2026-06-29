"""
Benchmark Runner per genius-confuc-io.

Esegue automaticamente la pipeline di generazione codice ConfuC-IO
per ogni prompt nel dataset di benchmark e valuta l'accuratezza
del codice generato rispetto al riferimento atteso.

Uso:
    python benchmark_runner.py                  # usa config da .env
    python benchmark_runner.py --mock           # forza MockLLMClient
    python benchmark_runner.py --verbose        # mostra codice generato
    python benchmark_runner.py --test TC-001    # esegue solo un test
"""

import json
import sys
import os
import argparse
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

# Fix encoding per Windows (cp1252 non supporta caratteri Unicode)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Assicura che il progetto sia nel path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from agents.orchestrator import Orchestrator
from agents.validator_agent import ValidatorAgent


# ═══════════════════════════════════════════════════════════════
# Costanti e pesi delle metriche
# ═══════════════════════════════════════════════════════════════

METRIC_WEIGHTS = {
    "syntax_valid": 0.25,
    "semantic_valid": 0.20,
    "snippet_match": 0.25,
    "construct_coverage": 0.15,
    "structural_match": 0.15,
}

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "benchmark.json")
RESULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "benchmark_results.json")
REPORT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "benchmark_report.md")


# ═══════════════════════════════════════════════════════════════
# Classe Evaluator
# ═══════════════════════════════════════════════════════════════

class BenchmarkEvaluator:
    """Valuta il codice ConfuC-IO generato rispetto al test case di riferimento."""

    def __init__(self):
        self.validator = ValidatorAgent()

    def evaluate(self, generated_code: str, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue tutte le metriche di valutazione per un singolo test case."""
        results = {}

        # 1. Validità sintattica
        results["syntax_valid"] = self._check_syntax(generated_code)

        # 2. Validità semantica
        results["semantic_valid"] = self._check_semantics(generated_code)

        # 3. Snippet match
        snippets = test_case.get("expected_code_snippets", [])
        results["snippet_match"] = self._check_snippets(generated_code, snippets)

        # 4. Construct coverage
        criteria = test_case.get("evaluation_criteria", {})
        expected_constructs = criteria.get("expected_constructs", [])
        results["construct_coverage"] = self._check_constructs(generated_code, expected_constructs)

        # 5. Structural match
        results["structural_match"] = self._check_structure(generated_code, criteria)

        # Score complessivo
        results["overall_score"] = self._compute_overall_score(results)

        return results

    def _check_syntax(self, code: str) -> Dict[str, Any]:
        """Verifica la validità sintattica."""
        try:
            from core.parser import sanitize_confucio_code
            sanitized = sanitize_confucio_code(code)
        except ImportError:
            sanitized = code

        errors = self.validator.validate_syntax(sanitized)
        return {
            "passed": len(errors) == 0,
            "score": 1.0 if len(errors) == 0 else 0.0,
            "errors": [e.error for e in errors]
        }

    def _check_semantics(self, code: str) -> Dict[str, Any]:
        """Verifica la validità semantica (solo se la sintassi è OK)."""
        # Prima verifica che la sintassi passi
        try:
            from core.parser import sanitize_confucio_code
            sanitized = sanitize_confucio_code(code)
        except ImportError:
            sanitized = code

        syntax_errors = self.validator.validate_syntax(sanitized)
        if syntax_errors:
            return {
                "passed": False,
                "score": 0.0,
                "errors": ["Impossibile validare semantica: errori di sintassi presenti"],
                "skipped": True
            }

        errors = self.validator.validate_semantics(sanitized)
        return {
            "passed": len(errors) == 0,
            "score": 1.0 if len(errors) == 0 else 0.0,
            "errors": [e.error for e in errors],
            "skipped": False
        }

    def _check_snippets(self, code: str, expected_snippets: List[str]) -> Dict[str, Any]:
        """Verifica quanti degli snippet attesi sono presenti nel codice."""
        if not expected_snippets:
            return {"passed": True, "score": 1.0, "matched": [], "missing": [], "total": 0}

        # Normalizza spazi per confronto più flessibile
        normalized_code = self._normalize_whitespace(code)
        matched = []
        missing = []

        for snippet in expected_snippets:
            normalized_snippet = self._normalize_whitespace(snippet)
            if normalized_snippet in normalized_code:
                matched.append(snippet)
            else:
                missing.append(snippet)

        score = len(matched) / len(expected_snippets)
        return {
            "passed": score == 1.0,
            "score": round(score, 4),
            "matched": matched,
            "missing": missing,
            "total": len(expected_snippets)
        }

    def _check_constructs(self, code: str, expected_constructs: List[str]) -> Dict[str, Any]:
        """Verifica la presenza dei costrutti ConfuC-IO attesi."""
        if not expected_constructs:
            return {"passed": True, "score": 1.0, "found": [], "missing": [], "total": 0}

        found = []
        missing = []

        for construct in expected_constructs:
            if construct in code:
                found.append(construct)
            else:
                missing.append(construct)

        score = len(found) / len(expected_constructs)
        return {
            "passed": score == 1.0,
            "score": round(score, 4),
            "found": found,
            "missing": missing,
            "total": len(expected_constructs)
        }

    def _check_structure(self, code: str, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica le proprietà strutturali del codice."""
        if not criteria:
            return {"passed": True, "score": 1.0, "checks": {}}

        checks = {}
        total_checks = 0
        passed_checks = 0

        # Verifica entry point
        if "has_entry_point" in criteria:
            total_checks += 1
            has_it = "Float side {] [" in code or "Float side{][" in self._normalize_whitespace(code)
            checks["has_entry_point"] = {
                "expected": criteria["has_entry_point"],
                "actual": has_it,
                "passed": has_it == criteria["has_entry_point"]
            }
            if checks["has_entry_point"]["passed"]:
                passed_checks += 1

        # Verifica input (deleteSystem32)
        if "has_input" in criteria:
            total_checks += 1
            has_it = "deleteSystem32" in code
            checks["has_input"] = {
                "expected": criteria["has_input"],
                "actual": has_it,
                "passed": has_it == criteria["has_input"]
            }
            if checks["has_input"]["passed"]:
                passed_checks += 1

        # Verifica output (FileInputStream)
        if "has_output" in criteria:
            total_checks += 1
            has_it = "FileInputStream" in code
            checks["has_output"] = {
                "expected": criteria["has_output"],
                "actual": has_it,
                "passed": has_it == criteria["has_output"]
            }
            if checks["has_output"]["passed"]:
                passed_checks += 1

        # Verifica loop (if = for, return = while)
        if "has_loop" in criteria:
            total_checks += 1
            # "if" come for-loop: cerca pattern "if {... ; ... ; ...]"
            has_for = bool(re.search(r'\bif\s*\{[^]]*;[^]]*;[^]]*\]', code))
            # "return" come while-loop
            has_while = bool(re.search(r'\breturn\s*\{', code))
            has_it = has_for or has_while
            checks["has_loop"] = {
                "expected": criteria["has_loop"],
                "actual": has_it,
                "passed": has_it == criteria["has_loop"]
            }
            if checks["has_loop"]["passed"]:
                passed_checks += 1

        # Verifica condizionali (func = if)
        if "has_conditional" in criteria:
            total_checks += 1
            has_it = bool(re.search(r'\bfunc\s*\{', code))
            checks["has_conditional"] = {
                "expected": criteria["has_conditional"],
                "actual": has_it,
                "passed": has_it == criteria["has_conditional"]
            }
            if checks["has_conditional"]["passed"]:
                passed_checks += 1

        # Verifica numero minimo di blocchi func ("funzioni")
        if "min_func_blocks" in criteria:
            total_checks += 1
            func_count = len(re.findall(r'\bfunc\s*\{', code))
            min_required = criteria["min_func_blocks"]
            passed = func_count >= min_required
            checks["min_func_blocks"] = {
                "expected": min_required,
                "actual": func_count,
                "passed": passed
            }
            if passed:
                passed_checks += 1

        # Verifica presenza di tutti e 4 gli operatori aritmetici
        if "has_all_arithmetic_ops" in criteria and criteria["has_all_arithmetic_ops"]:
            total_checks += 1
            # / = addizione, ~ = sottrazione, Bool = moltiplicazione, + = divisione
            # Cerco pattern "espressione OP espressione" per evitare falsi positivi
            has_add = bool(re.search(r'\w\s*/\s*\w', code))       # a / b (addizione)
            has_sub = bool(re.search(r'\w\s*~\s*\w', code))       # a ~ b (sottrazione)
            has_mul = bool(re.search(r'\w\s*Bool\s*\w', code))    # a Bool b (moltiplicazione)
            has_div = bool(re.search(r'\w\s*\+\s*\w', code))      # a + b (divisione)
            all_ops = has_add and has_sub and has_mul and has_div
            ops_found = []
            if has_add: ops_found.append("/ (add)")
            if has_sub: ops_found.append("~ (sub)")
            if has_mul: ops_found.append("Bool (mul)")
            if has_div: ops_found.append("+ (div)")
            checks["has_all_arithmetic_ops"] = {
                "expected": True,
                "actual": all_ops,
                "ops_found": ops_found,
                "passed": all_ops
            }
            if all_ops:
                passed_checks += 1

        score = passed_checks / total_checks if total_checks > 0 else 1.0
        return {
            "passed": score == 1.0,
            "score": round(score, 4),
            "checks": checks
        }

    def _compute_overall_score(self, results: Dict[str, Any]) -> float:
        """Calcola lo score complessivo come media pesata."""
        total = 0.0
        for metric_name, weight in METRIC_WEIGHTS.items():
            metric_result = results.get(metric_name, {})
            score = metric_result.get("score", 0.0)
            total += score * weight
        return round(total * 100, 2)

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Normalizza spazi multipli in singolo spazio per confronto."""
        return re.sub(r'\s+', ' ', text.strip())


# ═══════════════════════════════════════════════════════════════
# Funzioni di caricamento e salvataggio
# ═══════════════════════════════════════════════════════════════

def load_benchmark(path: str) -> List[Dict[str, Any]]:
    """Carica i test case dal file benchmark.json."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("benchmarks", [])


def save_results(results: List[Dict[str, Any]], path: str):
    """Salva i risultati dettagliati in JSON."""
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_tests": len(results),
        "results": results
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Risultati salvati in: {path}")


def generate_report(results: List[Dict[str, Any]], path: str):
    """Genera un report Markdown leggibile."""
    lines = []
    lines.append("# 📊 Benchmark Report - genius-confuc-io")
    lines.append("")
    lines.append(f"**Data**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Test eseguiti**: {len(results)}")
    lines.append("")

    # Tabella riassuntiva
    lines.append("## Risultati per Test Case")
    lines.append("")
    lines.append("| ID | Nome | Sintassi | Semantica | Snippet | Costrutti | Struttura | **Score** |")
    lines.append("|------|------|----------|-----------|---------|-----------|-----------|-----------|")

    overall_scores = []
    for r in results:
        tc_id = r["test_case_id"]
        tc_name = r["test_case_name"]
        ev = r.get("evaluation", {})

        syn = "✅" if ev.get("syntax_valid", {}).get("passed") else "❌"
        sem = "✅" if ev.get("semantic_valid", {}).get("passed") else "❌"

        snip_score = ev.get("snippet_match", {}).get("score", 0)
        snip = f"{snip_score*100:.0f}%"

        cons_score = ev.get("construct_coverage", {}).get("score", 0)
        cons = f"{cons_score*100:.0f}%"

        stru_score = ev.get("structural_match", {}).get("score", 0)
        stru = f"{stru_score*100:.0f}%"

        overall = ev.get("overall_score", 0)
        overall_scores.append(overall)
        score_str = f"**{overall:.1f}%**"

        lines.append(f"| {tc_id} | {tc_name} | {syn} | {sem} | {snip} | {cons} | {stru} | {score_str} |")

    lines.append("")

    # Media complessiva
    if overall_scores:
        avg = sum(overall_scores) / len(overall_scores)
        lines.append(f"### Score Medio Complessivo: **{avg:.1f}%**")
    lines.append("")

    # Dettaglio per ogni test case con errori o snippet mancanti
    lines.append("## Dettaglio Errori e Snippet Mancanti")
    lines.append("")

    for r in results:
        ev = r.get("evaluation", {})
        tc_id = r["test_case_id"]
        tc_name = r["test_case_name"]

        has_issues = False
        issues = []

        # Errori di sintassi
        syn_errors = ev.get("syntax_valid", {}).get("errors", [])
        if syn_errors:
            has_issues = True
            issues.append("**Errori di sintassi:**")
            for e in syn_errors:
                issues.append(f"  - `{e}`")

        # Errori di semantica
        sem_errors = ev.get("semantic_valid", {}).get("errors", [])
        if sem_errors:
            has_issues = True
            issues.append("**Errori di semantica:**")
            for e in sem_errors:
                issues.append(f"  - `{e}`")

        # Snippet mancanti
        missing = ev.get("snippet_match", {}).get("missing", [])
        if missing:
            has_issues = True
            issues.append("**Snippet mancanti:**")
            for s in missing:
                issues.append(f"  - `{s}`")

        # Costrutti mancanti
        cons_missing = ev.get("construct_coverage", {}).get("missing", [])
        if cons_missing:
            has_issues = True
            issues.append("**Costrutti mancanti:**")
            for c in cons_missing:
                issues.append(f"  - `{c}`")

        if has_issues:
            lines.append(f"### {tc_id} - {tc_name}")
            for issue in issues:
                lines.append(issue)
            lines.append("")

    # Legenda pesi
    lines.append("## Pesi delle Metriche")
    lines.append("")
    lines.append("| Metrica | Peso |")
    lines.append("|---------|------|")
    for name, weight in METRIC_WEIGHTS.items():
        lines.append(f"| {name} | {weight*100:.0f}% |")
    lines.append("")

    report_content = "\n".join(lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"📝 Report salvato in: {path}")


# ═══════════════════════════════════════════════════════════════
# Funzione di stampa risultati a console
# ═══════════════════════════════════════════════════════════════

def print_results_table(results: List[Dict[str, Any]]):
    """Stampa la tabella dei risultati a console."""
    print("\n" + "━" * 90)
    print(f"{'ID':<8} {'Nome':<22} {'Sintassi':^10} {'Semantica':^10} {'Snippet':^10} {'Costrutti':^10} {'Struttura':^10} {'Score':^8}")
    print("━" * 90)

    overall_scores = []
    for r in results:
        ev = r.get("evaluation", {})
        tc_id = r["test_case_id"]
        tc_name = r["test_case_name"][:20]

        syn = "✅" if ev.get("syntax_valid", {}).get("passed") else "❌"
        sem = "✅" if ev.get("semantic_valid", {}).get("passed") else "❌"

        snip_score = ev.get("snippet_match", {}).get("score", 0)
        cons_score = ev.get("construct_coverage", {}).get("score", 0)
        stru_score = ev.get("structural_match", {}).get("score", 0)
        overall = ev.get("overall_score", 0)
        overall_scores.append(overall)

        print(f"{tc_id:<8} {tc_name:<22} {syn:^10} {sem:^10} {snip_score*100:>5.0f}%{'':<4} {cons_score*100:>5.0f}%{'':<4} {stru_score*100:>5.0f}%{'':<4} {overall:>5.1f}%")

    print("━" * 90)
    if overall_scores:
        avg = sum(overall_scores) / len(overall_scores)
        print(f"{'':>52} Score medio complessivo: {avg:.1f}%")
    print("━" * 90)


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Runner per genius-confuc-io: valuta l'accuratezza della generazione di codice ConfuC-IO."
    )
    parser.add_argument("--mock", action="store_true", help="Forza l'uso del MockLLMClient")
    parser.add_argument("--verbose", action="store_true", help="Mostra il codice generato per ogni test case")
    parser.add_argument("--test", type=str, default=None, help="Esegue solo il test case con l'ID specificato (es. TC-001)")
    args = parser.parse_args()

    # Se --mock, forza USE_MOCK a True
    if args.mock:
        config.USE_MOCK = True

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     BENCHMARK RUNNER - genius-confuc-io                     ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print(f"  Client: {'MOCK' if config.USE_MOCK else 'AZURE/OLLAMA'}")
    print(f"  Dataset: {DATASET_PATH}")
    print()

    # Carica dataset
    test_cases = load_benchmark(DATASET_PATH)
    print(f"📦 Caricati {len(test_cases)} test case dal dataset.")

    # Filtra se richiesto un singolo test
    if args.test:
        test_cases = [tc for tc in test_cases if tc["id"] == args.test]
        if not test_cases:
            print(f"❌ Test case '{args.test}' non trovato nel dataset.")
            sys.exit(1)
        print(f"🎯 Esecuzione filtrata: solo {args.test}")

    # Inizializza orchestrator e evaluator
    print("\n🔧 Inizializzazione Orchestrator...")
    orchestrator = Orchestrator()
    evaluator = BenchmarkEvaluator()

    # Esegui benchmark
    all_results = []
    total = len(test_cases)

    for idx, tc in enumerate(test_cases, 1):
        tc_id = tc["id"]
        tc_name = tc["name"]
        request = tc["user_request"]

        print(f"\n{'='*60}")
        print(f"[{idx}/{total}] {tc_id} - {tc_name}")
        print(f"  Prompt: \"{request}\"")
        print(f"{'='*60}")

        # Genera codice tramite la pipeline
        try:
            generated_code = orchestrator.run_pipeline(request)
        except Exception as e:
            print(f"  ⚠️  Errore durante la generazione: {e}")
            generated_code = ""

        if args.verbose:
            print(f"\n--- Codice Generato ---")
            print(generated_code if generated_code else "(vuoto)")
            print(f"--- Fine Codice ---\n")

        # Valuta il codice generato
        evaluation = evaluator.evaluate(generated_code, tc)

        result = {
            "test_case_id": tc_id,
            "test_case_name": tc_name,
            "user_request": request,
            "generated_code": generated_code,
            "evaluation": evaluation
        }
        all_results.append(result)

        # Stampa score del singolo test
        score = evaluation.get("overall_score", 0)
        syn_ok = "✅" if evaluation["syntax_valid"]["passed"] else "❌"
        sem_ok = "✅" if evaluation["semantic_valid"]["passed"] else "❌"
        print(f"  → Sintassi: {syn_ok} | Semantica: {sem_ok} | Score: {score:.1f}%")

    # Stampa tabella riassuntiva
    print_results_table(all_results)

    # Salva risultati e report
    save_results(all_results, RESULTS_PATH)
    generate_report(all_results, REPORT_PATH)

    print("\n✅ Benchmark completato!")


if __name__ == "__main__":
    main()
