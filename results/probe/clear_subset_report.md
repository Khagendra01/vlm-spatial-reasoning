# Human-Clear Test Subset Evaluation

Annotated persistent-failure test ids excluded: 48 total.

- clear: 137 - 13 = 124 examples (exclude ['annotation_questionable', 'camera_viewpoint_ambiguity'])

- strict: 137 - 23 = 114 examples (+ ['front_back_object_ambiguous', 'intrinsic_orientation_ambiguous', 'small_occluded_object'])

## T1_facing_vs_facingaway

| method | full | clear (n) | strict (n) |
|---|---|---|---|
| ungrounded_vit_linear | 0.650 (n=103) | 0.649 (n=97) | 0.648 (n=88) |
| ungrounded_vit_mlp | 0.563 (n=103) | 0.598 (n=97) | 0.659 (n=88) |
| ungrounded_merger_linear | 0.689 (n=103) | 0.711 (n=97) | 0.716 (n=88) |
| ungrounded_merger_mlp | 0.612 (n=103) | 0.608 (n=97) | 0.614 (n=88) |
| grounded_vit_linear | 0.616 (n=99) | 0.602 (n=93) | 0.583 (n=84) |
| grounded_vit_mlp | 0.616 (n=99) | 0.624 (n=93) | 0.560 (n=84) |
| grounded_merger_linear | 0.657 (n=99) | 0.656 (n=93) | 0.643 (n=84) |
| grounded_merger_mlp | 0.626 (n=99) | 0.387 (n=93) | 0.536 (n=84) |
| gen_zeroshot | 0.641 (n=103) | 0.660 (n=97) | 0.682 (n=88) |
| gen_lora | 0.689 (n=103) | 0.722 (n=97) | 0.784 (n=88) |

## T2_parallel_vs_perp

| method | full | clear (n) | strict (n) |
|---|---|---|---|
| ungrounded_vit_linear | 0.618 (n=34) | 0.556 (n=27) | 0.577 (n=26) |
| ungrounded_vit_mlp | 0.676 (n=34) | 0.593 (n=27) | 0.654 (n=26) |
| ungrounded_merger_linear | 0.647 (n=34) | 0.593 (n=27) | 0.615 (n=26) |
| ungrounded_merger_mlp | 0.647 (n=34) | 0.593 (n=27) | 0.654 (n=26) |
| grounded_vit_linear | 0.536 (n=28) | 0.500 (n=22) | 0.524 (n=21) |
| grounded_vit_mlp | 0.536 (n=28) | 0.545 (n=22) | 0.571 (n=21) |
| grounded_merger_linear | 0.536 (n=28) | 0.545 (n=22) | 0.571 (n=21) |
| grounded_merger_mlp | 0.607 (n=28) | 0.409 (n=22) | 0.429 (n=21) |
| gen_zeroshot | 0.618 (n=34) | 0.778 (n=27) | 0.808 (n=26) |
| gen_lora | 0.559 (n=34) | 0.630 (n=27) | 0.615 (n=26) |

## T3_4way

| method | full | clear (n) | strict (n) |
|---|---|---|---|
| ungrounded_vit_linear | 0.526 (n=137) | 0.548 (n=124) | 0.544 (n=114) |
| ungrounded_vit_mlp | 0.504 (n=137) | 0.532 (n=124) | 0.579 (n=114) |
| ungrounded_merger_linear | 0.533 (n=137) | 0.556 (n=124) | 0.570 (n=114) |
| ungrounded_merger_mlp | 0.474 (n=137) | 0.508 (n=124) | 0.482 (n=114) |
| grounded_vit_linear | 0.504 (n=127) | 0.496 (n=115) | 0.495 (n=105) |
| grounded_vit_mlp | 0.488 (n=127) | 0.409 (n=115) | 0.486 (n=105) |
| grounded_merger_linear | 0.520 (n=127) | 0.522 (n=115) | 0.514 (n=105) |
| grounded_merger_mlp | 0.496 (n=127) | 0.513 (n=115) | 0.448 (n=105) |
| gen_zeroshot | 0.635 (n=137) | 0.685 (n=124) | 0.711 (n=114) |
| gen_lora | 0.657 (n=137) | 0.702 (n=124) | 0.746 (n=114) |
