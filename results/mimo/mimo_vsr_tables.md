# MiMo-V2.5 zero-shot VSR (additive evidence)

| Condition | Overall | Orientation | Depth | Horizontal | Containment | Topology/contact |
|---|---|---|---|---|---|---|
| MiMo-V2.5 zero-shot | 79.5 | 65.7 | 74.8 | 81.9 | 87.1 | 84.6 |

Orientation family: n=137 | Wilson 95% CI [57.4, 73.1]

## Orientation per relation
| relation | n | acc % | Wilson 95% |
|---|---|---|---|
| facing | 64 | 75.0 | [63.2, 84.0] |
| facing away from | 39 | 56.4 | [41.0, 70.7] |
| parallel to | 22 | 63.6 | [43.0, 80.3] |
| perpendicular to | 12 | 50.0 | [25.4, 74.6] |

## Clean-label subsets (frozen first-annotator masks)
| subset | n | acc % |
|---|---|---|
| full | 137 | 65.7 |
| minus_questionable | 132 | 67.4 |
| clear | 124 | 69.3 |
| strict | 107 | 71.0 |

## Consistency (complementary statements)
| family | n | orig acc % | flip acc % | consistent % | contradiction % |
|---|---|---|---|---|---|
| LR | 245 | 75.9 | 49.4 | 51.8 | 34.7 |
| FB | 314 | 73.2 | 60.8 | 56.1 | 37.3 |
| FF | 103 | 66.0 | 60.2 | 42.7 | 54.4 |
| PP | 34 | 58.8 | 47.1 | 23.5 | 76.5 |
