# 📊 Benchmark Report - genius-confuc-io

**Data**: 2026-07-01 14:51:52
**Test eseguiti**: 11

## Risultati per Test Case

| ID | Nome | Sintassi | Semantica | Snippet | Costrutti | Struttura | **Score** |
|------|------|----------|-----------|---------|-----------|-----------|-----------|
| TC-001 | Fibonacci | ✅ | ✅ | 60% | 50% | 80% | **79.5%** |
| TC-002 | Fattoriale | ✅ | ✅ | 67% | 25% | 60% | **74.4%** |
| TC-003 | Hello World | ✅ | ✅ | 100% | 100% | 100% | **100.0%** |
| TC-004 | Somma | ✅ | ✅ | 100% | 100% | 100% | **100.0%** |
| TC-005 | Countdown | ✅ | ✅ | 100% | 100% | 100% | **100.0%** |
| TC-006 | Stampa ciao | ✅ | ✅ | 0% | 100% | 100% | **75.0%** |
| TC-007 | Massimo tra due numeri | ✅ | ✅ | 100% | 100% | 100% | **100.0%** |
| TC-008 | Somma da 1 a N | ❌ | ❌ | 50% | 33% | 60% | **26.5%** |
| TC-009 | Pari o Dispari | ✅ | ✅ | 100% | 100% | 100% | **100.0%** |
| TC-010 | Tabellina | ✅ | ✅ | 71% | 67% | 100% | **87.9%** |
| TC-011 | Calcolatrice Interattiva | ✅ | ❌ | 100% | 100% | 100% | **80.0%** |

### Score Medio Complessivo: **83.9%**

## Dettaglio Errori e Snippet Mancanti

### TC-001 - Fibonacci
**Snippet mancanti:**
  - `func {`
  - `if {`
**Costrutti mancanti:**
  - `if`
  - `func`

### TC-002 - Fattoriale
**Snippet mancanti:**
  - `if {`
  - `FileInputStream{`
**Costrutti mancanti:**
  - `FileInputStream`
  - `if`
  - `func`

### TC-006 - Stampa ciao
**Snippet mancanti:**
  - `FileInputStream{"ciao"]`

### TC-008 - Somma da 1 a N
**Errori di sintassi:**
  - `Unexpected token Token('AT', '@') at line 4, column 42.
Expected one of: 
	* TILDE
	* COMPARE_OP
	* RSQB
	* BOOL
	* PLUS
	* SLASH
Previous tokens: [Token('CNAME', 'somma')]
`
**Errori di semantica:**
  - `Impossibile validare semantica: errori di sintassi presenti`
**Snippet mancanti:**
  - `deleteSystem32{`
  - `if {`
  - ` / `
**Costrutti mancanti:**
  - `deleteSystem32`
  - `if`

### TC-010 - Tabellina
**Snippet mancanti:**
  - `if {`
  - ` / `
**Costrutti mancanti:**
  - `if`

### TC-011 - Calcolatrice Interattiva
**Errori di semantica:**
  - `Type mismatch: cannot assign 'Float' to variable 'continuare' of type 'While'`

## Pesi delle Metriche

| Metrica | Peso |
|---------|------|
| syntax_valid | 25% |
| semantic_valid | 20% |
| snippet_match | 25% |
| construct_coverage | 15% |
| structural_match | 15% |
