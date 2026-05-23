# MASA SAM Eval Report

**Run:** 2026-05-23T21:53:44.972801+00:00  
**Fixtures:** 150  
**Errors:** 0

---

## POPULATION CAVEAT

The use cases were mined from CFPB complaints and Reddit, which skew toward the general population and toward collections-heavy issues. MASA's members skew older (55+), Medicare/Medicare Advantage, and ambulance-centric. The eval therefore demonstrates *the engine works on complaint-derived cases* — it does not, on its own, demonstrate *the engine works for MASA's specific member population*. This caveat should be stated wherever eval results are reported; a MASA-representative test set is a recommended follow-on.

---

## Summary Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Triage classification accuracy | >=85% | 100.0% | ✓ |
| Citation validity | 100% | 100.0% | ✓ |
| Code-decode coverage (excl. CPT) | >=95% | 100.0% | ✓ |
| NSA rule-engine correctness | 100% | 100.0% | ✓ |
| Ground-ambulance node produces rate | 100% | 100.0% | ✓ |
| Cases ending in concrete next step | >=95% | 100.0% | ✓ |
| Human-review rules → escalation | 100% | 100.0% | ✓ |
| No false confident answer | 100% | 100.0% | ✓ |

---

## Broker-Deck Metrics

- **Share of bills with identified issues:** 36.7% (55/150)
- **Dollar exposure surfaced:** $0.00 across 150 cases
- **Share of cases reaching a concrete next step:** 100.0%

---

## Failures Requiring Attention

_No failures — all cases passed all automated checks._

---

## Case-Level Detail

| Fixture ID | Primary Need | PRD Fit | Workflow | Triage | Cites | Next Step |
|------------|--------------|---------|----------|--------|-------|-----------|
| GS-0001 | transparency_general | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |
| GS-0002 | appeal_pathway | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0003 | ambulance_advocacy | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0004 | itemized_bill_guidance | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0005 | duplicate_billing | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0006 | collection_with_underlying_bil | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0007 | code_decode | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0008 | appeal_pathway | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0009 | nsa_surprise_billing | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0010 | appeal_pathway | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0011 | plan_benefit_with_collection | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0012 | medicare_general | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0013 | ambulance_advocacy | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0014 | ambulance_advocacy | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0015 | appeal_pathway | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0016 | collection_with_underlying_bil | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0017 | collection_with_underlying_bil | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0018 | nsa_general | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0019 | plan_benefit_with_collection | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0020 | transparency_unspecified | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |
| GS-0021 | plan_benefit_lookup | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0022 | collection_with_underlying_bil | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0023 | transparency_unspecified | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |
| GS-0024 | medicare_general | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0025 | collection_with_underlying_bil | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0026 | network_verification | MODERATE | workflow_2 | ✓ | ✓ | ✓ |
| GS-0027 | itemized_bill_guidance | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0028 | ambulance_advocacy | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0029 | code_decode_eob | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0030 | transparency_general | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |
| GS-0031 | medical_necessity_denial | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0032 | plan_benefit_lookup | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0033 | code_decode | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0034 | transparency_general | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |
| GS-0035 | medical_necessity_denial | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0036 | transparency_unspecified | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |
| GS-0037 | transparency_general | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |
| GS-0038 | medicare_coverage | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0039 | appeal_pathway | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0040 | medicare_coverage | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0041 | medical_necessity_denial | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0042 | duplicate_billing | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0043 | ambulance_general | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0044 | network_verification | MODERATE | workflow_2 | ✓ | ✓ | ✓ |
| GS-0045 | code_decode | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0046 | medicare_coverage | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0047 | appeal_pathway | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0048 | itemized_bill_guidance | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0049 | medicare_coverage | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0050 | itemized_bill_guidance | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0051 | nsa_surprise_billing | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0052 | medicare_coverage | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0053 | transparency_unspecified | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |
| GS-0054 | ambulance_advocacy | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0055 | medical_necessity_denial | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0056 | appeal_pathway | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0057 | medicare_coverage | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0058 | code_decode | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0059 | ambulance_general | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0060 | medicare_general | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0061 | nsa_general | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0062 | network_verification | MODERATE | workflow_2 | ✓ | ✓ | ✓ |
| GS-0063 | ambulance_general | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0064 | code_decode_eob | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0065 | transparency_unspecified | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |
| GS-0066 | collection_with_underlying_bil | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0067 | medical_necessity_denial | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0068 | medicare_general | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0069 | code_decode_eob | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0070 | plan_benefit_with_collection | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0071 | code_decode_eob | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0072 | code_decode_eob | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0073 | plan_benefit_lookup | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0074 | medical_necessity_denial | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0075 | code_decode | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0076 | medical_necessity_denial | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0077 | plan_benefit_lookup | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0078 | medical_necessity_denial | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0079 | ambulance_advocacy | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0080 | itemized_bill_guidance | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0081 | network_verification | MODERATE | workflow_2 | ✓ | ✓ | ✓ |
| GS-0082 | appeal_pathway | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0083 | duplicate_billing | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0084 | nsa_surprise_billing | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0085 | plan_benefit_lookup | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0086 | plan_benefit_with_collection | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0087 | network_verification | MODERATE | workflow_2 | ✓ | ✓ | ✓ |
| GS-0088 | medicare_general | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0089 | medicare_coverage | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0090 | plan_benefit_lookup | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0091 | transparency_unspecified | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |
| GS-0092 | code_decode_eob | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0093 | transparency_general | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |
| GS-0094 | network_verification | MODERATE | workflow_2 | ✓ | ✓ | ✓ |
| GS-0095 | ambulance_advocacy | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0096 | plan_benefit_lookup | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0097 | collection_with_underlying_bil | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0098 | nsa_surprise_billing | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0099 | nsa_general | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0100 | appeal_pathway | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0101 | itemized_bill_guidance | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0102 | medical_necessity_denial | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0103 | itemized_bill_guidance | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0104 | duplicate_billing | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0105 | plan_benefit_with_collection | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0106 | plan_benefit_with_collection | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0107 | ambulance_general | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0108 | code_decode | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0109 | ambulance_general | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0110 | nsa_general | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0111 | medicare_coverage | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0112 | collection_with_underlying_bil | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0113 | itemized_bill_guidance | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0114 | plan_benefit_with_collection | PARTIAL | workflow_4 | ✓ | ✓ | ✓ |
| GS-0115 | ambulance_general | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0116 | nsa_surprise_billing | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0117 | code_decode | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0118 | duplicate_billing | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0119 | nsa_general | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0120 | medicare_general | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0121 | ambulance_advocacy | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0122 | medical_necessity_denial | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0123 | nsa_surprise_billing | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0124 | itemized_bill_guidance | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0125 | nsa_surprise_billing | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0126 | plan_benefit_lookup | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0127 | code_decode_eob | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0128 | nsa_general | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0129 | code_decode | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0130 | medicare_coverage | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0131 | nsa_general | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0132 | medicare_general | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0133 | medicare_general | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0134 | network_verification | MODERATE | workflow_2 | ✓ | ✓ | ✓ |
| GS-0135 | duplicate_billing | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0136 | ambulance_general | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0137 | network_verification | MODERATE | workflow_2 | ✓ | ✓ | ✓ |
| GS-0138 | ambulance_advocacy | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0139 | duplicate_billing | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0140 | itemized_bill_guidance | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0141 | nsa_surprise_billing | STRONG | workflow_2 | ✓ | ✓ | ✓ |
| GS-0142 | medicare_coverage | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0143 | network_verification | MODERATE | workflow_2 | ✓ | ✓ | ✓ |
| GS-0144 | duplicate_billing | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0145 | transparency_general | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |
| GS-0146 | transparency_unspecified | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |
| GS-0147 | duplicate_billing | MODERATE | workflow_1 | ✓ | ✓ | ✓ |
| GS-0148 | code_decode_eob | STRONG | workflow_1 | ✓ | ✓ | ✓ |
| GS-0149 | transparency_unspecified | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |
| GS-0150 | transparency_unspecified | PARTIAL | workflow_1 | ✓ | ✓ | ✓ |

---

## Notes

- **Fixture source:** MASA_Use_Case_Coverage_Analysis.xlsx (stratified sample, seed=42)
- **Fixture count:** 150
- **PRD Fit filter:** STRONG, MODERATE, PARTIAL rows only
- **State default:** FL (dataset has no state column)
- **LLM calls:** All still stubs (answer-card rendering is Python fallback, not LLM-polished)
- **NSA rules status:** All 59 rules are `status=draft`; all NSA determinations degrade to `human_review_required`

> The use cases were mined from CFPB complaints and Reddit, which skew toward the general population and toward collections-heavy issues. MASA's members skew older (55+), Medicare/Medicare Advantage, and ambulance-centric. The eval therefore demonstrates *the engine works on complaint-derived cases* — it does not, on its own, demonstrate *the engine works for MASA's specific member population*. This caveat should be stated wherever eval results are reported; a MASA-representative test set is a recommended follow-on.
