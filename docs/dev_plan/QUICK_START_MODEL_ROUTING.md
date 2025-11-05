# Quick Start: Model-Based Task Routing in Windsurf
## Project 24-105: Truck Ticket Processing System

**Goal:** Route your 31 GitHub issues to optimal AI models for best quality and speed.

---

## 🚀 **3-Minute Setup**

### **Step 1: Import GitHub Issues**
```bash
# Upload truck_ticket_issues_with_models.csv to your GitHub repo
# GitHub → Issues → Import
# This creates 31 issues with model labels pre-assigned
```

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

## 📊 **Your 31 Issues Breakdown**

| Model | Issues | Hours | Use Cases |
|-------|--------|-------|-----------|
| **Claude 4.5** | 18 | ~110h | Business logic, compliance, orchestration, reports |
| **SWE-1.5** | 13 | ~50h | ORM generation, seed data, parsers, test fixtures |
| **Total** | 31 | ~160h | Complete v1.0 implementation |

---

## 🎯 **Week 2 Critical Path** (Next 40 hours)

Start with these in order:

| Priority | Issue | Model | Hours | Template |
|----------|-------|-------|-------|----------|
| 🔴 P0 | #4: Duplicate detection | Claude 4.5 | 3h | Template 1 |
| 🔴 P0 | #5: Manifest validation | Claude 4.5 | 3h | Template 1 |
| 🟡 P1 | #2: ORM models | SWE-1.5 | 2h | Template 2 |
| 🟡 P1 | #3: Seed data | SWE-1.5 | 2h | Template 2 |
| 🔴 P0 | #7: Main processor | Claude 4.5 | 8h | Template 3 |
| 🔴 P0 | #8: Review queue | Claude 4.5 | 3h | Template 1 |
| 🔴 P0 | #12: Excel exporter | Claude 4.5 | 8h | Template 4 |
| 🟡 P1 | #11: Test fixtures | SWE-1.5 | 3h | Template 5 |

**Total: ~32 hours** → Completes core v1.0 functionality

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
