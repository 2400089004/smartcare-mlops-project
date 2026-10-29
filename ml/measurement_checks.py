# Broad demonstration guardrails for data quality and screening flags only.
# These are not diagnostic thresholds, clinical advice, or emergency triage rules.

ALLOWED_RANGES = {
    "heart_rate_bpm": (20, 250),
    "spo2_percent": (50, 100),
    "temperature_c": (25, 45),
    "systolic_bp_mmhg": (50, 280),
    "diastolic_bp_mmhg": (30, 180),
    "glucose_mg_dl": (20, 800),
}

def check_measurements(payload):
    unknown = set(payload) - set(ALLOWED_RANGES)
    if unknown:
        raise ValueError(f"Unsupported measurement field(s): {', '.join(sorted(unknown))}")

    flags = []
    for field, value in payload.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be a number")
        low, high = ALLOWED_RANGES[field]
        if not low <= value <= high:
            flags.append({
                "field": field,
                "kind": "outside_accepted_input_range",
                "message": "Check the value and measurement units; repeat or seek professional advice as appropriate."
            })

    # Only illustrative flags, not a medical assessment.
    if "spo2_percent" in payload and payload["spo2_percent"] < 90:
        flags.append({
            "field": "spo2_percent",
            "kind": "requires_prompt_attention",
            "message": "A low oxygen reading can be serious. Recheck device placement; seek urgent medical assessment, especially with symptoms."
        })
    return flags
