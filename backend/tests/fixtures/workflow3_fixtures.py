"""Workflow 3 document generation test fixtures."""

WORKFLOW3_FIXTURES: list[tuple[dict, dict]] = [
    # 1 — Billing error: itemized bill request always generated
    (
        {
            "insurance_situation": "commercial_employer",
            "state": "FL",
            "problem_type": "billing_error",
            "amount_billed": 500.0,
            "codes_present": [{"code_type": "ICD10CM", "code": "A00"}],
        },
        {"document_types_include": ["itemized_bill_request"]},
    ),
    # 2 — Denial present: internal appeal added
    (
        {
            "insurance_situation": "commercial_employer",
            "state": "FL",
            "problem_type": "clean_denial",
            "denial_present": True,
            "denial_codes": ["1"],
        },
        {"document_types_include": ["itemized_bill_request", "internal_appeal"]},
    ),
    # 3 — Balance bill: dispute letter added
    (
        {
            "insurance_situation": "commercial_employer",
            "state": "FL",
            "problem_type": "balance_bill",
            "amount_billed": 1800.0,
            "amount_patient_responsibility": 1500.0,
        },
        {"document_types_include": ["itemized_bill_request", "balance_bill_dispute"]},
    ),
    # 4 — Self-pay + GFE received: PPDR added
    (
        {
            "insurance_situation": "uninsured_self_pay",
            "state": "FL",
            "problem_type": "surprise_out_of_network",
            "gfe_received": True,
            "gfe_expected_charges": [{"provider_name": "ABC Ambulance", "expected_charge": 900.0}],
            "amount_billed": 1800.0,
        },
        {
            "document_types_include": [
                "itemized_bill_request",
                "balance_bill_dispute",
                "ppdr_initiation",
            ]
        },
    ),
    # 5 — No PPDR when not self-pay
    (
        {
            "insurance_situation": "commercial_employer",
            "state": "FL",
            "problem_type": "billing_error",
            "gfe_received": True,
        },
        {"document_types_exclude": ["ppdr_initiation"]},
    ),
    # 6 — No internal appeal when denial_present=False
    (
        {
            "insurance_situation": "commercial_employer",
            "state": "FL",
            "problem_type": "billing_error",
            "denial_present": False,
        },
        {"document_types_exclude": ["internal_appeal"]},
    ),
]
