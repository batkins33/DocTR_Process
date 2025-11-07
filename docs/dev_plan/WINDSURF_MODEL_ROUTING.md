# WINDSURF_MODEL_ROUTING.md

> **Purpose:** Opinionated, price–performance–quality–speed routing guide for BA’s DocTR_Process / TruckTickets ecosystem inside Windsurf (and compatible IDEs). Use this to pick the right model for the task, create issues with correct labels, and keep handoffs clean.

_Last updated: Nov 5, 2025_

---

## 1) TL;DR
- **SWE‑1.5** = wiring/IO/tests/packaging/caching. Cheap, fast, deterministic. ~60–70% of commits.
- **GPT‑5 Codex** = mid‑complexity Python/SQL/file I/O implementations. Great library recall.
- **Claude 4.5 (Thinking)** = complex orchestration, rule‑heavy logic, exports, SQL design.
- **Claude 3.7 (Thinking)** = design/spec/acceptance criteria/architecture and review.
- **Claude Haiku 4.5** = micro‑patches/diffs/renames/config nits.

**Project Status: 97% Complete (30/31 issues)**

**Completed:** PDF processing, OCR integration, exports, database operations, testing framework
**Remaining:** Production monitoring dashboard (Issue #31)

---

## 2) Routing Principles
1. **Cheapest model that reliably succeeds** wins; upgrade only when blocked by context, reasoning, or refactoring breadth.
2. **Split by role:** Design (Claude 3.7) → Implement (SWE‑1.5 / Codex) → Orchestrate/Refactor (Claude 4.5) → Patch (Haiku).
3. **Handoffs are explicit:** Open an issue comment with: _"handoff → @model: X; acceptance criteria Y; known edge cases Z"_.
4. **Determinism first for IO:** hashing, caching, path rules, export schemas → SWE‑1.5.
5. **Schema or business rules?** Use Claude 4.5 to define them, Codex/SWE to implement.
6. **Favor small, test‑bounded PRs.** If a task straddles models, split into Design vs Impl subtasks.

---

## 3) Model Catalog (Value Map)

| Model | Best For | Avoid | Notes |
|---|---|---|---|
| **SWE‑1.5** | CLI wiring, logging, packaging, caching, adapters, unit/integration harness | Multi‑file policy design, heavy refactors | Ultra‑cheap/fast; great for deterministic code and tests |
| **GPT‑5 Codex** | Library integration (PyMuPDF, pandas, sqlite3), repo‑level edits, mid‑complexity Python/SQL | Open‑ended architecture | Excellent type inference; practical default implementer |
| **Claude 4.5 (Thinking)** | Business rules, export schemas, cross‑module orchestration, E2E test design | Small diffs | Use sparingly; highest reasoning with higher cost |
| **Claude 3.7 (Thinking)** | Spec writing, acceptance criteria, migration plans, review checklists | Production coding | Fast/cheap architect; sets the stage |
| **Claude Haiku 4.5** | Quick diffs, renames, config tweaks, comment/doc fixes | Context‑heavy tasks | Ideal pre‑commit polish |

---

## 4) Global Routing Rules

| Task Type | Default Model | Upgrade When | Downgrade When |
|---|---|---|---|
| Wiring/Boilerplate/Packaging | **SWE‑1.5** | Needs multi‑file awareness → **Codex** | Trivial one‑liners → **Haiku** |
| Library Integration (PDF/IMG/DB) | **GPT‑5 Codex** | Cross‑module policy/rollback → **Claude 4.5** | Becomes pure IO glue → **SWE‑1.5** |
| Business Rules / Normalization | **Claude 4.5** | Implementation is straightforward → **Codex** | Simple mapping tables → **SWE‑1.5** |
| SQL/ETL/Reporting Design | **Claude 4.5** | Pure DDL or query tuning → **Codex** | Simple indexes → **SWE‑1.5** |
| Test Plans & E2E Harness | **Claude 4.5** | Fixtures/basic harness → **SWE‑1.5** | N/A |
| Micro‑fix / Diff | **Haiku** | Needs tests/logic → **SWE‑1.5** | N/A |

---

## 5) TruckTickets: Issue‑Level Routing (Price–Performance Balanced)

**Completed Core Features** ✅
1. **PDF → Image conversion** - COMPLETE
   _Status:_ Implemented with DocTR integration, 29 tests passing
   _Features:_ DPI control, multi-page support, error handling

2. **Material / Source / Destination extraction** - COMPLETE
   _Status:_ Full precedence logic implemented with SynonymNormalizer
   _Features:_ Filename → folder → OCR → UI override precedence

3. **Export implementations** - COMPLETE
   _Status:_ All 4 export types implemented with comprehensive tests
   _Features:_ Excel (5 sheets), Invoice CSV, Manifest CSV, Review CSV

**Remaining Work**
4. **Production monitoring dashboard** — **Claude 4.5** (Issue #31, optional)
5. **Maintenance tasks** — **SWE‑1.5** (bug fixes, optimizations)
6. **Documentation updates** — **SWE‑1.5** (as needed)

**Completed Features** ✅
7. **End‑to‑End integration tests** — COMPLETE (comprehensive test framework)
8. **Vendor templates** — COMPLETE (multiple vendor templates implemented)
9. **SQL optimization & indexes** — COMPLETE (reference caching, optimized queries)
10. **OCR integration** — COMPLETE (DocTR, Tesseract, EasyOCR support)
11. **Batch processing** — COMPLETE (multi-threaded with error recovery)
12. **CLI interface** — COMPLETE (full command-line interface)
13. **Database operations** — COMPLETE (CRUD, duplicate detection, validation)

---

## 6) Model Routing Optimization Table (Operational)

| # | Task / Module | Primary Model | Secondary / Handoff | Reasoning Depth | Typical Latency (s) | Est. Cost ($/1K tok) | Promotion Triggers |
|---|---|---|---|---|---|---|---|
| 1 | PDF → Image | **GPT‑5 Codex** | SWE‑1.5 | ⚙️ Impl | 6–10 | 0.004 | Cross‑module debug → Claude 4.5 |
| 2 | Mat/Source/Dest | **Claude 4.5** | Codex | 🧠 High | 9–13 | 0.008–0.009 | Many edge cases or ambiguity |
| 3 | Exports | **Claude 4.5** | Codex | 🧩 Med‑High | 10–14 | 0.009 | Schema churn or fiscal logic |
| 4 | Confidence scoring | **SWE‑1.5** | – | 🧮 Low | 3–5 | 0.002 | Vector math needed → Codex |
| 5 | GUI log wiring | **SWE‑1.5** | Haiku | 🪶 Low | 2–4 | 0.002 | – |
| 6 | Export DB queries | **GPT‑5 Codex** | SWE‑1.5 | ⚙️ Med | 6–8 | 0.004 | ORM complexity ↑ |
| 7 | E2E tests | **Claude 4.5** | SWE‑1.5 | 🧭 High | 10–15 | 0.009 | – |
| 8 | Vendor templates | **Claude 3.7** | SWE‑1.5 | 🧩 Med | 5–9 | 0.005 | – |
| 9 | SQL optimization | **Claude 4.5** | Codex | 🧮 Med‑High | 9–12 | 0.008 | – |
| 10 | OCR caching | **SWE‑1.5** | – | 🧮 Low | 3–5 | 0.002 | – |
| 11 | GPU validation | **SWE‑1.5** | – | 🧮 Low | 2–4 | 0.002 | – |
| 12 | Review queue GUI | **Claude 4.5** | SWE‑1.5 | 🧠 High | 12–18 | 0.009 | Complex UX/flows |
| 13 | Console script | **SWE‑1.5** | Haiku | 🧮 Low | 2–4 | 0.002 | – |

> Costs are indicative; adjust to your provider’s current pricing.

---

## 7) Issue Labels & Windsurf Routing

Apply labels to auto‑route work to the correct model agents.

- **Priority:** `priority:critical` | `priority:medium` | `priority:low`
- **Model:** `model:swe-1.5` | `model:gpt5-codex` | `model:claude-4.5` | `model:claude-3.7` | `model:haiku`
- **Phase/Milestone:** `phase:P1-core` | `phase:P2-extraction` | `phase:P3-exports` | `phase:P4-tests`
- **Type:** `type:design` | `type:impl` | `type:refactor` | `type:test` | `type:ops`

**CLI snippets (adjust issue numbers):**
```bash
# Critical path
gh issue edit 1  --add-label "priority:critical,model:gpt5-codex,type:impl"
gh issue edit 2  --add-label "priority:critical,model:claude-4.5,type:design"
gh issue edit 3  --add-label "priority:critical,model:claude-4.5,type:design"

# Medium
gh issue edit 4  --add-label "priority:medium,model:swe-1.5,type:impl"
gh issue edit 5  --add-label "priority:medium,model:swe-1.5,type:impl"
gh issue edit 6  --add-label "priority:medium,model:gpt5-codex,type:impl"

# Low / deferred
gh issue edit 7  --add-label "priority:low,model:claude-4.5,type:test"
gh issue edit 8  --add-label "priority:low,model:claude-3.7,type:design"
gh issue edit 9  --add-label "priority:low,model:claude-4.5,type:design"
gh issue edit 10 --add-label "priority:low,model:swe-1.5,type:impl"
```

---

## 8) Mini‑Prompts (Copy/Paste into Agents)

**Claude 4.5 – PDF→Image (design)**
> Implement real PDF→image rendering for `pdf_utils.py` using PyMuPDF. Include DPI arg, per‑page image generation, and robust error handling (route failed pages to review queue). Add unit tests with small fixture PDFs. Target ≥4 pages/sec CPU.

**GPT‑5 Codex – PDF→Image (impl)**
> Wire PyMuPDF into `pdf_utils.py`. Functions: `render_pdf_to_images(path, dpi=200) -> List[PIL.Image]`. Map `page_num → image`. Handle encrypted/empty pages. Write tests with tmp files.

**Claude 4.5 – Extraction rules**
> Define precedence logic for material/source/destination: filename → folder → OCR tokens → UI override. Provide normalization tables and conflict resolution policy. Output acceptance criteria + test cases.

**SWE‑1.5 – Confidence scoring**
> Parse OCR engine confidences (word/line). Aggregate to field/page/doc. Thresholds route items to review queue. Add unit tests for low/high confidence.

**Claude 4.5 – Exports design**
> Specify Excel workbook schema (5 sheets), CSV schemas (Invoice/Manifest/Review). Define Job Week/Month rules. Provide golden snapshot examples.

**GPT‑5 Codex – Exports impl**
> Implement writers using `TicketRepository`. Filters: date/job/vendor. Create regression snapshot tests.

---

## 9) Maintenance & Audits
- **Weekly:** Compare routed model usage vs. success rate; demote tasks where SWE‑1.5 succeeds.
- **Monthly:** Re‑benchmark PDF→Image and OCR throughput; update DPI/defaults.
- **Quarterly:** Review export schemas with stakeholders; update normalization tables.
- **On failure:** Create a _"Promotion Note"_ in the issue describing why the model was upgraded (context/complexity/latency).

---

## 10) Appendix – Quick Checklists

**Acceptance Criteria Template**
- [ ] Unit tests added/updated
- [ ] Golden snapshots validated
- [ ] CLI flags documented
- [ ] Errors routed to review queue
- [ ] Perf note (before/after, CPU/GPU)

**PR Template Snippet**
- Scope: …
- Model used: … (SWE‑1.5 / Codex / Claude 4.5 / etc.)
- Why this model: …
- Tests: …
- Risks & rollbacks: …

**Troubleshooting Promotions**
- If SWE‑1.5 fails on context merges → try GPT‑5 Codex.
- If Codex struggles with policy/semantics → escalate to Claude 4.5 for design, then return to Codex/SWE for impl.
- For tiny edits → Haiku first.

---

**End of document.**
