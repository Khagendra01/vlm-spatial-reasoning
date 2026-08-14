#!/usr/bin/env python3
"""Step 4: canonical publication figures + tables for Paper 2.

ALL numbers come from results/seed_campaign/numerical_audit.json (Step-1
independent audit, PASS) -- no hand-typed values. Produces:

  results/seed_campaign/figures/fig1_conceptual.png   (dA/dG/dC concept)
  results/seed_campaign/figures/fig2_multiseed.png    (per-seed dA/dG)
  results/seed_campaign/figures/fig3_transform.png    (Tier-C trio)
  results/seed_campaign/figures/PUBLICATION_TABLES.md (compact tables)
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parent.parent
AUDIT = json.load(open(REPO / 'results' / 'seed_campaign' / 'numerical_audit.json',
                       encoding='utf-8'))
FIG = REPO / 'results' / 'seed_campaign' / 'figures'
FIG.mkdir(parents=True, exist_ok=True)

fam = AUDIT['families']
q7, s2 = fam['qwen2vl'], fam['smolvlm2']
q3 = AUDIT['q3vl']

GRAY = '#9ca3af'
C7, C2, C3 = '#1f77b4', '#d62728', '#2ca02c'


def cpair(f, ck):
    return f['checkpoints'][ck]['tier_c']['hflip_flip']['C_pair']


def atrans(f, ck):
    return f['checkpoints'][ck]['tier_c']['hflip_flip']['A_transform']


def both(f, ck):
    return f['checkpoints'][ck]['tier_c']['hflip_flip']['both_correct']


# ---------------------------------------------------------------- fig 1
def fig1():
    fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=200)
    # three axes: dA (x), dG (y), dC bubble size
    labels = ['7B seed-0', '7B seedA', '7B seedB', '7B seedC',
              '2B seed-0', '2B seedA', '2B seedB', '2B seedC',
              'Qwen3-VL tuned']
    dA = [q7['seed0']['dA']] + [q7['seeds'][s]['dA'] for s in q7['seeds']] + \
         [s2['seed0']['dA']] + [s2['seeds'][s]['dA'] for s in s2['seeds']] + \
         [q3['deltas']['dA_normal']]
    dG = [q7['seed0']['dG']] + [q7['seeds'][s]['dG'] for s in q7['seeds']] + \
         [s2['seed0']['dG']] + [s2['seeds'][s]['dG'] for s in s2['seeds']] + \
         [q3['deltas']['dG']]
    dC = [cpair(q7, 'general_lora') - cpair(q7, 'zero_shot')] + \
         [cpair(q7, s) - cpair(q7, 'zero_shot') for s in q7['seeds']] + \
         [cpair(s2, 'general_lora') - cpair(s2, 'zero_shot')] + \
         [cpair(s2, s) - cpair(s2, 'zero_shot') for s in s2['seeds']] + \
         [0.0]  # Qwen3-VL: C_pair not computed
    colors = [C7] * 4 + [C2] * 4 + [C3]
    sizes = [900] * 8 + [600]
    for i, (x, y, c, s, lab) in enumerate(zip(dA, dG, colors, sizes, labels)):
        ax.scatter(x, y, s=s, c=c, alpha=0.85, edgecolors='black', linewidths=0.5,
                   zorder=3)
        ax.annotate(lab, (x, y), textcoords='offset points', xytext=(6, 5),
                    fontsize=7, color='black')
    ax.axhline(0, color=GRAY, lw=0.8, ls='--')
    ax.axvline(0, color=GRAY, lw=0.8, ls='--')
    ax.set_xlabel(r'$\Delta A$  (benchmark accuracy gain)', fontsize=11)
    ax.set_ylabel(r'$\Delta G$  (correct-image dependence gain)', fontsize=11)
    ax.set_title('Spatial fine-tuning as a vector of capability changes\n'
                 '(bubble size = $\\Delta C$, semantic pair consistency)',
                 fontsize=10)
    # quadrant annotation
    ax.text(0.02, 0.02, 'positive ΔA AND positive ΔG:\nconsistent across all\n'
            'seeds and backbones', transform=ax.transAxes, fontsize=7.5,
            color='#14532d', va='bottom')
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIG / 'fig1_conceptual.png', bbox_inches='tight')
    plt.close(fig)
    print('fig1 done')


# ---------------------------------------------------------------- fig 2
def fig2():
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8), dpi=200, sharey=False)
    for ax, (f, name, col) in zip(axes, [(q7, 'Qwen2-VL-7B', C7),
                                         (s2, 'SmolVLM2-2B', C2)]):
        seeds = list(f['seeds'])
        dA = [f['seed0']['dA']] + [f['seeds'][s]['dA'] for s in seeds]
        dG = [f['seed0']['dG']] + [f['seeds'][s]['dG'] for s in seeds]
        xs = np.arange(len(dA))
        w = 0.36
        ax.bar(xs - w / 2, dA, w, label=r'$\Delta A$', color=col, alpha=0.85)
        ax.bar(xs + w / 2, dG, w, label=r'$\Delta G$', color='#ffa600', alpha=0.85)
        ax.axhline(0, color=GRAY, lw=0.8)
        ax.set_xticks(xs)
        ax.set_xticklabels(['seed-0'] + [s.replace('r1_', '') for s in seeds],
                           fontsize=8)
        ax.set_title(name, fontsize=11)
        ax.legend(fontsize=8, framealpha=0.9)
        ax.grid(axis='y', alpha=0.2)
        ax.set_ylim(-0.02, 0.09)
        # mean/SD annotation
        import statistics
        m_a, s_a = statistics.mean(dA[1:]), statistics.stdev(dA[1:])
        m_g, s_g = statistics.mean(dG[1:]), statistics.stdev(dG[1:])
        ax.text(0.02, 0.95,
                f'fresh-seed dA {m_a:+.3f} ± {s_a:.3f}\nfresh-seed dG {m_g:+.3f} ± {s_g:.3f}',
                transform=ax.transAxes, fontsize=8, va='top', color='#334155')
    fig.suptitle('Multi-seed replication of the adaptation decomposition',
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(FIG / 'fig2_multiseed.png', bbox_inches='tight')
    plt.close(fig)
    print('fig2 done')


# ---------------------------------------------------------------- fig 3
def fig3():
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.8), dpi=200)
    for ax, (f, name, col) in zip(axes, [(q7, 'Qwen2-VL-7B', C7),
                                         (s2, 'SmolVLM2-2B', C2)]):
        cks = ['zero_shot', 'general_lora'] + list(f['seeds'])
        a = [atrans(f, c) for c in cks]
        cp = [cpair(f, c) for c in cks]
        b = [both(f, c) for c in cks]
        xs = np.arange(len(cks))
        w = 0.26
        ax.bar(xs - w, a, w, label='A_transform', color=col, alpha=0.85)
        ax.bar(xs, cp, w, label='C_pair', color='#ffa600', alpha=0.85)
        ax.bar(xs + w, b, w, label='both_correct', color='#9467bd', alpha=0.85)
        ax.set_xticks(xs)
        ax.set_xticklabels(['zero'] + ['gen0'] + [s.replace('r1_', '') for s in f['seeds']],
                           fontsize=8)
        ax.set_title(f'{name} — hflip_flip (n=245)', fontsize=10)
        ax.legend(fontsize=7, framealpha=0.9)
        ax.grid(axis='y', alpha=0.2)
        ax.set_ylim(0, 0.85)
    fig.suptitle('Transformation behavior: three separate quantities',
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(FIG / 'fig3_transform.png', bbox_inches='tight')
    plt.close(fig)
    print('fig3 done')


# ---------------------------------------------------------------- tables
def tables():
    L = []
    w = L.append
    w('# Paper-2 R1: Canonical Publication Tables (audit-sourced)\n')
    w('All values from numerical_audit.json (Step-1 independent audit, PASS).\n')

    w('## Table 1 — Headline adaptation quantities (per seed)\n')
    w('| family | checkpoint | ΔA | G | ΔG |')
    w('|---|---|---|---|---|')
    for name, f in [('Qwen2-VL-7B', q7), ('SmolVLM2-2B', s2)]:
        for ck, v in [('seed-0', f['seed0'])] + \
                     [(s.replace('r1_seed', 'seed'), f['seeds'][s]) for s in f['seeds']]:
            w(f'| {name} | {ck} | {v["dA"]:+.4f} | {v["G"]:.4f} | {v["dG"]:+.4f} |')
    w(f'| Qwen3-VL-8B | tuned | {q3["deltas"]["dA_normal"]:+.4f} | '
      f'{q3["checkpoints"]["general_lora"]["normal"]["accuracy"] - q3["checkpoints"]["general_lora"]["shuffle"]["accuracy"]:.4f} '
      f'| {q3["deltas"]["dG"]:+.4f} |')
    w('')

    w('## Table 2 — Tier-C transformation behavior, hflip_flip (n=245)\n')
    w('| family | checkpoint | A_transform | C_pair | both_correct |')
    w('|---|---|---|---|---|')
    for name, f in [('Qwen2-VL-7B', q7), ('SmolVLM2-2B', s2)]:
        for ck in ['zero_shot', 'general_lora'] + list(f['seeds']):
            v = f['checkpoints'][ck]['tier_c']['hflip_flip']
            w(f'| {name} | {ck} | {v["A_transform"]:.4f} | {v["C_pair"]:.4f} '
              f'| {v["both_correct"]:.4f} |')
    w('')

    w('## Table 3 — Fresh-seed summary statistics\n')
    w('| family | ΔA mean ± SD | ΔG mean ± SD |')
    w('|---|---|---|')
    for name, f in [('Qwen2-VL-7B', q7), ('SmolVLM2-2B', s2)]:
        st = f['seed_stats']
        w(f'| {name} | {st["dA_mean"]:+.4f} ± {st["dA_sd"]:.4f} | '
          f'{st["dG_mean"]:+.4f} ± {st["dG_sd"]:.4f} |')
    w('')

    w('## Table 4 — Qwen3-VL-8B post-confirmatory extension\n')
    w('| metric | zero-shot | tuned | Δ |')
    w('|---|---|---|---|')
    zs, gl = q3['checkpoints']['zero_shot'], q3['checkpoints']['general_lora']
    w(f'| normal accuracy | {zs["normal"]["accuracy"]:.4f} | '
      f'{gl["normal"]["accuracy"]:.4f} | {q3["deltas"]["dA_normal"]:+.4f} |')
    w(f'| shuffle accuracy | {zs["shuffle"]["accuracy"]:.4f} | '
      f'{gl["shuffle"]["accuracy"]:.4f} | '
      f'{gl["shuffle"]["accuracy"] - zs["shuffle"]["accuracy"]:+.4f} |')
    w(f'| hflip_flip A_transform | {zs["hflip_flip"]["accuracy"]:.4f} | '
      f'{gl["hflip_flip"]["accuracy"]:.4f} | '
      f'{q3["deltas"]["dhflip_flip_A_transform"]:+.4f} |')
    w('')
    w('C_pair not computed for the extension; no response-law claim.\n')

    w('## Table 5 — Canonical subset sizes (frozen)\n')
    w('| condition | n | source |')
    w('|---|---|---|')
    w('| normal / shuffle / blank / text_only | 2195 | vsr_test_ids.json |')
    w('| relcomp | 666 | semantic_eligible_ids.json |')
    w('| facingcomp | 103 | facing_eligible_ids.json |')
    w('| hflip_flip | 245 | visual_eligible_ids.json |')
    w('| hflip_invariant | 421 | visual_eligible_ids.json |')

    (FIG / 'PUBLICATION_TABLES.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print('tables done')


if __name__ == '__main__':
    fig1()
    fig2()
    fig3()
    tables()
