"""Combine indicators into a transparent screening category.

Rules (deliberately simple, not statistically calibrated, not a fraud probability):
  High concern : any validation FAIL, or an exact/same-file/conflicting duplicate
  Needs review : any validation REVIEW, a near-duplicate, an anomaly flag, or low field completeness (<75%)
  Low concern  : none of the above
The final decision always belongs to a human reviewer.
"""
DISCLAIMER = ("Screening alerts are prompts for human review, not findings of fraud. "
              "The final decision belongs to a human reviewer.")


def screen(completeness: float, validation: list, duplicates: list, anomaly: dict) -> dict:
    indicators = []
    high = review = False
    if completeness < 0.75:
        review = True
        indicators.append({"source": "extraction", "level": "REVIEW",
                           "detail": f"Only {completeness:.0%} of required fields were found."})
    for v in validation:
        if v["status"] == "FAIL":
            high = True
            indicators.append({"source": "validation", "level": "HIGH", "detail": f"{v['rule']}: {v['explanation']}"})
        elif v["status"] == "REVIEW":
            review = True
            indicators.append({"source": "validation", "level": "REVIEW", "detail": f"{v['rule']}: {v['explanation']}"})
    for d in duplicates:
        o = d["other"]
        label = f"{d['match_type']} match with record #{o.get('id')} ({o.get('vendor')} / {o.get('invoice_number')})"
        if d["match_type"] in ("exact", "same_file", "conflict"):
            high = True
            indicators.append({"source": "duplicates", "level": "HIGH", "detail": f"{label}: {d['reasons'][0]}"})
        else:
            review = True
            indicators.append({"source": "duplicates", "level": "REVIEW", "detail": f"{label}: {d['reasons'][0]}"})
    if anomaly and anomaly.get("flag"):
        review = True
        indicators.append({"source": "anomaly", "level": "REVIEW",
                           "detail": f"Isolation Forest flagged the record (score {anomaly['score']})."})
    category = "High concern" if high else "Needs review" if review else "Low concern"
    return {"category": category, "indicators": indicators, "disclaimer": DISCLAIMER}
