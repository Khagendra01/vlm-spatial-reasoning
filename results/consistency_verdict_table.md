# Consistency Verdict Patterns (CPU-only, from committed CSVs)

Strict families (exactly one truth value): complementary verdicts are the consistent outcome. Original and flipped True rates are the observed answer base rates on each member.

## 7B_zero_shot

| Family | n | both True | both False | complementary | orig True rate | flip True rate |
|---|---|---|---|---|---|---|
| facing / facing-away | 103 | 0 (0.0%) | 65 (63.1%) | 38 (36.9%) | 0.20 | 0.17 |
| in-front-of / behind | 314 | 7 (2.2%) | 128 (40.8%) | 179 (57.0%) | 0.43 | 0.18 |
| left / right | 245 | 0 (0.0%) | 103 (42.0%) | 142 (58.0%) | 0.50 | 0.08 |
| parallel/perpendicular (soft; both-True is the true contradiction) | 34 | 2 (5.9%) | 25 (73.5%) | --- | 0.18 | 0.15 |

## LM_only_LoRA

| Family | n | both True | both False | complementary | orig True rate | flip True rate |
|---|---|---|---|---|---|---|
| facing / facing-away | 103 | 25 (24.3%) | 10 (9.7%) | 68 (66.0%) | 0.62 | 0.52 |
| in-front-of / behind | 314 | 18 (5.7%) | 74 (23.6%) | 222 (70.7%) | 0.55 | 0.27 |
| left / right | 245 | 12 (4.9%) | 90 (36.7%) | 143 (58.4%) | 0.50 | 0.18 |
| parallel/perpendicular (soft; both-True is the true contradiction) | 34 | 11 (32.4%) | 11 (32.4%) | --- | 0.59 | 0.41 |

## hardneg_LoRA

| Family | n | both True | both False | complementary | orig True rate | flip True rate |
|---|---|---|---|---|---|---|
| facing / facing-away | 103 | 18 (17.5%) | 5 (4.9%) | 80 (77.7%) | 0.60 | 0.52 |
| in-front-of / behind | 314 | 23 (7.3%) | 67 (21.3%) | 224 (71.3%) | 0.56 | 0.30 |
| left / right | 245 | 13 (5.3%) | 93 (38.0%) | 139 (56.7%) | 0.51 | 0.16 |
| parallel/perpendicular (soft; both-True is the true contradiction) | 34 | 11 (32.4%) | 8 (23.5%) | --- | 0.62 | 0.47 |

## projector_LoRA

| Family | n | both True | both False | complementary | orig True rate | flip True rate |
|---|---|---|---|---|---|---|
| facing / facing-away | 103 | 18 (17.5%) | 15 (14.6%) | 70 (68.0%) | 0.53 | 0.50 |
| in-front-of / behind | 314 | 10 (3.2%) | 96 (30.6%) | 208 (66.2%) | 0.50 | 0.23 |
| left / right | 245 | 9 (3.7%) | 96 (39.2%) | 140 (57.1%) | 0.49 | 0.15 |
| parallel/perpendicular (soft; both-True is the true contradiction) | 34 | 5 (14.7%) | 12 (35.3%) | --- | 0.50 | 0.29 |

## vision_proj_LoRA

| Family | n | both True | both False | complementary | orig True rate | flip True rate |
|---|---|---|---|---|---|---|
| facing / facing-away | 103 | 14 (13.6%) | 23 (22.3%) | 66 (64.1%) | 0.49 | 0.43 |
| in-front-of / behind | 314 | 13 (4.1%) | 89 (28.3%) | 212 (67.5%) | 0.52 | 0.24 |
| left / right | 245 | 4 (1.6%) | 95 (38.8%) | 146 (59.6%) | 0.51 | 0.12 |
| parallel/perpendicular (soft; both-True is the true contradiction) | 34 | 13 (38.2%) | 8 (23.5%) | --- | 0.59 | 0.56 |

