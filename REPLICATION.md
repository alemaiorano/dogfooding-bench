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
| P95 Latency | 13.8s | [13.1s, 14.5s] |
| Safety Pass Rate | 100.0% | [100.0%, 100.0%] |

--- 

## Citation

If you use these artifacts in your research, please cite:

```text
Maiorano, A. (2026). Automated Self-Testing as a Quality Gate: Evidence-Driven Release Management for LLM Applications.
Preprint / submission-ready manuscript.
```
