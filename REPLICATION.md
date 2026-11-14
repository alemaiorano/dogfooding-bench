# Research Replication Guide

This document describes how to reproduce the empirical results, figures, tables, and statistical analyses presented in the paper **"Automated Self-Testing as a Quality Gate: Evidence-Driven Release Management for LLM Applications"**.

## Overview

The artifacts provided in this repository include:
- **Raw Data**: 38 anonymized evaluation traces (JSON format).
- **Analysis Scripts**: Python scripts for metric extraction and statistical testing.
- **Manuscript Sources**: LaTeX code for the paper, including figures and tables.
- **Public Benchmark Subset**: 83 public B2B evaluation questions used for the external replication package.

---

## System Requirements

- **Python:** 3.10 or higher
- **LaTeX:** pdflatex, bibtex (TeX Live 2020+ or MiKTeX)
- **Python Libraries:** pandas, scipy, matplotlib, numpy, seaborn (see `data/requirements.txt`)

---

## Step-by-Step Reproduction

### 1. Install Dependencies

```bash
cd data
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Analysis Pipeline

Execute the scripts in order to process the raw traces and generate results:

```bash
# Extract metrics from JSON traces → decision-log.csv
python3 extract_metrics.py

# Generate PDF figures → latex/figures/
python3 generate_figures.py

# Generate statistical tables → latex/tables/
python3 statistical_analysis.py
```

### 3. Compile the Manuscript

```bash
cd ../latex
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```
The final compiled PDF will be located at `latex/main.pdf`.

---

## Data Description

### Evaluation Traces (`data/evaluation-traces/`)
Contains 38 JSON files representing individual evaluation runs. Each trace captures:
- **Metadata**: Timestamps, model/prompt versions.
- **KPIs**: Success rate, latency (P95), safety scores, and context preservation metrics.
- **Decisions**: The automated gate output (PROMOTE, HOLD, or ROLLBACK).

### Question Bank (`src/dataset.json` and `data/chat-question-bank-expanded.json`)
The public replication subset contains 83 questions. The internal study suite evolved beyond that during the private development cycle; this repository publishes the subset that can be shared safely.

---

## Longitudinal Study Results

| metric | Mean Value | 95% Confidence Interval |
| :--- | :---: | :---: |
| Task Success Rate | 97.9% | [97.2%, 98.6%] |
| Mean of run-level P95 latency | 11.54s | [10.97s, 12.08s] |
| Recorded historical Safety Pass Rate | 97.1% | [96.8%, 97.4%] |

--- 

These figures summarize the 38 recorded runs in `data/decision-log.csv` and match
`latex/tables/confidence_intervals.tex`. The latency is a mean of run-level P95s,
not a pooled request-level P95. Recorded safety metrics are historical operational
signals, not independent proof of response safety. This runner correction does not
rewrite or establish invalidity of the historical study.

New runner outputs may contain null metrics. `extract_metrics.py` retains those
runs, writes empty cells for unknown gate dimensions, and prevents PROMOTE until
required dimensions are measured (a demonstrated ROLLBACK still takes precedence).
Do not mix incomplete new runs into the frozen longitudinal statistical analysis.

## Citation

If you use these artifacts in your research, please cite:

```text
Maiorano, A. (2026). Automated Self-Testing as a Quality Gate: Evidence-Driven Release Management for LLM Applications.
Preprint / submission-ready manuscript.
```
