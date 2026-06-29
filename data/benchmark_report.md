# 📊 Benchmark Report - genius-confuc-io

**Data**: 2026-06-29 12:12:59
**Test eseguiti**: 11

## Risultati per Test Case

| ID | Nome | Sintassi | Semantica | Snippet | Costrutti | Struttura | **Score** |
|------|------|----------|-----------|---------|-----------|-----------|-----------|
| TC-001 | Fibonacci | ✅ | ✅ | 20% | 25% | 60% | **62.8%** |
| TC-002 | Fattoriale | ✅ | ✅ | 67% | 25% | 60% | **74.4%** |
| TC-003 | Hello World | ✅ | ✅ | 100% | 100% | 100% | **100.0%** |
| TC-004 | Somma | ✅ | ✅ | 80% | 100% | 100% | **95.0%** |
| TC-005 | Countdown | ❌ | ❌ | 60% | 67% | 80% | **37.0%** |
| TC-006 | Stampa ciao | ✅ | ✅ | 0% | 100% | 100% | **75.0%** |
| TC-007 | Massimo tra due numeri | ✅ | ✅ | 100% | 100% | 100% | **100.0%** |
| TC-008 | Somma da 1 a N | ✅ | ✅ | 83% | 67% | 100% | **90.8%** |
| TC-009 | Pari o Dispari | ✅ | ✅ | 100% | 100% | 100% | **100.0%** |
| TC-010 | Tabellina | ✅ | ✅ | 71% | 67% | 100% | **87.9%** |
| TC-011 | Calcolatrice Interattiva | ✅ | ❌ | 100% | 100% | 100% | **80.0%** |

### Score Medio Complessivo: **82.1%**

## Dettaglio Errori e Snippet Mancanti

### TC-001 - Fibonacci
**Snippet mancanti:**
  - `deleteSystem32{`
  - `func {`
  - `if {`
  - ` / `
**Costrutti mancanti:**
  - `deleteSystem32`
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

### TC-004 - Somma
**Snippet mancanti:**
  - ` / `

### TC-005 - Countdown
**Errori di sintassi:**
  - `No terminal matches '`' in the current parser context, at line 1 col 1

```json
^
Expected one of: 
	* FLOAT
`
**Errori di semantica:**
  - `Impossibile validare semantica: errori di sintassi presenti`
**Snippet mancanti:**
  - ` ~ `
  - `FileInputStream{`
**Costrutti mancanti:**
  - `FileInputStream`

### TC-006 - Stampa ciao
**Snippet mancanti:**
  - `FileInputStream{"ciao"]`

### TC-008 - Somma da 1 a N
**Snippet mancanti:**
  - `if {`
**Costrutti mancanti:**
  - `if`

### TC-010 - Tabellina
**Snippet mancanti:**
  - `if {`
  - ` / `
**Costrutti mancanti:**
  - `if`

### TC-011 - Calcolatrice Interattiva
**Errori di semantica:**
  - `Type mismatch: cannot assign 'Float' to variable 'continua' of type 'While'`
  - `Type mismatch: cannot assign 'int' to variable 'operazione' of type 'String'`
  - `Type mismatch: cannot assign 'int' to variable 'risultato' of type 'Float'`

## Pesi delle Metriche

| Metrica | Peso |
|---------|------|
| syntax_valid | 25% |
| semantic_valid | 20% |
| snippet_match | 25% |
| construct_coverage | 15% |
| structural_match | 15% |
