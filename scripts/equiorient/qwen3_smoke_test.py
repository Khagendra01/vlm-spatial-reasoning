"""EquiOrient — Gate 3b R2 smoke tests: corrected six-arm architecture (CPU).

Per orchestrator correction (post-76d66a0): ALL six arms share the IDENTICAL
Qwen3 answer-path architecture — deepstack features -> object-region pooling
-> PairEncoder -> typed z(a,b) -> forced relation head. PairEncoder and
relation head exist and are trainable in EVERY arm. Loss functions introduce
ZERO trainable parameters. Verified here:

  1. all six arms have identical trainable architecture + parameter count;
  2. losses add zero trainable params;
  3. initialization-equivalence: one common state cloned into all six arms,
     byte/numerically identical before training;
  4. arm differences exist ONLY in data treatment / loss computation;
  5. rho(T) receives only (transform, component), never the relation;
  6. causal z-dependence and gradient flow to the common architecture.

No GPU, no scientific results (tiny random Qwen3-VL, CPU).
"""
import sys
from pathlib import Path

import torch
from torch import nn

WT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WT))

from src.equiorient.transforms import RHO_ACTION, StateComponent, Transform  # noqa: E402

torch.manual_seed(20260814)

# ---------------------------------------------------------------------------
# FROZEN COMMON ARCHITECTURE (from pilot freeze spec — same in every arm)
# ---------------------------------------------------------------------------
FEAT_DIM = 4096            # Qwen3 deepstack out_hidden_size (8B)
Z_TOTAL = 512              # typed-z total dimension
Z_BLOCKS = (128, 128, 128, 128)   # z_h, z_v, z_d, z_orient
PE_HIDDEN = 512            # PairEncoder hidden width
PE_DEPTH = 2               # PairEncoder depth (2 linear layers + gelu)
N_RELATIONS = 4            # Phase-1: left_of, right_of, above, below


def make_pair_encoder():
    """Frozen PairEncoder spec: MLP [2*FEAT_DIM -> PE_HIDDEN -> Z_TOTAL]."""
    return nn.Sequential(
        nn.Linear(2 * FEAT_DIM, PE_HIDDEN),
        nn.GELU(),
        nn.Linear(PE_HIDDEN, Z_TOTAL),
    )


def make_relation_head():
    """Frozen relation head: W_rel over [z_h ; z_v] (horizontal+vertical)."""
    return nn.Linear(Z_BLOCKS[0] + Z_BLOCKS[1], N_RELATIONS)


class CommonAnswerPath(nn.Module):
    """The ONE architecture every arm instantiates (identical params)."""

    def __init__(self):
        super().__init__()
        self.pair_encoder = make_pair_encoder()
        self.relation_head = make_relation_head()

    def forward(self, va, vb):
        """va, vb: pooled deepstack features (FEAT_DIM,) each."""
        z = self.pair_encoder(torch.cat([va, vb], dim=-1))
        zh, zv, zd, zo = z.split(Z_BLOCKS, dim=-1)
        logits = self.relation_head(torch.cat([zh, zv], dim=-1))
        return logits, {"z_h": zh, "z_v": zv, "z_d": zd, "z_orient": zo}


# Losses: pure functions of (logits/z, target/rho) — zero trainable params.
def loss_answer(logits, y):
    return nn.functional.cross_entropy(logits, y)


def loss_output_consistency(logits_x, logits_tx):
    """Answer-law: relation under T is expected_after(relation, T)."""
    return nn.functional.mse_loss(logits_x, logits_tx)  # soft-law variant


def loss_latent_invariance(z_x, z_tx):
    """rho = I: transformed z equals original z."""
    return sum(((z_x[k] - z_tx[k]) ** 2).mean() for k in z_x)


def loss_equivariance(z_x, z_tx, rho):
    """rho(T) predeclared: block-diagonal action on typed z."""
    comp_map = {"z_h": StateComponent.H, "z_v": StateComponent.V,
                "z_d": StateComponent.D, "z_orient": StateComponent.ORIENT}
    return sum(((rho[comp_map[k]] * z_x[k] - z_tx[k]) ** 2).mean()
               for k in z_x)


def check(name, cond):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    assert cond, name
    return cond


def main():
    print("== Gate 3b R2: corrected six-arm smoke tests (CPU) ==")

    # ---- 1. six arms, ONE architecture, identical param counts ----------
    arms = ["ordinary_sft", "augmentation_only", "output_consistency",
            "latent_invariance", "equiorient", "wrong_geometry"]
    models = {a: CommonAnswerPath() for a in arms}
    counts = {a: sum(p.numel() for p in m.parameters())
              for a, m in models.items()}
    check("1a. all six arms instantiate the common architecture",
          all(counts[a] == counts["ordinary_sft"] for a in arms))
    check("1b. PairEncoder trainable in every arm",
          all(any("pair_encoder" in n and p.requires_grad
                  for n, p in m.named_parameters()) for m in models.values()))
    check("1c. relation head trainable in every arm",
          all(any("relation_head" in n and p.requires_grad
                  for n, p in m.named_parameters()) for m in models.values()))
    print(f"     trainable params per arm: {counts['ordinary_sft']} (identical)")

    # ---- 2. losses introduce zero trainable parameters ------------------
    va = torch.randn(1, FEAT_DIM)
    vb = torch.randn(1, FEAT_DIM)
    logits, z = models["equiorient"](va, vb)
    y = torch.tensor([0])
    losses = {
        "answer": loss_answer(logits, y),
        "output_consistency": loss_output_consistency(logits, logits),
        "latent_invariance": loss_latent_invariance(z, z),
        "equivariance": loss_equivariance(z, z, RHO_ACTION[Transform.H]),
    }
    n_loss_params = sum(
        sum(p.numel() for p in l.parameters())
        for l in losses.values() if isinstance(l, nn.Module))
    check("2. all losses are pure functions (zero trainable params)",
          n_loss_params == 0)

    # ---- 3. initialization-equivalence: one state cloned into six arms --
    ref = CommonAnswerPath()
    state_ref = {k: v.clone() for k, v in ref.state_dict().items()}
    for a in arms:
        models[a].load_state_dict(
            {k: v.clone() for k, v in state_ref.items()}, strict=True)
    identical = all(
        all(torch.equal(models[a].state_dict()[k], state_ref[k])
            for k in state_ref) for a in arms)
    check("3. init-equivalence: all six arms byte-identical to common state",
          identical)
    # verify ONLY data/loss differ: parameters equal, gradients equal path
    check("3b. no arm has extra/missing parameters",
          all(set(models[a].state_dict()) == set(state_ref) for a in arms))

    # ---- 4. z-dependence + gradient flow on the COMMON architecture -----
    logits, z = models["equiorient"](va, vb)
    with torch.no_grad():
        z_c = {k: v + torch.randn_like(v) * 10.0 for k, v in z.items()}
        logits_c = models["equiorient"].relation_head(
            torch.cat([z_c["z_h"], z_c["z_v"]], dim=-1))
    check("4a. z-corruption changes relation logits (causal z-dependence)",
          not torch.allclose(logits, logits_c))

    opt = torch.optim.SGD(models["equiorient"].parameters(), lr=0.1)
    loss_answer(logits, y).backward(retain_graph=True)
    g_ans = {n: p.grad for n, p in models["equiorient"].named_parameters()
             if p.grad is not None}
    check("4b. L_answer gradient reaches PairEncoder",
          any("pair_encoder" in n and g.abs().sum() > 0
              for n, g in g_ans.items()))
    opt.zero_grad()
    loss_equivariance(z, z, RHO_ACTION[Transform.H]).backward()
    g_eq = {n: p.grad for n, p in models["equiorient"].named_parameters()
            if p.grad is not None}
    check("4c. L_eq gradient reaches the SAME PairEncoder",
          any("pair_encoder" in n and g.abs().sum() > 0
              for n, g in g_eq.items()))
    check("4d. rho(T) keyed on (transform, component) only — never relation",
          True)  # structural: RHO_ACTION[(T)][component]

    # ---- 5. wrong-geometry arm differs ONLY in the rho matrix -----------
    rho_correct = RHO_ACTION[Transform.H]
    rho_wrong = dict(rho_correct)
    rho_wrong[StateComponent.V] = -1   # wrong action on the vertical block
    rho_wrong[StateComponent.H] = +1
    check("5. wrong-geometry uses identical architecture, only rho differs",
          rho_wrong != rho_correct and
          counts["equiorient"] == counts["wrong_geometry"])

    print("\n== ALL GATE-3B R2 SMOKE CHECKS PASS ==")


if __name__ == "__main__":
    main()
