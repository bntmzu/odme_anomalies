from typing import List, Dict
from odme_anomalies.schemas.anomaly_schema import AnomalyAttributeIn


# Base threat level scores based on anomaly category
BASE_SCORES: Dict[str, int] = {
    "Měňavec": 70,
    "Elementál": 50,
    "Přízrak": 30,
}

# Modifiers applied to threat level based on specific attributes
WEIGHT_ADJUSTMENTS = {
    "agresivita": lambda v: int(v) * 2,
    "agresivita_odhad": {
        "nízká": -10,
        "střední": 0,
        "vysoká": 20,
    },
}


def calculate_threat_level(
    category: str,
    attributes: List[AnomalyAttributeIn],
) -> int:
    """
    Calculate the threat level of an anomaly between 0 and 100.

    Steps:
    1. Start with a base score by category:
         - "Měňavec" → 70
         - "Elementál" → 50
         - "Přízrak" → 30
         - any other → 10
    2. For each attribute:
       - If key == "agresivita": add (int(value) * 2)
       - If key == "agresivita_odhad": look up verbal adjustment:
           "nízká" → -10, "střední" → 0, "vysoká" → +20
    3. Clamp the final score into [0, 100].
    """

    # 1. Get base score from category
    score = BASE_SCORES.get(category, 10)

    # 2. Process all attributes
    for attr in attributes:
        if attr.key == "agresivita":
            try:
                score += WEIGHT_ADJUSTMENTS["agresivita"](attr.value)
            except (ValueError, TypeError):
                # ignore non‑integer or invalid values
                continue

        elif attr.key == "agresivita_odhad":
            score += WEIGHT_ADJUSTMENTS["agresivita_odhad"].get(attr.value.lower(), 0)

    # 3. Clamp score to 0–100
    return max(0, min(score, 100))
