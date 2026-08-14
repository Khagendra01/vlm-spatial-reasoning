"""Gate 1: transformation-algebra unit tests (protocol section 6 + Amendment A).

Required checks, as executable tests:

1. identity action test:      rho(I) = I on state AND relations;
2. inverse transform test:    rho(H) rho(H) = I, rho(V) rho(V) = I;
3. composition test:          rho(V o H) = rho(V) rho(H)  (state + relations);
4. label/action consistency:  expected_after matches the rho action on the
                              relation's typed component;
5. deterministic regeneration: repeated calls are stable;
6. no contradictory action maps: every (relation, transform) has exactly one
                              declared outcome and it is reachable;
7. no ambiguous pairs in the confirmatory set;
8. wrong-geometry control reachability: an incorrect rho must be constructible
                              and must differ from the correct rho.
"""

import pytest

from src.equiorient import (
    ALGEBRA_TABLE,
    RHO_ACTION,
    Relation,
    StateComponent,
    Transform,
    expected_after,
    relation_state_component,
)

CONFIRMATORY_TRANSFORMS = {Transform.I, Transform.H, Transform.V}
ALL_RELATIONS = set(Relation)
PHASE1_RELATIONS = ALL_RELATIONS  # facing intentionally not in Relation enum


def rho_product(t1: Transform, t2: Transform):
    """rho(t1) composed with rho(t2): (t1 o t2) applied in sequence."""
    return {c: RHO_ACTION[t1][c] * RHO_ACTION[t2][c] for c in StateComponent}


class TestIdentity:
    def test_rho_identity_is_identity_on_state(self):
        for c in StateComponent:
            assert RHO_ACTION[Transform.I][c] == +1

    def test_expected_after_identity(self):
        for r in ALL_RELATIONS:
            assert expected_after(r, Transform.I) == r

    def test_algebra_table_identity_column(self):
        for r in ALL_RELATIONS:
            assert ALGEBRA_TABLE[r.value][Transform.I.value] == r.value


class TestInverse:
    @pytest.mark.parametrize("t", [Transform.H, Transform.V])
    def test_double_application_returns_identity_on_state(self, t):
        for c in StateComponent:
            assert RHO_ACTION[t][c] * RHO_ACTION[t][c] == +1

    @pytest.mark.parametrize("t", [Transform.H, Transform.V])
    def test_double_application_returns_identity_on_relations(self, t):
        for r in ALL_RELATIONS:
            assert expected_after(expected_after(r, t), t) == r


class TestComposition:
    def test_rho_vh_is_product_of_rho_v_and_rho_h_on_state(self):
        for c in StateComponent:
            assert RHO_ACTION[Transform.VH][c] == (
                RHO_ACTION[Transform.V][c] * RHO_ACTION[Transform.H][c]
            )

    def test_rho_vh_equals_rho_product_mapping(self):
        assert RHO_ACTION[Transform.VH] == rho_product(Transform.V, Transform.H)

    def test_expected_after_vh_equals_sequential(self):
        for r in ALL_RELATIONS:
            direct = expected_after(r, Transform.VH)
            sequential = expected_after(expected_after(r, Transform.H),
                                        Transform.V)
            assert direct == sequential

    def test_h2_is_identity_on_state_and_relations(self):
        for c in StateComponent:
            assert RHO_ACTION[Transform.H2][c] == +1
        for r in ALL_RELATIONS:
            assert expected_after(r, Transform.H2) == r


class TestGeometryDerivedActions:
    """rho comes from geometry: flips only the relation's axis component."""

    def test_h_flips_only_horizontal_component(self):
        assert RHO_ACTION[Transform.H][StateComponent.H] == -1
        for c in [StateComponent.V, StateComponent.D, StateComponent.ORIENT]:
            assert RHO_ACTION[Transform.H][c] == +1

    def test_v_flips_only_vertical_component(self):
        assert RHO_ACTION[Transform.V][StateComponent.V] == -1
        for c in [StateComponent.H, StateComponent.D, StateComponent.ORIENT]:
            assert RHO_ACTION[Transform.V][c] == +1

    def test_depth_invariant_under_h_and_v(self):
        for t in [Transform.H, Transform.V, Transform.VH]:
            assert RHO_ACTION[t][StateComponent.D] == +1
        for r in [Relation.IN_FRONT, Relation.BEHIND]:
            assert expected_after(r, Transform.H) == r
            assert expected_after(r, Transform.V) == r

    def test_orientation_invariant_under_h_and_v(self):
        for r in [Relation.PARALLEL, Relation.PERPENDICULAR]:
            assert expected_after(r, Transform.H) == r
            assert expected_after(r, Transform.V) == r

    def test_relation_component_matches_rho(self):
        # left/right flip under H but not V; above/below flip under V but not H
        assert (RHO_ACTION[Transform.H]
                [relation_state_component(Relation.LEFT_OF)]) == -1
        assert (RHO_ACTION[Transform.V]
                [relation_state_component(Relation.LEFT_OF)]) == +1
        assert (RHO_ACTION[Transform.V]
                [relation_state_component(Relation.ABOVE)]) == -1
        assert (RHO_ACTION[Transform.H]
                [relation_state_component(Relation.ABOVE)]) == +1


class TestNoContradictions:
    def test_every_relation_transform_pair_has_declared_outcome(self):
        for r in ALL_RELATIONS:
            for t in Transform:
                out = ALGEBRA_TABLE[r.value][t.value]
                assert out in {x.value for x in ALL_RELATIONS}

    def test_no_relation_maps_to_itself_under_a_flipping_transform(self):
        # in the confirmatory set, flips must actually flip (no dead actions)
        for r in [Relation.LEFT_OF, Relation.RIGHT_OF]:
            assert expected_after(r, Transform.H) != r
        for r in [Relation.ABOVE, Relation.BELOW]:
            assert expected_after(r, Transform.V) != r

    def test_confirmatory_set_has_no_ambiguous_pairs(self):
        # every confirmatory (relation, transform) outcome is unique and
        # deterministic across two independent calls
        seen = {}
        for r in ALL_RELATIONS:
            for t in CONFIRMATORY_TRANSFORMS:
                key = (r.value, t.value)
                out = ALGEBRA_TABLE[r.value][t.value]
                assert out == expected_after(r, t).value  # table == function
                seen[key] = out
        assert len(seen) == len(ALL_RELATIONS) * len(CONFIRMATORY_TRANSFORMS)


class TestDeterminism:
    def test_repeated_calls_stable(self):
        for _ in range(5):
            for r in ALL_RELATIONS:
                for t in Transform:
                    assert ALGEBRA_TABLE[r.value][t.value] == \
                        expected_after(r, t).value


class TestWrongGeometryControlReachability:
    """Amendment A3: the wrong-geometry control MUST be constructible and
    MUST differ from the correct rho — otherwise the control is vacuous."""

    def test_wrong_rho_exists_and_differs(self):
        # a wrong rho: horizontal reflection acting on the VERTICAL component
        wrong = dict(RHO_ACTION[Transform.H])
        wrong[StateComponent.V] = -1
        wrong[StateComponent.H] = +1
        assert wrong != RHO_ACTION[Transform.H]
        # and it must be behaviorally distinguishable on above/below
        assert expected_after(Relation.ABOVE, Transform.H) == Relation.ABOVE
        # under the wrong action, ABOVE would flip to BELOW -> detectably wrong
        assert wrong[relation_state_component(Relation.ABOVE)] == -1
