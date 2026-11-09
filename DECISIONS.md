# Decisions

Every modelling choice is recorded here when it is made: date, choice, reason, alternatives considered, and any manual check performed. Entries are never deleted; a reversed decision gets a new entry that refers back to the old one.

Fields marked `[ ]` are to be filled in from `results/explore_report.txt`.

---

## D-00 · 2026-10 · Scope fixed before data work

**Choice**
- Investment (treaty-based) arbitration only.
- Primary task: binary outcome prediction for cases ending in an award.
- Settlement prediction is secondary and only if time allows.
- Time-based train/test split, not random.
- Majority-class baseline computed before any model.
- LLMs must state a confidence (0–100) with each prediction.

**Reasons**
- Commercial arbitration is confidential; investment arbitration has public records because a State is a party.
- A random split would place the same arbitrators and treaties in both train and test sets (leakage) and would not mimic real use, where only past cases are available.
- Without stated confidence, calibration cannot be measured.

**Alternatives considered**
- Five-category outcome prediction: rejected, categories too imbalanced.
- PITAD dataset: rejected, access terms unclear and rights reserved against AI training.
- ICSID panel database: rejected, lists designated candidates, not appointed arbitrators.

---

## D-01 · 2026-10-25 · Data source

**Choice** UNCTAD ISDS Navigator, **full data release as of 31/12/2023** (1,332 cases).

- File as downloaded: `UNCTAD-ISDS-Navigator-data-set-31December2023.xlsx`
- Download date: 2026-10-25, from UNCTAD's publication page (free, no registration)
- Saved as: `data/raw/isds_navigator.xlsx`
- Layout: data on sheet 1 with 11 note lines above the header (`HEADER_ROW = 11`); terms on sheet 2
- Terms of use: file links to UNCTAD's general terms; redistribution not stated → raw file **not tracked** in git
- Citation: *UNCTAD, Investment Dispute Settlement Navigator: full data release as of 31/12/2023 (excel format)*

**Reason** Latest free, complete public release; includes respondent, home State, sector, rules, institution, year, alleged and found breaches, amounts, outcome and arbitrators with roles.

**Alternatives considered** 31/07/2019 release (983 cases), used for a pilot run on 2026-10-25. Same layout; one column renamed (`BREACHES FOUND` → `IIA BREACHES FOUND`). Rejected: fewer cases, older test period.

---

## D-02 · 2026-10-25 · Outcome label

**Observed outcome values (n = 1,332)**

| Value | Count |
|---|---|
| Decided in favour of State | 361 |
| Pending | 354 |
| Decided in favour of investor | 268 |
| Settled | 177 |
| Discontinued for unknown reasons | 128 |
| Neither investor nor the State (liability found but no damages awarded) | 24 |
| Data not available | 20 |

State wins split by `IIA BREACHES FOUND`: jurisdiction declined 164 · all claims dismissed on the merits 188 · not available 9.

**Choice**

| Label | Definition | n | Investor share | Role |
|---|---|---|---|---|
| `label_a` | Award cases: 1 = decided in favour of investor; 0 = decided in favour of State (incl. jurisdiction declined) or neither | 653 | 41.0% | **primary** |
| `label_b` | As above, excluding `IIA BREACHES FOUND` = "None - jurisdiction declined" | 489 | 54.8% | robustness |

Settled, discontinued, pending and "data not available" are excluded from both; settled/discontinued kept separately.

**Reasons**
- A party weighing settlement cares whether the award will give it anything, at whatever stage it loses. `label_a` matches that question.
- "Neither" (liability found, no damages) gives the investor nothing → 0. Judgement call, noted in LIMITATIONS.
- `label_a` is larger.

**Alternatives considered** Merits-only as primary (`label_b`): smaller and less aligned with the settlement decision.

**Manual check** Investor wins: script 268 = outcome count 268. On the 2019 pilot the first run gave 205 instead of 191 because matching the word "investor" also caught "Neither investor nor the State"; fixed by matching "favour of investor". Excel filter check on the original file: `268`.

---

## D-03 · 2026-10-25 · Time split (provisional): train < 2014, test 2014–2018

Split on **year of initiation** (no year of conclusion in the data).

**Finding: strong right truncation.** Among award cases, investor share falls from 41.5% (initiated 2010–14) to 37.3% (2015–19) and 13.3% (2020–23). Pending share by cohort: 4% (2010–13), 13% (2014–16), 38% (2017–19), 81% (2020–23). Recent decided cases are the fast ones, and jurisdiction-declined awards rise to 34% (2017–19) and 67% (2020–23) of awards.

| Split | Train | Test A | Train pos | Test pos | Test B |
|---|---|---|---|---|---|
| < 2012 / ≥ 2012 | 306 | 347 | 45.4% | 37.2% | 256 |
| < 2014 / ≥ 2014 | 395 | 258 | 43.5% | 37.2% | 188 |
| **< 2014 / 2014–2018** | **395** | **225** | **43.5%** | **40.9%** | **169** |
| < 2015 / 2015–2019 | 434 | 204 | 43.8% | 37.3% | 151 |
| < 2016 / ≥ 2016 | 491 | 162 | 45.0% | 29.0% | 109 |

**Choice (provisional)** Train = initiated before 2014; test = initiated 2014–2018; award cases initiated 2019–2023 (33) excluded.

**Reasons**
- Meets train ≥ 200, test ≥ 80 for both labels with room for calibration bins.
- An open-ended recent test window would mostly measure truncation (test investor share 23–29%), not predictive reliability.
- Smallest train/test gap in base rate among candidates with a test set above 200.

**Alternatives considered** Test window ending 2017 (pending share 2017–19 is 38%); to check in Phase 1. Open-ended test windows: rejected for the reason above.

---

## D-04 · 2026-10-25 · Amount, claims and arbitrator fields

- **Amount claimed**: text (`3000.00 USD`, `11.00 EUR (12.50 USD)`); parse the USD figure. Missing 11.8% in award cases. Feature: log amount + missing flag.
- **Amount awarded**: **not used** — outcome information (leakage).
- **IIA breaches alleged**: `;`-separated; missing 11.5% in award cases. Features: count + flags for the most frequent types (chosen on the training set).
- **IIA breaches found**: outcome information — used only to define `label_b`, **never as a feature**.
- **Arbitrators**: one cell, `;`-separated, with roles. Missing 0.9% in award cases. Repeat-appointment feature: **keep (optional)**, counting only appointments in earlier-initiated cases.
- **Forum**: over a third of cases are not ICSID (UNCITRAL 411, SCC 56, ICC 26 …) → LLM prompts use the actual rules, not "an ICSID claim".

---

<!-- Template for new entries

## D-XX · YYYY-MM-DD · Title

**Choice**
**Reason**
**Alternatives considered**
**Manual check**

-->
