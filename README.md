# Can Parties Rely on It?

**AI-assisted outcome prediction and the duty to verify in investment arbitration**

> Status: **Phase 0 — data reconnaissance** (work in progress, October 2026)

## Research question

AI tools are increasingly presented as able to predict the outcome of arbitral proceedings, and parties may decide whether to settle on the strength of such predictions. For a party to act on a prediction, it is not enough that the tool is often right. The confidence it states has to match reality: of the cases it calls "70% likely", roughly 70% should actually end that way.

This repository tests that property — **calibration** — for (i) conventional machine-learning models trained on structural case features and (ii) large language models asked to predict outcomes and state their confidence, using publicly known treaty-based investor–state disputes. The results support a legal argument, made in an accompanying paper, about counsel's duty to verify AI output when advising on settlement.

Prior outcome-prediction studies in investment arbitration report accuracy. This project reports whether stated probabilities can be relied on.

## Data

UNCTAD, *Investment Dispute Settlement Navigator: full data release as of 31/12/2023 (excel format)*, available at <https://investmentpolicy.unctad.org/investment-dispute-settlement>.

The raw file is not redistributed here. Download it and place it at `data/raw/isds_navigator.xlsx` (see `DECISIONS.md` D-01 for the download date and terms).

## Repository layout

```
src/        analysis scripts, run in numeric order
results/    script outputs and working memos
figures/    plots
prompts/    LLM prompts, verbatim and versioned
data/       raw (not tracked) and processed data
DECISIONS.md    every modelling choice, dated, with reasons and alternatives
LIMITATIONS.md  known limits of the data and design
```

## Pipeline

| Step | Script | Status |
|---|---|---|
| 0. Reconnaissance | `src/01_explore.py` | in progress |
| 1. Preparation (labels, features, time split) | `src/02_prepare.py` | — |
| 2. Baselines and ML models | `src/03_models.py` | — |
| 3. LLM predictions with stated confidence | `src/04_llm.py` | — |
| 4. Calibration analysis | `src/05_calibration.py` | — |

## Findings

To be added.

## Reproducing

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/01_explore.py
```

Full reproduction steps will be added when the pipeline is complete.

## AI assistance

Code was drafted with AI assistance. Every output was checked against a manual baseline rather than accepted as produced, and all modelling decisions and the reasons for them are recorded in `DECISIONS.md`.

## Context

Final paper for *Alternative Dispute Resolution* (Kookmin University College of Law, Fall 2026).
