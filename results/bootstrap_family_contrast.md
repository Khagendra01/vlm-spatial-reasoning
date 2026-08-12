# Bootstrap family-relative improvement contrasts

Paired bootstrap (B=10,000) over the 2,195 shared VSR test examples. Contrast C_f = Delta_f - Delta_orientation (percentage points).

## 2B zs -> 7B zs (scaling)

| family | acc1 % | acc2 % | Delta_f pp | contrast pp | 95% CI | P(contrast>0) |
|---|---|---|---|---|---|---|
| orientation | 62.8 | 63.5 | +0.7 | --- | --- | --- |
| depth | 68.9 | 75.2 | +6.2 | +5.5 | [-5.7, +16.5] | 0.834 |
| horizontal | 70.2 | 84.8 | +14.6 | +13.9 | [+2.9, +24.8] | 0.993 |
| containment | 83.4 | 89.3 | +5.9 | +5.1 | [-5.9, +16.2] | 0.820 |
| topology_contact | 80.5 | 80.3 | -0.2 | -0.9 | [-11.2, +9.4] | 0.429 |

## 7B zs -> 7B General LoRA (adaptation)

| family | acc1 % | acc2 % | Delta_f pp | contrast pp | 95% CI | P(contrast>0) |
|---|---|---|---|---|---|---|
| orientation | 63.5 | 65.7 | +2.2 | --- | --- | --- |
| depth | 75.2 | 82.3 | +7.1 | +5.0 | [-6.5, +16.5] | 0.802 |
| horizontal | 84.8 | 87.4 | +2.6 | +0.5 | [-10.7, +11.5] | 0.538 |
| containment | 89.3 | 92.9 | +3.6 | +1.5 | [-10.1, +13.0] | 0.594 |
| topology_contact | 80.3 | 84.4 | +4.1 | +2.0 | [-9.6, +13.3] | 0.634 |
