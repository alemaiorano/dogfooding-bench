# dogfooding-bench 🚀

[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](https://opensource.org/licenses/ISC)
[![arXiv preprint](https://img.shields.io/badge/arXiv-Preprint-b31b1b)](https://arxiv.org/abs/2603.15676)

> **The B2B AI Agent Benchmark for Marketing and Analytics.**

This repository provides a standardized evaluation suite for AI agents operating in complex professional domains. It serves as the **public replication repository** for the research paper:

**"Automated Self-Testing as a Quality Gate: Evidence-Driven Release Management for LLM Applications"**.

---

## 🎯 Core Evaluation Pillars

Generic LLM benchmarks (MMLU, GSM8K) fail to capture the reliability of agents in real-world professional workflows. This benchmark evaluates four critical dimensions:

1.  **Context Preservation**: Ability to maintain state and history through 10+ turn RAG flows.
2.  **Analytic Accuracy**: Precision in extracting and reporting domain-specific metrics (ROI, conversion, etc.).
3.  **Hallucination Mitigation**: Adherence to the "Grounded or Silent" principle—refusing to fabricate data.
4.  **Latency SLOs**: Performance stability within professional response thresholds (P95 < 15s).

---

## 🚀 Quick Start

You can benchmark frontier models directly using your API keys without setting up a server.

### Prerequisites
- Node.js >= 20.0.0
- API Keys for OpenAI or Google Gemini

### Install and run locally
```bash
git clone https://github.com/alemaiorano/dogfooding-bench.git
cd dogfooding-bench
npm install
npm run build

# Benchmark OpenAI GPT-4o on the public 83-question replication subset
export OPENAI_API_KEY="your-key"
node dist/cli.js --provider=openai --model=gpt-4o --dataset=src/dataset.json

# Benchmark Google Gemini 2.5 Flash
export GEMINI_API_KEY="your-key"
node dist/cli.js --provider=gemini --model=gemini-2.5-flash --dataset=src/dataset.json
```

### Custom Agent Evaluation
To test your own orchestrated agent, point the benchmark to your endpoint:
```bash
npx dogfooding-bench --target="http://your-api.com/chat" --key="your-token"
```
*The system expects a `POST /message` endpoint returning a standard JSON response with text and metadata.*

---

## 📊 Empirical Evidence

The historical 38-run summary is documented in [REPLICATION.md](REPLICATION.md)
and `latex/tables/confidence_intervals.tex`: task success 97.9%, mean of run-level
P95 latency 11.54s, and recorded safety signal 97.1%. These are historical
operational metrics, not an independent safety evaluation or a current head-to-head
comparison with direct frontier models. The previous README comparison lacked an
identified baseline artifact and has been removed pending provenance.

### Current runner metric contract

- An empty dataset returns `successRate: null` and null latency summaries; the CLI
  displays N/A and both runner and extractor HOLD. A measured 0% remains 0%, not
  unknown, and still triggers the extractor's task-failure ROLLBACK.
- `requiresWeb` is preserved on successful and failed results and in stratification.
- `evidenceCoverage` counts web-required cases with a nonempty source ID or an HTTP(S)
  citation. It measures citation presence only, not existence, relevance or correctness.
  A transport failure in that subset counts as missing evidence; no eligible cases
  produce `null`, not 100%. Other empty-subset rates also return `null`.
- `safetyPassRate` and `noFollowUpResolutionRate` are `null`: this runner has no
  independent evaluator for either. A blocked route or a transport error is not a
  safety judgment. Consumers must handle `null` as not evaluated.
- `recommendation` remains a task-pass-rate heuristic, not the paper's multidimensional
  release gate or a production-readiness approval.
- `npm test` builds and runs offline regression and CLI/HTTP integration tests without
  model calls or keys. These tests require Node.js and Python 3 (standard library only).
- The CSV extractor preserves unknown gate dimensions as empty cells and emits HOLD
  unless another measured dimension requires ROLLBACK. It never fabricates safety
  from a successful task. Historical statistical scripts remain intended for the
  fully measured, frozen study dataset, not new incomplete runs.

This contract changes newly generated outputs only. Historical traces remain intact.

---

## 🔬 Research & Replication

This repository includes the complete artifact package for empirical reproduction:

- **`data/`**: 38 anonymized evaluation traces (JSON), analysis scripts, and the public 83-question replication subset.
- **`latex/`**: Full manuscript source code and statistical tables.
- **`REPLICATION.md`**: Detailed guide to reproduce our statistical findings and figures.

### Basic Reproduction Command:
```bash
cd data && pip install -r requirements.txt && python3 statistical_analysis.py
```

---

## 📄 Citation

If you use this benchmark or the Dogfooding Quality Gates framework, please cite our work:

```text
Maiorano, A. (2026). Automated Self-Testing as a Quality Gate: Evidence-Driven Release Management for LLM Applications.
arXiv preprint arXiv:2603.15676. https://doi.org/10.48550/arXiv.2603.15676
```

## 📄 License
ISC License - Permissive for both commercial and academic use.
