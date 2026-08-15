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

### DS-02 Entry — Credit Card Catalogue Repository + Product Grounding

- **Task ID and title:** DS-02 — Credit Card Catalogue Repository + Product Grounding
- **Date:** 2026-08-15
- **Objective:** Let Phase 6 safely retrieve an already-selected product
  (`CREDIT_CARD` / `CC014`) from the prototype CSV catalogue and expose only
  allowlisted, unambiguous facts suitable for future GenAI grounding.
  Service/repository layer only — no API route, no LLM, no prompts, no
  campaigns, no persistence.
- **Model used:** DeepSeek (deepseek-v4-flash) — primary implementation model.
- **Why that model was used:** Assigned coding model for the session; the work is
  deterministic service/repository code with strict data validation — no
  LLM-specific reasoning required.
- **Architecture/review model, if different:** Codex — none for implementation.
  No architecture problem forced escalation; the DS-01 scope audit carried
  forward unchanged.
- **Research papers/resources consulted:** None. **No external research paper
  required for DS-02.** CSV/pydantic stdlib behaviour was verified empirically
  where needed (see Problems & Decisions Register).
- **Why each source was relevant:** N/A (see Research Library).
- **Important findings adopted from each source:** N/A for papers. Catalogue
  findings adopted from inspecting the real CSV and its generation script:
  - 101-column schema, 32 products, no duplicate IDs, no blank cells; all rows
    `Active` with `end_date=2099-12-31` (no real inactive/expired rows).
  - Generation script documents sentinels: `TEXT_DEFAULT="Not Applicable"`,
    `NUM_DEFAULT=0`, `BOOL_DEFAULT="No"`.
  - `999` appears in lounge-visit counts (`priority_pass_visits`,
    `domestic_lounge_visits`) with **no documented "unlimited" semantic** →
    treated as an ambiguous sentinel and omitted from grounded facts.
  - `renewal_fee_waiver` values (300000–1000000) are spend thresholds for fee
    waiver, not fees → parsed but never grounded.
  - `product_description` is the generic "HDFC Bank credit card product." for
    31/32 products → not product-specific → omitted (`approved_description` is
    `None` for CC014).
  - CC014 international-lounge data is contradictory (`access=Yes`,
    `visits=0`, `priority_pass=No`) → international lounge facts omitted.
- **Files changed:**
  - Created: `Python/app/models/product.py`, `Python/app/repositories/__init__.py`,
    `Python/app/repositories/product_catalogue.py`, `Python/app/services/__init__.py`,
    `Python/app/services/product_grounding.py`, `Python/tests/unit/test_product_catalogue.py`,
    `Python/tests/unit/test_product_grounding.py`
  - Modified: `Python/app/models/__init__.py` (exports only),
    `Tasks/Lokhande/GENAI_DEVELOPMENT_LOG.md` (this entry)
  - Untouched: `Python/Database_csvs/**`, `Python/database_generation_scripts/**`,
    `Backend/**`, `Frontend/**`, `Python/main.py`, `Python/app/main.py`,
    `Python/requirements.txt` (no new dependencies)
- **Problems encountered:** P-006, P-007, P-008, P-009 (see Register).
- **Root cause:** see Register.
- **Fix/decision:** see Register; allowlist design decisions above (999, waiver
  threshold, generic description, contradictory international lounge data).
- **Tests run:** `cd Python && /tmp/ds01-venv/bin/python -m pytest tests/ -q`
  (full suite incl. DS-01 regression); plus a sanity print of grounded real
  `CC014` output.
- **Test results:** **49 passed** (24 DS-01 regression + 25 new DS-02), 0 failures.
- **Known limitations:**
  - `CREDIT_CARD` only; other families are rejected
    (`UnsupportedProductFamilyError`), unreachable until `ProductFamily` grows.
  - Fee facts expose raw amounts (`"2500"`) without currency formatting —
    formatting is the future generator's job.
  - No `forex_markup`, eligibility, or credit-limit facts (ambiguous / out of
    allowlist).
  - Only `status` + `end_date` are enforced; `launch_date` is not parsed.
  - Catalogue is loaded fully into memory per repository instance (32 rows —
    fine for the prototype).
- **Dependencies/blockers:** none new (`csv`, `hashlib`, `json` stdlib). No
  upstream NBO engine still (fixture-driven).
- **Lessons learned:**
  - Sentinel semantics must come from the data producer's documentation; an
    undocumented `999` must never be read as "unlimited".
  - Parse a curated typed subset at the repository, project an explicit
    allowlist at the service — raw rows never leave.
  - Hash only the grounded projection so the catalogue version changes iff a
    citable fact changes.
- **Branch:** `feature/genai-ds01-fastapi-contracts`
- **Commit:** `2dd750447cef6136f30036a1ee55c70aa7d63c8f`
- **PR status:** Not opened (no PR requested). Branch pushed to `origin` for
  team-leader review.
- **Next task:** DS-03 — Versioned prompt templates and safe prompt builder

### DS-03 Entry — Versioned Prompt Templates + Safe Prompt Builder

- **Task ID and title:** DS-03 — Versioned Prompt Templates + Safe Prompt Builder
- **Date:** 2026-08-15
- **Objective:** Prepare the LLM input for Phase 6: project a safe, explicit
  context from the request + grounded product, render it through versioned
  Jinja2 templates, and return a typed `PromptPackage`. Prepares input only —
  no LLM call, no network, no provider, no API route.
- **Model used:** DeepSeek (deepseek-v4-flash) — primary implementation model.
- **Why that model was used:** Assigned coding model for the session; the work
  is deterministic template/builder code with strict validation — no
  LLM-specific reasoning required.
- **Architecture/review model, if different:** Codex — none for implementation.
  No architecture problem forced escalation.
- **Research papers/resources consulted:** None. **No external research paper
  required for DS-03.** Jinja2 include/newline behaviour was verified
  empirically in the venv.
- **Why each source was relevant:** N/A (see Research Library).
- **Important findings adopted from each source:** N/A for papers. Empirical
  Jinja2 findings: dynamic `{% include %}` resolves against the loader root
  (not relative to the including template), and Jinja2 strips trailing
  newlines unless `keep_trailing_newline=True`.
- **Files changed:**
  - Created: `Python/app/prompts/__init__.py`, `Python/app/prompts/v1/system.jinja2`,
    `Python/app/prompts/v1/personalization.jinja2`,
    `Python/app/prompts/v1/channels/{push,sms,email,in_app,relationship_manager}.jinja2`,
    `Python/app/models/prompt.py`, `Python/app/services/prompt_builder.py`,
    `Python/tests/unit/test_prompt_builder.py`
  - Modified: `Python/app/models/__init__.py` (exports),
    `Python/requirements.txt` (added `jinja2`),
    `Tasks/Lokhande/GENAI_DEVELOPMENT_LOG.md` (this entry)
- **Prompt privacy design:** The builder never serializes `PersonalizationRequest`
  (no `request.model_dump()`). Rendered prompts contain only: mapped segment
  label, mapped generic event labels, persuasion reason labels, generation
  language, requested channels, and approved grounded facts + tags. Excluded:
  `customer_id`, `recommendation_id`, `source_event_id`, account/card/
  transaction IDs, contact/address/KYC/income/credit-score data, employer,
  transaction amounts, RM ID, propensity, and detailed eligibility/ownership
  data. System prompt states the product was selected and approved upstream
  and forbids re-evaluating eligibility/propensity/ownership.
- **Controlled mappings:** `FREQUENT_TRAVELLER → frequent traveller`;
  `FLIGHT_PURCHASE → recent flight purchase`; reason codes
  `HIGH_TRAVEL_SPEND/RECENT_FLIGHT_PURCHASE → high travel spending / recent
  flight purchase` (persuasion subset only — the safety codes
  `NO_CONFLICTING_TRAVEL_CARD`/`PRODUCT_ELIGIBLE` are validated but excluded).
  Unknown values fail at the boundary (`PromptContextError`,
  `PROMPT_CONTEXT_INVALID`). v1 supports language `en` only.
- **Problems encountered:** P-010, P-011, P-012, P-013 (see Register).
- **Root cause:** see Register.
- **Fix/decision:** see Register.
- **Tests run:** `cd Python && /tmp/ds01-venv/bin/python -m pytest tests/ -q`
  (full suite); manual render inspection of system + user prompts.
- **Test results:** **68 passed** (24 DS-01 + 25 DS-02 + 19 new DS-03), 0 failures.
- **Known limitations:**
  - v1 supports `en` only; other languages are rejected.
  - Only `FLIGHT_PURCHASE` / `FREQUENT_TRAVELLER` and the four fixture reason
    codes are mapped; anything else fails at the builder boundary (by design).
  - Length limits are prototype constants (`60`/`160` chars) injected into
    templates — tuning is expected later.
  - No output-schema enforcement yet (DS-04/DS-06 concern); the prompt only
    instructs the future LLM.
- **Dependencies/blockers:** added `jinja2` to `requirements.txt` (only new
  dependency). No provider, no network, no API route.
- **Lessons learned:**
  - Jinja2 dynamic includes resolve against the loader root — pass
    version-prefixed paths; and set `keep_trailing_newline=True` so included
    sections stay separated.
  - Concrete fact-id examples in prompts leak ids that may not be grounded —
    keep examples generic or dynamic.
  - Failing loudly on unknown mapping values is safer than silently leaking
    raw codes into prompts.
- **Branch:** `feature/genai-ds01-fastapi-contracts`
- **Commit:** `091be5cd1bb4860bb5470bd497542e02cbc7b75d`
- **PR status:** Not opened (no PR requested). Branch pushed to `origin` for
  team-leader review.
- **Next task:** DS-04 — LLM abstraction and deterministic fake provider

### DS-04 Entry — LLM Abstraction + Deterministic Fake Provider

- **Task ID and title:** DS-04 — LLM Abstraction + Deterministic Fake Provider
- **Date:** 2026-08-15
- **Objective:** Establish the provider boundary through which Phase 6 will
  eventually talk to a real LLM: a provider-neutral async contract plus a
  deterministic, offline, API-key-free fake provider for tests/CI/demos. No
  real LLM is called; no provider SDK, no network, no API route, no
  hallucination guard.
- **Model used:** DeepSeek (deepseek-v4-flash) — development coding agent only.
- **Why that model was used:** Assigned coding model for the session. Important
  distinction: DeepSeek writes this repository's code; the runtime provider
  abstraction is deliberately **provider-neutral** and is NOT coupled to
  DeepSeek merely because DeepSeek is the coding agent.
- **Architecture/review model, if different:** Codex — none for implementation.
  No escalation required.
- **Research papers/resources consulted:** None. **No external research paper
  required for DS-04.**
- **Why each source was relevant:** N/A (see Research Library).
- **Files changed:**
  - Created: `Python/app/llm/{__init__,base,fake,errors}.py`,
    `Python/app/models/generation.py`, `Python/tests/unit/test_llm_provider.py`,
    `Python/tests/unit/test_fake_llm_provider.py`, `Python/tests/integration/{__init__,test_phase6_composition}.py`
  - Modified: `Python/app/models/prompt.py` (added `fact_values` safe view),
    `Python/app/models/__init__.py` (exports), `Python/app/services/prompt_builder.py`
    (populates `fact_values`), `Tasks/Lokhande/GENAI_DEVELOPMENT_LOG.md` (this entry)
- **Provider architecture:** `LLMProvider` protocol (async `generate(prompt:
  PromptPackage) -> GeneratedContent`, plus `provider`/`model` attributes),
  `@runtime_checkable` for isinstance tests. Errors: `LLMProviderError` /
  `LLMProviderTimeoutError` / `LLMInvalidResponseError` (`LLM_PROVIDER_ERROR` /
  `LLM_PROVIDER_TIMEOUT` / `LLM_INVALID_RESPONSE`). Timeout/retry contract left
  for later DS work (no resilience framework built).
- **Fake provider design:** `DeterministicFakeProvider(provider="fake",
  model="deterministic-v1")` — no randomness, no network, no API key. Derives
  content from `PromptPackage.fact_values` (product facts only) so nothing is
  hardcoded (verified with a non-CC014 product name). Supports canned
  `response=` injection and `mode=` failure simulation
  (`SUCCESS`/`INVALID_RESPONSE`/`TIMEOUT`/`PROVIDER_ERROR`). Validates gross
  structural problems at the boundary: channels not requested →
  `LLM_INVALID_RESPONSE`; unknown fact refs → `LLM_INVALID_RESPONSE`; malformed
  canned content → `LLM_INVALID_RESPONSE`. No global mutable state.
- **Output model:** `GeneratedContent` reuses DS-01 channel models
  (`PushContent` etc.) with optional per-channel fields (only requested
  channels populated, at least one required) — smaller than DS-01's
  all-channels `ChannelContent`, with explicit `populated_channels()`.
- **Tests/results:** `cd Python && /tmp/ds01-venv/bin/python -m pytest tests/ -q`
  → **90 passed** (68 baseline + 22 new: 9 provider + 12 fake + 1
  integration-shaped composition). Composition test wires
  request → grounding → PromptBuilder → fake provider end to end.
- **Failures/problems:** P-014, P-015 (see Register).
- **Decisions:** see Register and above.
- **Limitations:** no real provider; no timeout/retry implementation; provider
  validates structure only — semantic claim validation is DS-05.
- **Dependency added:** none (zero new third-party dependencies).
- **Branch:** `feature/genai-ds01-fastapi-contracts`
- **Commit:** `a4b7a6dc9220affad55aadbe2d32feba870d9780`
- **PR status:** Not opened (no PR requested). Branch pushed to `origin` for
  team-leader review.
- **Next task:** DS-05 — Deterministic hallucination guard and generated-content
  safety validation

---

## Research Library

| Title | Authors/Org | Year | URL / DOI / arXiv | Topic | Why consulted | Used by task | Ideas adopted | Ideas rejected / not used |
|---|---|---|---|---|---|---|---|---|
| — | — | — | — | — | No external research was required for DS-01 through DS-04. Populate from DS-05 onwards (hallucination detection, claim extraction, evaluation). | — | — | — | — |

---

## Development Model Usage

DeepSeek and Codex are **third-party AI coding models/services used as engineering
tools**. The team did **not** train, fine-tune, or host them — this section records
only how they were used.

| Model | Role | Task | Reason selected | Outcome | Reviewed / fixed by another model? |
|---|---|---|---|---|---|
| DeepSeek (deepseek-v4-flash) | Primary implementation model | DS-01 — FastAPI scaffold, strict Phase 6 contracts, unit tests | Assigned coding model for the session; adequate for scaffold + contract work | 24/24 tests passed; `/health` HTTP 200; commit `6642470` | No — Codex performed an architecture audit / contract design review in parallel |
| Codex | Repository architecture audit and contract design | DS-01 — verify repo state, team boundaries, forbidden paths, contract shape | Independent second set of eyes on scope and git safety | Confirmed scope boundaries and contract structure before implementation | N/A (review role) |
| DeepSeek (deepseek-v4-flash) | Primary implementation model | DS-02 — catalogue repository, grounding service, tests | Assigned coding model for the session; deterministic service/data code, no LLM reasoning needed | 49/49 tests passed (incl. DS-01 regression); commit `2dd7504` | No — Codex not used for DS-02 implementation |
| DeepSeek (deepseek-v4-flash) | Primary implementation model | DS-03 — versioned prompt templates + safe prompt builder | Assigned coding model for the session; deterministic template/builder code with strict validation | 68/68 tests passed (incl. DS-01 + DS-02 regression); commit `091be5c` | No — Codex not used for DS-03 implementation |
| DeepSeek (deepseek-v4-flash) | Development coding agent | DS-04 — provider abstraction + deterministic fake provider | Assigned coding model; runtime provider abstraction kept provider-neutral (not coupled to DeepSeek) | 90/90 tests passed (incl. DS-01..DS-03 regression); commit `a4b7a6d` | No — Codex not used for DS-04 implementation |

---

## Trained / Evaluated Models

Reserved for any actual ML models the project later trains or evaluates (e.g.,
propensity/segmentation models by other team members, or future fine-tunes).

Fields recorded per model: model/algorithm · purpose · dataset · dataset version ·
features · train/validation/test split · hyperparameters · metrics · random seed ·
training date · artifact location · issues · final result.

> **Status (as of DS-02):** No Phase 6 LLM has been trained or fine-tuned. The LLM
> work (DS-03+) is expected to use a third-party provider API with prompt
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
| P-006 | DS-02 | Test fixture `cc_row()` called with `card_name=` kwarg, but signature is `(overrides, product_id)` | Fixture signature mismatch in test authoring | Call via `cc_row(product_id=..., overrides={"card_name": ...})` | Resolved |
| P-007 | DS-02 | `csv.DictWriter` ValueError: fixture row contained `cashback_available`, which is not in `REQUIRED_COLUMNS` | Fixture included a column the repository intentionally never parses | Removed the key — cashback is out of the parse allowlist by design | Resolved |
| P-008 | DS-02 | Test fixture `tag_golf=0` drifted from the real CC014 row (`tag_golf=1`) | Hand-authored fixture, not generated from data | Set `tag_golf=1` in fixtures and updated expected tags (GOLF) | Resolved |
| P-009 | DS-02 | `999` sentinel in lounge-visit counts (e.g. `priority_pass_visits=999`, `domestic_lounge_visits=999`) | Generation script documents `0`/`No`/`Not Applicable` defaults but not `999` | Treat as undocumented sentinel; omit from grounded facts; never interpret as unlimited | Resolved (decision) |
| P-010 | DS-03 | Jinja2 dynamic `{% include %}` did not resolve `channels/push.jinja2` relative to the including template | Dynamic includes resolve against the loader root, not the including template's directory | Pass version-prefixed paths (`v1/channels/<name>.jinja2`) from the builder | Resolved |
| P-011 | DS-03 | Rendered channel sections merged (`fact_refs.[EMAIL]`) | Jinja2 strips trailing template newlines unless `keep_trailing_newline=True` | Enable `keep_trailing_newline=True` in the builder Environment | Resolved |
| P-012 | DS-03 | Unknown reason codes / event types / segment codes reaching the prompt | No policy for unknown controlled values | Fail at the builder boundary with `PromptContextError` (`PROMPT_CONTEXT_INVALID`) rather than leaking raw codes | Resolved (decision) |
| P-013 | DS-03 | Hardcoded fact example `["product_name", "domestic_lounge_visits"]` in the template leaked a non-grounded id | Concrete example was not guaranteed to be grounded | Removed the concrete example; the `Allowed fact IDs` line provides the guidance | Resolved |
| P-014 | DS-04 | Fake provider needed approved fact *values*, but `PromptPackage` carried only rendered text + `allowed_fact_ids` | Parsing rendered prompt text would be fragile | Extended `PromptPackage` with a safe structured `fact_values` view (product facts only, populated by the builder) — no privacy impact | Resolved (decision) |
| P-015 | DS-04 | `inspect.signature` returned the annotation as the string `'PromptPackage'` | `from __future__ import annotations` defers annotation evaluation | Test accepts class-or-string form; also switched deprecated `asyncio.iscoroutinefunction` to `inspect.iscoroutinefunction` | Resolved |
