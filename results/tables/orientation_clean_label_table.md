# Clean-Label Orientation Robustness (VSR test)

Full test (137) vs subsets with annotation-questionable / ambiguous examples removed.
Exclusion sets from the 48-example manual audit (results/orientation_persistent_annotations.csv).

| Condition | full (137) | −questionable (132) | clear (124) | strict (107) |
|---|---|---|---|---|
| 2B zero-shot | 0.628 (n=137) | 0.652 (n=132) | 0.669 (n=124) | 0.757 (n=107) |
| 2B structured | 0.533 (n=137) | 0.523 (n=132) | 0.516 (n=124) | 0.533 (n=107) |
| 2B General LoRA | 0.620 (n=137) | 0.636 (n=132) | 0.645 (n=124) | 0.729 (n=107) |
| 2B Targeted LoRA | 0.642 (n=137) | 0.659 (n=132) | 0.685 (n=124) | 0.766 (n=107) |
| 7B zero-shot | 0.635 (n=137) | 0.652 (n=132) | 0.685 (n=124) | 0.720 (n=107) |
| 7B General LoRA | 0.657 (n=137) | 0.674 (n=132) | 0.702 (n=124) | 0.785 (n=107) |
| 7B Targeted LoRA | 0.642 (n=137) | 0.659 (n=132) | 0.694 (n=124) | 0.720 (n=107) |
| 7B Hard-Neg LoRA | 0.664 (n=137) | 0.682 (n=132) | 0.702 (n=124) | 0.766 (n=107) |
| 7B Projector LoRA | 0.642 (n=137) | 0.659 (n=132) | 0.694 (n=124) | 0.738 (n=107) |
| 7B Vision+Projector LoRA | 0.642 (n=137) | 0.652 (n=132) | 0.685 (n=124) | 0.738 (n=107) |
