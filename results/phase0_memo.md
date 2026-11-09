# Phase 0 reconnaissance memo

Date: 2026-10-25
Source output: `results/explore_report.txt`

## File

- File: `UNCTAD-ISDS-Navigator-data-set-31December2023.xlsx` ("Updated as of 31 December 2023")
- Downloaded: 2026-10-25
- Layout: sheet 1 = data, 11 note lines above the header (header row index 11); sheet 2 = disclaimer and terms
- Terms: file links to UNCTAD's general terms of use; redistribution not stated → raw file **not tracked** in git
- Total cases: **1,332** (matches UNCTAD's stated count) · 28 columns · initiation years 1987–2023
- A pilot run on the 31/07/2019 release (983 cases) used the same layout; one column was renamed (`BREACHES FOUND` → `IIA BREACHES FOUND`). The script handles both.

## Outcomes

| Outcome value | Count |
|---|---|
| Decided in favour of State | 361 |
| Pending | 354 |
| Decided in favour of investor | 268 |
| Settled | 177 |
| Discontinued for unknown reasons | 128 |
| Neither investor nor the State (liability found but no damages awarded) | 24 |
| Data not available | 20 |

- Concluded 958 / pending 354 / unknown 20
- **Ending in an award: 653** = investor 268 + State 361 + neither 24
  - State wins split by `IIA BREACHES FOUND`: jurisdiction declined **164** / all claims dismissed on the merits **188** / not available 9
- Settled 177 + discontinued 128 = **31.8%** of concluded cases (matches the ICSID 31% used in the paper)

**Gate: award cases ≥ 300 → PASS (653)**

| Label | n | Investor share |
|---|---|---|
| label_a — all award cases | 653 | 41.0% |
| label_b — excluding jurisdiction declined | 489 | 54.8% |

## Fields

- **Arbitrators**: one cell, `;`-separated, with roles (`Name - President; Name - Claimant; Name - Respondent`, or sole arbitrator). Missing 0.9% in award cases.
- **Years**: year of initiation only; no year of conclusion.
- **Amount claimed**: text (`3000.00 USD`, `11.00 EUR (12.50 USD)`); missing 11.8% in award cases.
- **Amount awarded**: present (missing 57.9% in award cases) — outcome information, **never a feature**.
- **IIA breaches alleged**: `;`-separated; missing 11.5% in award cases.
- **Forum (arbitral rules)**: ICSID 718 / UNCITRAL 411 / ICSID AF 76 / SCC 56 / ICC 26 / other or n.a. 45. Over a third not ICSID → LLM prompt uses `{forum}`.
- **Sector**: Tertiary 880 / Primary 255 / Secondary 175 / n.a. 22.
- **Respondents** in award cases: 109 States, 39 with ≥ 5 cases.
- No arbitrator nationality.

## Cutoff and right truncation — the main design finding

Investor share among award cases falls for recent cohorts:

| Initiated | Award cases | Investor share |
|---|---|---|
| before 2005 | 110 | 50.9% |
| 2005–09 | 131 | 41.2% |
| 2010–14 | 193 | 41.5% |
| 2015–19 | 204 | 37.3% |
| 2020–23 | 15 | 13.3% |

Recent cases that are already decided are mostly the fast ones, and fast cases are disproportionately jurisdictional dismissals:

| Initiated | Still pending | Jurisdiction declined, share of awards |
|---|---|---|
| 2010–13 | 4% | 26% |
| 2014–16 | 13% | 18% |
| 2017–19 | 38% | 34% |
| 2020–23 | 81% | 67% |

An open-ended test set ("2016 onwards") would be dominated by this artefact: train 45% vs test 29% investor share at a 2016 cutoff, 23% at 2017. A model would look badly calibrated for reasons that have nothing to do with prediction.

| Split | Train | Test A | Test pos | Test B |
|---|---|---|---|---|
| < 2012 / ≥ 2012 | 306 | 347 | 37.2% | 256 |
| < 2014 / ≥ 2014 | 395 | 258 | 37.2% | 188 |
| **< 2014 / 2014–2018** | **395** | **225** | **40.9%** | **169** |
| < 2015 / 2015–2019 | 434 | 204 | 37.3% | 151 |
| < 2016 / ≥ 2016 | 491 | 162 | 29.0% | 109 |

**Provisional split: train = initiated before 2014 (395); test = initiated 2014–2018 (225); award cases initiated 2019–2023 (33) excluded as too truncated.** Train investor share 43.5%, test 40.9%.

## Manual check

- Investor wins: script **268** = outcome count 268 ✔ (the "Neither investor…" matching bug found on the 2019 pilot is fixed)
- To do: confirm 268 with an Excel filter on the original file.

## Decisions (recorded in DECISIONS.md)

- Source: **31/12/2023 release** (D-01)
- Primary label: **A**; B as robustness check (D-02)
- Provisional split: **train < 2014, test 2014–2018** (D-03)
- Arbitrator features: **keep (optional)** (D-04)

## Surprises / open questions

- Right truncation is strong enough to change the design (above). Worth one sentence in the paper's limitations.
- "Neither" cases (24): breach found but nothing awarded → 0 in label_a. Judgement call.
- Ask in Phase 1: should the test window end at 2017 instead (pending share 2017–19 is 38%)? Check test size if so.
