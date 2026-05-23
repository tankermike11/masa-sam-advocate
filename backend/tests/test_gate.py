"""
Unit tests for the monetization gate (PRD §9).
No DB dependency — pure function tests against the real pricing_rules.yaml.
"""

from backend.escalation.service import GateDecision, evaluate_gate, _load_pricing_config


def test_waived_tier_emergency_shield_plus():
    decision = evaluate_gate(is_masa_member=True, masa_plan_tier="Emergency Shield Plus")
    assert decision.fee_applies is False
    assert decision.tier_matched == "Emergency Shield Plus"
    assert decision.message  # non-empty


def test_waived_tier_lifetime():
    decision = evaluate_gate(is_masa_member=True, masa_plan_tier="Lifetime")
    assert decision.fee_applies is False
    assert decision.tier_matched == "Lifetime"


def test_non_waived_tier_charged():
    decision = evaluate_gate(is_masa_member=True, masa_plan_tier="Basic")
    assert decision.fee_applies is True
    assert decision.tier_matched is None
    assert decision.message


def test_masa_member_none_tier_charged():
    """None plan_tier is not in waived_tiers — fee applies."""
    decision = evaluate_gate(is_masa_member=True, masa_plan_tier=None)
    assert decision.fee_applies is True
    assert decision.tier_matched is None


def test_masa_member_unknown_tier_charged():
    decision = evaluate_gate(is_masa_member=True, masa_plan_tier="Unknown Tier XYZ")
    assert decision.fee_applies is True


def test_non_member_charged():
    decision = evaluate_gate(is_masa_member=False, masa_plan_tier=None)
    assert decision.fee_applies is True


def test_non_member_with_tier_still_charged():
    """Non-member path ignores tier — future state, always charged."""
    decision = evaluate_gate(is_masa_member=False, masa_plan_tier="Emergency Shield Plus")
    assert decision.fee_applies is True


def test_gate_reads_real_pricing_rules_yaml():
    """Gate uses real config file; waived_tiers matches PRD §9."""
    config = _load_pricing_config()
    assert "member" in config
    assert "waived_tiers" in config["member"]
    waived = config["member"]["waived_tiers"]
    assert "Emergency Shield Plus" in waived
    assert "Lifetime" in waived


def test_waived_message_differs_from_charged_message():
    waived = evaluate_gate(is_masa_member=True, masa_plan_tier="Lifetime")
    charged = evaluate_gate(is_masa_member=True, masa_plan_tier="Basic")
    assert waived.message != charged.message


def test_gate_decision_is_pydantic_model():
    result = evaluate_gate(is_masa_member=True, masa_plan_tier="Lifetime")
    assert isinstance(result, GateDecision)
    assert isinstance(result.fee_applies, bool)
    assert isinstance(result.message, str)
