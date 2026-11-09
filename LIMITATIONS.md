# Limitations

Known limits of the data and design. Updated as the analysis proceeds.

## Data coverage

1. **Publicly known cases only.** The ISDS Navigator covers treaty-based disputes that have become public. Confidential proceedings, and contract-based disputes, are absent. The sample is not the full population of investor–state disputes.
2. **Concluded cases only.** Pending cases have no outcome and are excluded, which shrinks the sample and may introduce selection effects.
3. **Right truncation.** Among recently initiated cases, only those that ended quickly are concluded, and quick cases are disproportionately jurisdictional dismissals. Investor share among award cases falls from 41.5% (initiated 2010–14) to 13.3% (2020–23). The test window is therefore bounded at 2018 and cases initiated 2019–2023 are excluded (`DECISIONS.md` D-03); some truncation remains in the 2017–18 cohorts.
4. **Data as of 31 December 2023.** Later developments in individual cases (annulment, set-aside, settlement after award) are not reflected.

## Outcome definition

5. **Settled and discontinued cases are treated separately**, not merged with decided cases. They differ in kind from merits outcomes.
6. **Outcome categories are UNCTAD's.** Mapping them to a binary label requires judgement, especially for jurisdictional dismissals and "neither party" decisions (see `DECISIONS.md` D-02).

## Design

7. **Descriptive study.** The analysis measures how well outcomes can be predicted and whether stated confidence is reliable. It makes no causal claim about why tribunals decide as they do.
8. **Structural features only.** Models see case characteristics available at initiation, not pleadings, evidence or tribunal reasoning.
9. **Investment arbitration only.** Results are not extended to commercial arbitration.

## LLM-specific (to be completed in Phase 3)

10. **Possible training-data contamination.** Most cases predate the LLMs' training cutoffs, so models may have seen outcomes. Case names and party names are removed from prompts to reduce this, but it cannot be eliminated. If models remain poorly calibrated despite possible exposure, that strengthens rather than weakens the conclusion.
