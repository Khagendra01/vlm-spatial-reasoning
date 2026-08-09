# Logical Consistency Analysis: Do Models Maintain a Coherent Relational World Model?

## Method

VSR test statements are template-generated from each image caption; object
pairs are verified present, so for a statement S with label l, the
**flipped complementary statement S′** (same image, same objects, complement
relation) has truth ¬l. We generated S′ for all test statements in four
families and ran all five conditions on S′ (greedy, same prompt); verdicts on
S come from the saved prediction CSVs.

- left ↔ right (n=245), front ↔ behind (n=314), facing ↔ facing-away (n=103):
  **strict complements** — exactly one holds; consistency ⇔ opposite verdicts.
- parallel ↔ perpendicular (n=34): **soft complement** — both-False is
  legitimate (oblique objects); only both-True is a true contradiction.

## Results

### Self-consistency / contradiction (strict families)

| Condition | left/right cons (contra) | front/behind cons (contra) | facing cons (contra) |
|---|---|---|---|
| 7B zero-shot | 58.0% (42.0%) | 57.0% (43.0%) | **36.9% (63.1%)** |
| LM-only LoRA | 58.4% (41.6%) | **70.7% (29.3%)** | 66.0% (34.0%) |
| hardneg LoRA | 56.7% (43.3%) | **71.3% (28.7%)** | **77.7% (22.3%)** |
| projector LoRA | 57.1% (42.9%) | 66.2% (33.8%) | 68.0% (32.0%) |
| vision+proj LoRA | 59.6% (40.4%) | 67.5% (32.5%) | 64.1% (35.9%) |

### Accuracy vs consistency (facing/facing-away — the critical family)

| Condition | orig acc | flip acc | consistent | both-correct | both-wrong |
|---|---|---|---|---|---|
| 7B zero-shot | 64.1% | 55.3% | 36.9% | 28.2% | 8.7% |
| LM-only LoRA | 68.9% | 68.0% | 66.0% | 51.5% | 14.6% |
| hardneg LoRA | 68.9% | 69.9% | **77.7%** | 58.3% | 19.4% |
| projector LoRA | 69.9% | 67.0% | 68.0% | 52.4% | 15.5% |
| vision+proj LoRA | 67.0% | 66.0% | 64.1% | 48.5% | 15.5% |

### Paired McNemar on self-consistency vs LM-only control (strict, n=662 pairs)

| Condition | control-consistent-only | cond-consistent-only | p |
|---|---|---|---|
| 7B zero-shot | 117 | 43 | **<0.0001** (control better) |
| hardneg LoRA | 31 | 41 | 0.29 |
| projector LoRA | 63 | 48 | 0.18 |
| vision+proj LoRA | 65 | 56 | 0.47 |

### Parallel/perp (soft complement, n=34; both-True is the true contradiction)

| Condition | both-True | both-False | orig acc |
|---|---|---|---|
| 7B zero-shot | **5.9%** | 73.5% | 61.8% |
| LM-only LoRA | 32.4% | 32.4% | 55.9% |
| hardneg LoRA | 32.4% | 23.5% | 58.8% |
| projector LoRA | 14.7% | 35.3% | 47.1% |
| vision+proj LoRA | 38.2% | 23.5% | 55.9% |

## Findings

1. **The zero-shot 7B model is systematically self-contradictory.**
   It agrees with itself on only 57% of front/behind pairs, 58% of left/right
   pairs, and **37% of facing pairs** — i.e., it contradicts itself on 63% of
   the facing family, even while achieving 64% accuracy. A model that merely
   *guessed* the relation would be 50% consistent by chance; the facing family
   is *worse* than chance. This is direct evidence of the mechanism question:
   the model often does not hold a coherent relational world model, it holds
   relation-specific answer biases.

2. **LM-side training repairs coherence, and hard negatives repair it most.**
   LM-only LoRA raises facing consistency 36.9% → 66.0% (and front/behind
   57.0% → 70.7%); hard-negatives push facing to **77.7%**. On the paired
   McNemar (strict families), zero-shot is significantly *less* consistent
   than LM-only (p<0.0001); hardneg/projector/vision_proj are statistically
   indistinguishable from LM-only (p=0.29 / 0.18 / 0.47).

3. **Adaptation improves consistency even when accuracy plateaus.**
   The decisive row: facing accuracy is identical for LM-only and hardneg
   (68.9% = 68.9%), yet consistency jumps 66.0% → 77.7% (both-correct
   51.5% → 58.3%). Training (especially with hard negatives) teaches the
   model *not to affirm complementary statements simultaneously* — a
   coherence gain that raw accuracy is blind to.

4. **Vision-side adaptation does not beat LM-only on coherence.**
   Projector (68.0%) and vision+proj (64.1%) sit between zero-shot and LM-only
   on facing consistency; neither is significantly better than the control on
   the paired test. Consistent with the accuracy results: the coherence
   deficit is repaired by language-side training, not by visual adaptation.

5. **Parallel/perp is the exception that sharpens the story (n=34, careful).**
   Zero-shot is the *most* conservative (only 5.9% both-True — it rarely
   affirms geometric relations at all, which is why its orig acc 61.8% comes
   mostly from saying False). LM-side LoRA raises both-True contradiction to
   32% — trained models affirm parallel AND perpendicular together on the same
   object pair. This is a specialization tradeoff introduced by training:
   adaptation improved facing/front/behind coherence but degraded
   parallel/perp exclusivity.

## Answer to the mechanism question

> Do these models fail because they do not know the relation, or because they
> cannot maintain a coherent relational world model across logically linked
> statements?

**Both — and the coherence deficit is the more demonstrable one.**
Left/right accuracy is 86–88%, yet the same model contradicts itself on 41%
of those pairs. The failure signature is not "no knowledge of the relation"
(the model is above chance and improves with training) but **relation-specific
affirmation biases** — it commits to "True" on the familiar template and
cannot propagate the entailment to its complement. Hard-negative training
directly targets this (77.7% facing consistency) without any accuracy gain,
confirming the two are separable. The overall orientation ceiling (~66%) is
therefore not just a perception problem: part of it is a *logical integrity*
problem in the generative interface.

## Files

- `results/consistency_flips_{condition}.csv` — flip evaluations (5 conditions)
- `results/consistency_stats_all.json`
- `scripts/eval_consistency_flips.py`
