# Orientation Deep-Dive Analysis

## Key Findings

### Per-Relation Orientation Accuracy (137 examples total)

| Relation | N | 2B Zero | 2B LoRA | 7B Zero | 7B LoRA |
|----------|---|---------|---------|---------|---------|
| facing | 64 | 70.3% | 68.8% | 73.4% | **75.0%** |
| facing away from | 39 | 53.8% | 53.8% | 48.7% | **59.0%** |
| parallel to | 22 | 59.1% | 59.1% | 63.6% | 63.6% |
| perpendicular to | 12 | 58.3% | 58.3% | 58.3% | 41.7% |

### Transition Analysis

**Scaling: 2B zero-shot → 7B zero-shot**
- 28 examples wrong in both (persistent)
- 23 examples fixed by scaling (2B wrong → 7B right)
- 22 examples broken by scaling (2B right → 7B wrong)
- 64 examples correct in both

**Adaptation: 7B zero-shot → 7B General LoRA**
- 20 examples wrong in both (persistent)
- 30 examples fixed by LoRA (7B wrong → LoRA right)
- 27 examples broken by LoRA (7B right → LoRA wrong)
- 60 examples correct in both

### Persistent Hard Cases (20 examples)

Wrong in BOTH 7B zero-shot AND 7B LoRA:

**By relation:**
- facing away from: 9 (45%)
- facing: 4 (20%)
- parallel to: 4 (20%)
- perpendicular to: 3 (15%)

**By label:**
- True label (statement is correct): 16 (80%)
- False label (statement is incorrect): 4 (20%)

**Key observation:** "facing away from" dominates persistent failures. Models consistently fail to correctly identify when objects are facing away from each other.

### Pattern Analysis

The persistent failures show a clear pattern:

1. **"facing away from" is hardest** (9/20 persistent failures)
   - Models tend to predict "True" even when it's actually True (i.e., they're confused about the relationship)
   - 7B zero-shot is actually WORSE than 2B zero-shot on this relation (48.7% vs 53.8%)

2. **"parallel to" and "perpendicular to" are geometry-dependent**
   - These require understanding spatial alignment
   - Models sometimes get confused about the reference frame

3. **"facing" is relatively easier** but still has persistent failures
   - Usually when objects are small or partially occluded

### Next Steps

1. Manual inspection of 20 persistent failures using annotation tool
2. Categorize failures by:
   - Object pose clarity
   - Camera/viewpoint ambiguity
   - Parallel/perpendicular geometry
   - Front/back ambiguity
   - Subject/reference inversion
   - Small/occluded objects
   - Annotation quality
   - Model reasoning failure (clear image, wrong answer)

3. Decision point:
   - If dominated by vision-side issues → vision encoder adaptation
   - If dominated by relation inversion → hard negatives
   - If dominated by ambiguity → benchmark finding
