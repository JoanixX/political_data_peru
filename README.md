# Political Data Peru — Entity-resolution pipeline linking candidates to public records

An open-source data platform that consolidates Peruvian senators and presidential
candidates from the JNE, the Congress of the Republic, and government transparency
portals into a single curated layer, then links each candidate to companies sanctioned by
OSCE and scores them on a transparent, reproducible risk index. The pipeline is a
medallion layout (raw → staging → normalized → matched → curated) in Polars, served by a
FastAPI read layer over Parquet.

**Layer docs:** [src](src/README.md) · [data](data/README.md) · [backend](backend/README.md) · [tests](tests/README.md) · **License:** MIT

## Results

The entity matcher and the risk index have **no labelled evaluation**. There is no
annotated set of true candidate↔company links, so precision and recall are unmeasured,
and no accuracy table can honestly be published. What is fixed and auditable is the
decision rule: every parameter below is a constant in the source, and every score is
recomputable from the curated layer.

| Parameter | Value | Defined in |
|---|---|---|
| Fuzzy company-name match threshold | 0.92 | `src/entity_resolution/matching.py` |
| Deterministic match score (DNI→RUC→sanction) | 1.0 | `src/entity_resolution/matching.py` |
| Risk index weights (financial / legal / stability) | 40% / 40% / 20% | `synthesize_itr`, `src/analytics/risk_engine.py` |
| Financial score method | robust z-score on median + MAD × 1.4826, clamped at 3 MADs | `evaluate_financial_risk` |
| Score for candidates with no financial signal | 50.0 (neutral), flagged separately | `evaluate_financial_risk` |
| Legal score scale (0 / 1 / >1 sentences) | 100 / 50 / 0 | `evaluate_legal_integrity` |
| Semantic search model | `paraphrase-multilingual-MiniLM-L12-v2` over FAISS inner product | `src/entity_resolution/vector_store.py` |

Reproduce: `docker-compose up --build`, then `pytest tests/` for the scraper and
data-integrity suites.

The number worth trusting least is the fuzzy one. Deterministic matches are traceable
(national ID → tax ID → sanction record) and carry `osce_match_method=DETERMINISTIC`;
fuzzy name matches above 0.92 are an unvalidated guess and are labelled as such in the
output so a consumer can filter them out.

## How it works

- **Matching runs deterministic-first, fuzzy-second, and records which method fired.**
  A DNI→RUC bridge join is exact and defensible; string similarity on company names is
  not. Collapsing both into one score would make an unverifiable match indistinguishable
  from a documented one, so `osce_match_method` travels with every row.
- **Financial risk uses median and MAD, not mean and standard deviation.** Declared assets
  in Peruvian filings are heavily skewed and contain extreme outliers — the very cases the
  index is meant to surface. A mean-based z-score would be dragged by those outliers and
  would compress exactly the signal of interest; MAD × 1.4826 is the consistent estimator
  for the normal case while staying robust.
- **Missing financial data scores 50, not 0.** A candidate with no declared income and no
  public experience is unmeasured, not clean and not guilty; scoring them neutral and
  raising an explicit `Información Financiera Insuficiente` flag keeps absence of evidence
  from reading as evidence.
- **The index is a fixed linear combination with published weights** rather than a fitted
  model. Nothing in this domain provides a ground-truth label for "risk", so a learned
  score would be unfalsifiable; a stated 40/40/20 weighting can be argued with, audited,
  and recomputed.
- **Risk flags are emitted as a list alongside the score**, so a consumer sees the
  specific reasons (multiple sentences, party volatility, sanctioned-company link with its
  RUC) rather than a single opaque number.
- **Field-level change auditing** (`src/utils/audit.py`) records what each pipeline stage
  altered, so a value in the curated layer can be traced back to the source that produced
  it.
- **Semantic search over government plans is built offline into a FAISS index** with
  normalized embeddings, so inner product equals cosine similarity and query time stays
  independent of the model.

## Quick start

```bash
cp .env.example .env      # fill in credentials
docker-compose up --build
```

The API serves the curated layer with offset/limit pagination and ETag support:

| Method | Route | Description |
|---|---|---|
| GET | `/health` | Service and data-layer status |
| GET | `/candidatos` | Paginated candidate list from the curated layer |
| GET | `/candidato/{global_id}` | Single candidate record |
| GET | `/osce/{ruc}` | OSCE audit record for a company: sanctions, fines, disqualifications, contractual penalties, consortium participation, and the direct link to its Ficha Única de Proveedor |

Per-directory setup and development instructions live in each subdirectory's README.

## Data & provenance

Sources are official and public: the Jurado Nacional de Elecciones (candidate filings and
sworn declarations), the Congress of the Republic, OSCE's sanctioned-supplier registry,
and government transparency portals. Observed values are scraped unmodified into the raw
layer and never overwritten; everything downstream — normalized names, resolved
identities, all four scores, and the risk flags — is derived and marked as such, with
field-level lineage in the audit log. `data/` ships empty (`.gitkeep`): no scraped
personal data is committed to this repository, and running the pipeline reproduces it
from source.

## Limitations

- **A false positive here is an accusation about a named real person.** The fuzzy branch
  links a candidate to a sanctioned company on a 0.92 name-similarity score, and common
  Peruvian company naming (shared surnames, generic "S.A.C." forms, regional duplicates)
  produces genuine collisions. Precision at that threshold has never been measured, and
  the 0.92 cutoff was chosen by judgement, not tuned against labelled data.
- **The risk index is an opinion expressed in arithmetic.** The 40/40/20 weighting, the
  100/50/0 legal ladder, and the 3-MAD clamp are defensible defaults with no empirical
  basis. A different analyst would pick different constants and rank candidates
  differently; the index should be read as one transparent scoring scheme, not a
  measurement.
- **Legal scoring counts sentences without weighting them.** One conviction for a traffic
  offence and one for embezzlement both score 50, because the source data as scraped does
  not reliably distinguish severity or matter.
- **Scraper fragility is the main operational risk.** Every source is an HTML portal that
  can change layout, rate-limit, or block; the pipeline's coverage on any given day
  depends on scrapes that are not guaranteed to have succeeded, and partial ingestion
  silently shrinks the population a percentile-based score is computed over.
- **Scores are relative to whoever was ingested.** The financial score is computed against
  the median of the current cohort, so a candidate's number moves when the cohort changes
  — figures are not comparable across pipeline runs.
- **No documented `docs/` directory exists** despite earlier references to one;
  architecture notes currently live in the per-directory READMEs listed above.
- **The semantic-search layer indexes government-plan text only** and is unevaluated: no
  retrieval metrics, no query set, no relevance judgements.

## License

MIT
