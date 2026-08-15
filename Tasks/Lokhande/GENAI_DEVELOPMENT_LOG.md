# GenAI Development Log — Phase 6/7

Persistent engineering and research log for the assigned work on:

- **Phase 6 — GenAI Personalization** (how to communicate an already-approved product)
- **Phase 7 — Marketing Campaign Engine**

Maintained for every major Codex/DeepSeek task. **Append new entries; never rewrite
history.** This log is documentation only — it must never drive production code changes.

---

## Task Log

### Entry template (copy for every new task)

- **Task ID and title:** `DS-0X — <title>`
- **Date:** YYYY-MM-DD
- **Objective:** <what this task was meant to establish>
- **Model used:** <e.g. DeepSeek, Codex>
- **Why that model was used:** <selection rationale>
- **Architecture/review model, if different:** <reviewing/auditing model, if any>
- **Research papers/resources consulted:** <titles + links>
- **Why each source was relevant:** <link each source to the task>
- **Important findings adopted from each source:** <what we actually used>
- **Files changed:** <paths, created vs modified>
- **Problems encountered:** <short list; IDs into the Problems & Decisions Register>
- **Root cause:** <of each problem>
- **Fix/decision:** <what was done>
- **Tests run:** <exact commands>
- **Test results:** <counts + evidence>
- **Known limitations:** <what remains deferred/unsupported>
- **Dependencies/blockers:** <env, upstream systems, external constraints>
- **Lessons learned:** <takeaways for later tasks>
- **Branch:** <feature branch>
- **Commit:** <full hash>
- **PR status:** <opened/merged/none + reason>
- **Next task:** <planned follow-up>

### DS-01 Initial Entry

- **Task ID and title:** DS-01 — FastAPI Scaffold and Strict Phase 6 Contracts
- **Date:** 2026-08-15
- **Objective:** Establish the FastAPI application skeleton and the strict Phase 6
  request/response contracts (input + output models, enums, validation rules) so
  later tasks (DS-02+) can build generation on top. Architecture only — no LLM,
  no grounding, no campaigns, no persistence.
- **Model used:** DeepSeek (deepseek-v4-flash) — primary implementation model.
- **Why that model was used:** Assigned coding model for the session; adequate for
  FastAPI scaffolding and strict Pydantic contract work, which requires no
  LLM-specific reasoning. FastAPI did not exist in the repo before DS-01.
- **Architecture/review model, if different:** Codex — repository architecture
  audit and contract design. Independent check of git state, team boundaries,
  forbidden paths, and the shape of the Phase 6 input/output contracts.
- **Research papers/resources consulted:** None required — no research paper was
  specifically needed for DS-01. Pydantic v2 strict-mode behavior (datetime and
  enum string handling) was verified empirically with small in-venv scripts
  rather than external literature.
- **Why each source was relevant:** N/A for DS-01 (see Research Library below).
- **Important findings adopted from each source:** N/A for papers. Empirical
  pydantic v2 findings are captured in the Problems & Decisions Register
  (P-001…P-005).
- **Files changed:**
  - Created: `Python/app/__init__.py`, `Python/app/core/__init__.py`,
    `Python/app/core/config.py`, `Python/app/main.py`, `Python/app/models/__init__.py`,
    `Python/app/models/personalization.py`, `Python/tests/__init__.py`,
    `Python/tests/unit/__init__.py`, `Python/tests/unit/test_personalization_contracts.py`
  - Modified: `Python/main.py` (entry point re-exporting the canonical app),
    `Python/requirements.txt` (minimal deps: fastapi, uvicorn, pydantic, pytest, httpx)
  - Untouched: `Python/Database_csvs/**`, `Python/database_generation_scripts/**`,
    `Backend/**`, `Frontend/**`, `Tasks/**` (at the time), `GenAI_Banking_Marketing_README.md`
- **Problems encountered:** P-001 strict-mode datetime rejected RFC 3339 strings;
  P-002 strict-mode enums rejected wire strings; P-003 `Field(strict=False)` on a
  list container did not relax list items; P-004 no Python deps pre-installed;
  P-005 bytecode/cache artifacts left by test runs.
- **Root cause:** Pydantic v2 strict mode semantics + fresh environment (see Register).
- **Fix/decision:** Per-field `Field(strict=False)` for datetime/enum fields
  (exact-value matching preserved), per-item `Annotated` for the channel list,
  isolated venv outside the repo for verification, caches removed before commit.
- **Tests run:**
  - `cd Python && /tmp/ds01-venv/bin/python -m pytest tests/ -v`
  - Boot check: `uvicorn main:app --port 8765` + `curl http://127.0.0.1:8765/health`
- **Test results:** **24 passed** (0 failures; 1 library-internal starlette
  deprecation warning). `/health` returned **HTTP 200**
  `{"status":"ok","service":"genai-personalization"}`; OpenAPI exposes only `/health`.
- **Known limitations:**
  - First-slice enums only: `ProductFamily.CREDIT_CARD`, five `Channel` values,
    `EligibilityStatus.ELIGIBLE`, `OwnershipStatus.NO_CONFLICT`.
  - No generation endpoint yet — contracts are validated by unit tests only.
  - Strict float `propensity_score` accepts only JSON numbers `0.0`/`1.0` form,
    not the integer `1` (must be sent as `1.0`).
  - No catalogue grounding, no provider call, no persistence, no Spring/Frontend
    integration (deliberate — DS-01 scope).
  - No upstream NBO implementation currently exists, so the project uses
    **fixture-driven contracts** for the first Phase 6 vertical slice.
- **Dependencies/blockers:**
  - Python 3.9+ (tested on 3.14.6); pydantic ≥ 2.8 (uses `AwareDatetime`).
  - Verification deps installed in an isolated venv at `/tmp/ds01-venv`
    (outside the repo); `requirements.txt` declares the runtime/test deps.
  - Blocker: no upstream Next-Best-Offer engine exists yet → fixture-based testing.
- **Lessons learned:**
  - Pydantic v2 strict mode disables string parsing for `datetime` and requires
    enum *instances*; relax per-field with `Field(strict=False)`, which still
    rejects unknown enum values and malformed timestamps.
  - `Field(strict=False)` on a list container does **not** propagate to list
    items — annotate each item type instead.
  - Strict-by-default plus explicit wire-format exceptions yields the strongest
    contract without breaking JSON interop.
- **Branch:** `feature/genai-ds01-fastapi-contracts`
- **Commit:** `6642470f56edf637a36864e4e7a616a356400341`
- **PR status:** Not opened (no PR requested). Branch pushed to `origin` for
  team-leader review.
- **Next task:** DS-02 — Catalogue repository and product grounding

---

## Research Library

| Title | Authors/Org | Year | URL / DOI / arXiv | Topic | Why consulted | Used by task | Ideas adopted | Ideas rejected / not used |
|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | No external research was required for DS-01. Populate from DS-02 onwards (product grounding, RAG / hallucination control papers). | — | — | — | — |

---

## Development Model Usage

DeepSeek and Codex are **third-party AI coding models/services used as engineering
tools**. The team did **not** train, fine-tune, or host them — this section records
only how they were used.

| Model | Role | Task | Reason selected | Outcome | Reviewed / fixed by another model? |
|---|---|---|---|---|---|
| DeepSeek (deepseek-v4-flash) | Primary implementation model | DS-01 — FastAPI scaffold, strict Phase 6 contracts, unit tests | Assigned coding model for the session; adequate for scaffold + contract work | 24/24 tests passed; `/health` HTTP 200; commit `6642470` | No — Codex performed an architecture audit / contract design review in parallel |
| Codex | Repository architecture audit and contract design | DS-01 — verify repo state, team boundaries, forbidden paths, contract shape | Independent second set of eyes on scope and git safety | Confirmed scope boundaries and contract structure before implementation | N/A (review role) |

---

## Trained / Evaluated Models

Reserved for any actual ML models the project later trains or evaluates (e.g.,
propensity/segmentation models by other team members, or future fine-tunes).

Fields recorded per model: model/algorithm · purpose · dataset · dataset version ·
features · train/validation/test split · hyperparameters · metrics · random seed ·
training date · artifact location · issues · final result.

> **Status (DS-01):** No Phase 6 LLM has been trained or fine-tuned. The first LLM
> work (DS-02+) is expected to use a third-party provider API with prompt
> engineering and product grounding — not custom training. This section stays empty
> until an actual model is trained.

---

## Problems & Decisions Register

Chronological, append-only.

| ID | Task | Problem | Root Cause | Decision / Fix | Status |
|---|---|---|---|---|---|
| P-001 | DS-01 | Strict-mode `datetime` rejected RFC 3339 ISO strings (`2026-08-12T06:34:14+05:30`) | Pydantic v2 strict mode disables string parsing for datetime fields | Use `AwareDatetime = Field(strict=False)` — accepts RFC 3339 strings, still rejects naive timestamps | Resolved |
| P-002 | DS-01 | Strict-mode `str` enums rejected wire strings (`"PUSH"`, `"ELIGIBLE"`) | Pydantic v2 strict mode requires enum *instances*, not values | `Field(strict=False)` on enum fields — exact value match preserved, unknown values still rejected | Resolved |
| P-003 | DS-01 | `Field(strict=False)` on a `list[Channel]` container did not relax the items | The strict flag is not propagated from a container field to its items | Per-item annotation: `list[Annotated[Channel, Field(strict=False)]]` | Resolved |
| P-004 | DS-01 | No Python dependencies pre-installed (fresh env, Python 3.14) | Empty `requirements.txt`, no venv | Isolated venv at `/tmp/ds01-venv` for verification; deps declared (unpinned) in `requirements.txt` | Resolved |
| P-005 | DS-01 | `__pycache__` / `.pytest_cache` artifacts left in the tree by test runs | Python bytecode + pytest cache generation | Removed before commit; never staged | Resolved |
