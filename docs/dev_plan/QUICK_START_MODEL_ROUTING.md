# Quick Start: Model-Based Task Routing in Windsurf
## Project 24-105: Truck Ticket Processing System

**Goal:** Route development tasks to optimal AI models for maintenance and enhancements.

**Status:** Project is 97% complete (30/31 issues done). This guide now focuses on maintenance, enhancements, and the remaining work.

---

## 🚀 **Current Status**

### **Completed (30/31 issues):**
- ✅ All core functionality implemented
- ✅ All export generators working
- ✅ OCR integration complete
- ✅ Database operations functional
- ✅ Comprehensive test coverage

### **Step 2: Reference the Routing Guide**
- Keep `WINDSURF_MODEL_ROUTING.md` open in a browser tab
- Quick lookup: Which model for which task type

### **Step 3: Use Task Templates**
- Copy templates from `WINDSURF_TASK_TEMPLATES.md`
- Fill in specifics from your GitHub issue
- Paste into Windsurf

---

## ⚡ **Fastest Workflow**

### **Starting a New Task:**

1. **Look at GitHub issue** → Check labels
   - Has `model:swe-1.5` label? → Use SWE-1.5
   - No label or `model:claude-4.5`? → Use Claude 4.5

2. **Open task template** → Match your task type:
   - Critical logic → Template 1 (Claude 4.5)
   - Boilerplate → Template 2 (SWE-1.5)
   - Orchestration → Template 3 (Claude 4.5)
   - Reports → Template 4 (Claude 4.5)
   - Test data → Template 5 (SWE-1.5)
   - Hybrid → Template 6 (Both)

3. **Fill in details** → Paste into Windsurf

---

## 📊 **Remaining Work & Future Enhancements**

| Status | Tasks | Model | Use Cases |
|--------|-------|-------|-----------|
| **Remaining** | 1 issue | Claude 4.5 | Production monitoring dashboard |
| **Maintenance** | Ongoing | SWE-1.5 | Bug fixes, minor enhancements |
| **Future** | TBD | Both | New features, optimizations |

### 🏷️ Labeling & Model Routing Checklist (Current Remaining Work)

1. **Apply priority/model labels in GitHub** (after importing `truck_ticket_issues_with_models.csv`):
   ```bash
   gh issue edit 1  --add-label "priority:critical" --add-label "model:claude-4.5"
   gh issue edit 2  --add-label "priority:critical" --add-label "model:claude-4.5"
   gh issue edit 3  --add-label "priority:critical" --add-label "model:claude-4.5"
   gh issue edit 5  --add-label "priority:medium"   --add-label "model:swe-1.5"
   gh issue edit 6  --add-label "priority:medium"   --add-label "model:swe-1.5"
   gh issue edit 7  --add-label "priority:low"      --add-label "model:hybrid"
   gh issue edit 8  --add-label "priority:low"      --add-label "model:hybrid"
   gh issue edit 9  --add-label "priority:low"      --add-label "model:hybrid"
   gh issue edit 10 --add-label "priority:low"      --add-label "model:swe-1.5"
   gh issue edit 11 --add-label "priority:low"      --add-label "model:swe-1.5"
   gh issue edit 12 --add-label "priority:low"      --add-label "model:hybrid"
   gh issue edit 13 --add-label "priority:low"      --add-label "model:swe-1.5"
   ```
   *Adjust numbers as needed if the tracker already contains live issues.*

2. **Map the 13 active remaining issues to models** (see `src/truck_tickets/IMPLEMENTATION_STATUS.md` for full scopes):
   - **Claude 4.5:** PDF → Image conversion; Material/Source/Destination extraction; Export implementations; Confidence scoring thresholds; Integration test design; Import vendor template rules; SQL optimization strategy; Review queue workflow.
   - **SWE-1.5:** Confidence-score adapters; GUI log wiring; Standalone export query wiring; Vendor template YAML plumbing; Index DDL; OCR cache implementation; Console script packaging.

3. **When tasks straddle both models**, split them into "Design" (Claude 4.5) and "Implementation" (SWE-1.5) subtasks and track both in GitHub for clearer routing.

4. **Reference docs before kicking off work:**
   - `src/truck_tickets/IMPLEMENTATION_STATUS.md` → Most recent remaining-issue scopes & DoD.
   - `docs/dev_plan/WINDSURF_MODEL_ROUTING.md` → Decision tree for model selection.
   - `docs/dev_plan/WINDSURF_TASK_TEMPLATES.md` → Prompt templates per task type.

5. **Critical-path order (Q4 2025 refresh):**
   1. PDF → Image conversion → 2. Material/Source/Destination extraction → 3. Export implementations → 4. Confidence scoring → 5. Export CLI DB queries → 6. GUI log wiring → 7. Integration tests → remaining items.

---

## 🎯 **Current Focus** (Remaining Work)

| Priority | Task | Model | Hours | Status |
|----------|------|-------|-------|--------|
| 🟢 P3 | #31: Production monitoring dashboard | Claude 4.5 | 8h | Optional |
| 🔄 Ongoing | Bug fixes and optimizations | SWE-1.5 | As needed | Maintenance |
| 🔄 Ongoing | Documentation updates | SWE-1.5 | As needed | Maintenance |

**Project Status: 97% Complete** ✅

---

## 🧠 **Decision Tree (When In Doubt)**

```
START: Look at task description

├─ Does it say "CRITICAL", "MUST", "100%", "compliance", "regulatory"?
│  └─ YES → Use Claude 4.5 (Template 1)
│
├─ Does it coordinate multiple modules or files?
│  └─ YES → Use Claude 4.5 (Template 3)
│
├─ Is it "Generate X from Y" (deterministic transform)?
│  └─ YES → Use SWE-1.5 (Template 2)
│
├─ Is it >80% boilerplate or following existing pattern?
│  └─ YES → Use SWE-1.5 (Template 2 or 5)
│
├─ Does it involve SQL pivots, complex queries, or reports?
│  └─ YES → Use Claude 4.5 (Template 4)
│
└─ Still unsure?
   └─ Default to Claude 4.5 (safer for first-time implementation)
```

---

## ✅ **Example: Your First Task** (Issue #4)

### **1. Check GitHub Issue**
```
Issue #4: Build duplicate detection logic (120-day window)
Labels: phase-2, priority-critical, backend, compliance
Model: claude-4.5 (implied - critical + compliance)
```

### **2. Open Template 1** (Critical Business Logic)
Copy from `WINDSURF_TASK_TEMPLATES.md` → Template 1

### **3. Fill in Specifics**
```markdown
TASK: Implement Duplicate Detection Logic (Issue #4)
MODEL: Claude Sonnet 4.5
PRIORITY: Critical

CONTEXT:
Implementing duplicate detection for Project 24-105 truck ticket processing.

REQUIREMENTS FROM SPEC v1.1:
1. Check (ticket_number, vendor_id) within 120-day rolling window
2. If duplicate: set duplicate_of, review_required=True
3. Route to review queue with comparison data
4. Edge cases: same ticket different vendors (NOT duplicate)

TARGET: src/truck_tickets/database/repository.py
METHOD: TicketRepository.check_duplicate()

ACCEPTANCE CRITERIA:
- Returns None if no duplicate
- Returns ticket_id if duplicate found
- Efficient SQL with indexes
- Unit tests with 5+ cases

Please implement with SQL query, edge handling, and tests.
```

### **4. Paste into Windsurf**
```bash
# In Windsurf:
windsurf > [Paste the filled template]

# Windsurf (using Claude 4.5) generates:
# - check_duplicate() method
# - SQL query with 120-day window
# - Edge case handling
# - Unit tests
```

### **5. Review & Test**
```python
# Review generated code
# Run tests: pytest tests/test_repository.py
# Commit: git commit -m "feat: implement duplicate detection (Issue #4)"
```

---

## 🚨 **Common Mistakes to Avoid**

### **❌ DON'T:**
1. Use SWE-1.5 for anything with "CRITICAL" or "compliance"
2. Use Claude 4.5 for simple ORM generation (waste of reasoning power)
3. Switch models mid-task (causes context loss)
4. Skip the template (inconsistent prompting)
5. Forget to review SWE-1.5 output (it can miss subtle requirements)

### **✅ DO:**
1. Check the issue label first
2. Use the template for your task type
3. Include spec section references in prompts
4. Review all generated code before committing
5. Write unit tests for critical logic

---

## 📈 **Measuring Success**

Track these metrics as you work through issues:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Time Savings** | ~30% on boilerplate | Compare hours: SWE-1.5 vs manual |
| **Code Quality** | High on critical logic | Code review pass rate |
| **Context Retention** | Minimal rework | How often you need to refactor? |
| **Test Coverage** | >80% | pytest --cov |
| **Spec Compliance** | 100% | Checklist against spec v1.1 |

---

## 🎯 **Success Checklist**

After completing Week 2 (40 hours):

- [ ] All 8 P0 tasks complete (duplicate detection, manifest validation, main processor, etc.)
- [ ] Database operations working (insert, duplicate check, review queue)
- [ ] Excel exporter generating 5 sheets matching legacy format
- [ ] End-to-end test: PDF → database → Excel output
- [ ] Manifest validation achieving 100% recall on test set
- [ ] Code reviewed and merged to main branch

---

## 📚 **Reference Documents**

Quick links to your implementation guides:

1. **Model Routing Guide** → `WINDSURF_MODEL_ROUTING.md`
   - Which model for which task type
   - Decision trees and examples

2. **Task Templates** → `WINDSURF_TASK_TEMPLATES.md`
   - 6 ready-to-use prompt templates
   - Examples for each GitHub issue type

3. **Enhanced Issues CSV** → `truck_ticket_issues_with_models.csv`
   - All 31 issues with model assignments
   - Import into GitHub for tracking

4. **Spec v1.1** → `Truck_Ticket_Processing_Complete_Spec_v1.1.md`
   - Complete technical specification
   - Reference for requirements

5. **Alignment Analysis** → `Alignment_Analysis_Report.md`
   - Worksheet analysis findings
   - Scope clarifications

---

## 💡 **Pro Tips**

### **For Maximum Efficiency:**

1. **Batch similar tasks**
   - Do all SWE-1.5 tasks in one session (flow state)
   - Do all Claude 4.5 tasks in another

2. **Start with SWE-1.5 tasks**
   - Generate boilerplate first (ORM, seed data)
   - Build on that foundation with Claude 4.5

3. **Use version control**
   - Branch per issue: `git checkout -b issue-4-duplicate-detection`
   - Commit after each working implementation

4. **Review before committing**
   - SWE-1.5 can be 90% correct but miss edge cases
   - Claude 4.5 needs validation against spec requirements

5. **Keep context fresh**
   - Reference spec sections in every prompt
   - Include relevant GitHub issue numbers

---

## 🎓 **Learning Curve**

**Week 1:** Getting used to model routing (~10% slower)
**Week 2:** Finding your rhythm (~same speed)
**Week 3+:** Significantly faster (~30% time savings)

The investment in setup pays off quickly!

---

## 🆘 **When Things Go Wrong**

### **Problem: SWE-1.5 missed a critical requirement**
**Solution:**
1. Don't blame the model - check if requirement was in prompt
2. Add missing context to template
3. Rerun with explicit requirement stated
4. If still missed → switch to Claude 4.5

### **Problem: Claude 4.5 too slow for simple task**
**Solution:**
1. Break task into design (Claude) + implementation (SWE-1.5)
2. Use Template 6 (multi-phase approach)
3. Get architecture from Claude, boilerplate from SWE-1.5

### **Problem: Lost context between model switches**
**Solution:**
1. Complete logical units with one model
2. Include full context in next model's prompt
3. Reference previous outputs explicitly

---

## 🎉 **You're Ready!**

You now have:
- ✅ 31 issues with model assignments
- ✅ Routing guide for decisions
- ✅ Templates for every task type
- ✅ Week 2 critical path defined
- ✅ Success metrics to track

**Next step:** Pick Issue #2 (ORM generation with SWE-1.5) or Issue #4 (Duplicate detection with Claude 4.5) and start building! 🚀

---

**Questions? Check the routing guide or task templates for detailed examples.**
