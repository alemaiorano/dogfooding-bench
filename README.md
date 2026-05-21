# dogfooding-bench 🚀

[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](https://opensource.org/licenses/ISC)
[![Paper: EMSE](https://img.shields.io/badge/Paper-Submission--Ready-blue)](https://github.com/alemaiorano/dogfooding-bench)

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

Our research demonstrates that providing context via system prompts is insufficient for professional reliability. On the public 83-question replication subset, orchestrated agents with **Quality Gates** significantly outperform direct frontier-model baselines:

| Metric | Native Gemini 2.5 Flash | Orchestrated Agent (Paper) |
| :--- | :---: | :---: |
| **Success Rate** | ~49% | **98.2%** |
| **P95 Latency** | ~19.7s | **13.8s** |
| **Evidence Quality** | Unstructured | **Structured Citations** |
| **Tone/Conciseness** | Conversational | **Surgical / Professional** |

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
Preprint / submission-ready manuscript.
```

## 📄 License
ISC License - Permissive for both commercial and academic use.
