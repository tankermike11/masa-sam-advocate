"""
Tests for the data-access module against pilot.db.

All tests in this module are skipped if data/pilot.db is absent.
"""

from pathlib import Path

import pytest

PILOT_DB_PATH = Path("data/pilot.db")

pytestmark = pytest.mark.skipif(
    not PILOT_DB_PATH.exists(),
    reason="pilot.db not present — copy snapshot to data/pilot.db first",
)

from backend.data_access.interface import (  # noqa: E402 — after pytestmark guard
    get_ambulance_reference_rate,
    get_nsa_rules,
    lookup_code,
    resolve_source,
    search_plan,
)


def test_lookup_icd10cm_code():
    result = lookup_code("ICD10CM", "A00")
    assert result is not None
    assert result["code"] == "A00"
    assert "cholera" in result["description"].lower()
    assert result["source_id"] == "a01_icd10cm"


def test_lookup_hcpcs_ambulance_code():
    result = lookup_code("HCPCS", "A0425")
    assert result is not None
    assert result["code_type"] == "HCPCS"
    assert result["code"] == "A0425"


def test_lookup_cpt_returns_fallback_not_none():
    result = lookup_code("CPT", "99213")
    assert result is not None
    assert "fallback" in result
    assert result["code_type"] == "CPT"
    assert result["source_id"] == "a04_cpt_handling"
    assert result["description"] is None


def test_lookup_unknown_code_returns_none():
    result = lookup_code("ICD10CM", "ZZZZZZZ")
    assert result is None


def test_search_plan_by_issuer_with_state():
    results = search_plan("Premera", state="AK")
    assert len(results) > 0
    assert all("premera" in r["plan_name"].lower() for r in results)
    assert all(r["state"] == "AK" for r in results)


def test_search_plan_no_state_filter():
    results = search_plan("Blue Cross")
    assert len(results) > 0


def test_search_plan_no_match_returns_empty():
    results = search_plan("XYZXYZXYZ_NO_MATCH_12345")
    assert results == []


def test_get_ambulance_reference_rate_found():
    result = get_ambulance_reference_rate("A0425", "AK")
    assert result is not None
    assert result["hcpcs"] == "A0425"
    assert result["reference_rate"] > 0
    assert result["reference_rate_dollars"] == result["reference_rate"] / 100
    assert "source_id" in result
    assert "effective_year" in result


def test_get_ambulance_reference_rate_invalid_state_returns_none():
    result = get_ambulance_reference_rate("A0425", "XX")
    assert result is None


def test_get_nsa_rules_ground_ambulance_category():
    rules = get_nsa_rules(["K"])
    assert len(rules) == 11
    assert all(r["category"] == "K" for r in rules)


def test_get_nsa_rules_multiple_categories():
    rules = get_nsa_rules(["A", "B"])
    categories = {r["category"] for r in rules}
    assert categories == {"A", "B"}
    assert len(rules) == 10   # 4 in A + 6 in B


def test_get_nsa_rules_empty_list_returns_empty():
    rules = get_nsa_rules([])
    assert rules == []


def test_get_nsa_rules_all_have_status_field():
    rules = get_nsa_rules(["A"])
    assert all("status" in r for r in rules)


def test_resolve_source_found():
    result = resolve_source("a01_icd10cm")
    assert result is not None
    assert result["source_id"] == "a01_icd10cm"
    assert result["publisher"] == "CMS"


def test_resolve_source_not_found():
    result = resolve_source("nonexistent_source_xyz")
    assert result is None
