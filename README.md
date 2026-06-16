# Causal Inference — Learning Notes & Projects

Working through **Brady Neal's [A Brief Introduction to Causal Inference](https://www.bradyneal.com/causal-inference-course)**.
Each section below is added as I finish it.

---

## Lecture 1 · Slides 5–8: Simpson's Paradox

### What I learned

**Simpson's Paradox** is when a trend visible in every subgroup disappears or *reverses* once the subgroups are combined.

Brady Neal's motivating example: a COVID-19 trial comparing Treatment A vs B.

|  | Mild condition | Severe condition | **Total** |
|--|---------------|-----------------|-----------|
| Treatment A | 15% mortality | 30% mortality | **16%** |
| Treatment B | 10% mortality | 20% mortality | **19%** |

A is worse in *every* subgroup — yet the Total column says B is worse.  
Why? Patients in severe condition (who have higher baseline mortality) were disproportionately assigned to Treatment A.

The column headers tell the whole story:
- Subgroup columns → **E[Y | T, C]** (outcome given treatment *and* condition)
- Total column → **E[Y | T]** (outcome given treatment only)

When the subgroups are mixed in unequal proportions across treatments, E[Y | T] is contaminated by whoever ended up in each group — not just the treatment itself.

**Correlation ≠ Causation.** E[Y | T=1] − E[Y | T=0] measures association, not the causal effect of T on Y.

### Project: Amazon Dynamic Currency Conversion (DCC)

Applied the same structure to Amazon's DCC A/B test, where **device type** is the confounder:

|  | Mobile | Desktop | **Total** |
|--|--------|---------|-----------|
| Shown DCC offer (T=1) | 22.9% | 41.8% | **24.2%** |
| Not shown (T=0) | 13.5% | 35.3% | **29.9%** |
| Effect | **+9.4% ✓** | **+6.5% ✓** | **−5.7% ✗** |

DCC helps in every device group — yet the aggregate says it hurts.  
Reason: Amazon shows the DCC offer far more on mobile (80%) than desktop (10%), and mobile users have lower baseline checkout rates. The treatment group ends up packed with low-converting mobile users; the control group with high-converting desktop users.

**Run the demo:**
```bash
uv run streamlit run app.py
```

---

*More sections will be added as I progress through the course.*
