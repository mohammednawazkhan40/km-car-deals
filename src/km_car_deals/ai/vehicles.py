"""Vehicle name vocabulary used by the intake agent.

This is a fixed, conservative mapping of manufacturers to their common models
for the Indian pre-owned market. The intake agent only uses it to confirm a
brand/model the user explicitly typed — it never invents a car not present in
the user's message.
"""

# Each brand maps to a set of model tokens (lowercase, spaces->"_").
MODEL_REGISTRY: dict[str, list[str]] = {
    "hyundai": [
        "i20", "creta", "verna", "venue", "alto", "santoro", "aura", "tucson",
        "creta_knight", "grand_i10", "grand_i10_nios", "exter", "i10",
    ],
    "maruti": [
        "swift", "baleno", "dzire", "wagonr", "altok10", "alto", "ertiga",
        "brezza", "vitara_brezza", "ciaz", "s_presso", "ignis", "celerio",
        "jimny", "fronx", "gv", "eeco",
    ],
    "tata": [
        "nexon", "punch", "tiago", "altroz", "harrier", "safari", "tigor", "curvv",
    ],
    "mahindra": [
        "xuv700", "xuv300", "scorpio", "scorpio_n", "thar", "bolero", "xuv500",
        "tuv300", "kushaq", "marazzo",
    ],
    "kia": ["seltos", "sonet", "carens", "ev6", "sportage", "carnival"],
    "honda": ["city", "amaze", "brio", "jazz", "wr_v", "civic", "elevate", "cr_v"],
    "toyota": ["innova", "fortuner", "corolla", "etios", "glanza", "rumion", "camry"],
    "volkswagen": ["polo", "virtus", "taigun", "vento", "santana"],
    "skoda": ["slavia", "kushaq", "octavia", "rapid", "superb"],
    "renault": ["kwid", "duster", "triber", "kiger"],
    "nissan": ["magnite", "sunny", "kicks", "terrano"],
    "mg": ["hector", "zseven", "astor", "comet", "gloster", "windsor"],
    "ford": ["ecosport", "endeavour", "figo", "aspire"],
    "suzuki": ["swift", "baleno", "dzire", "ertiga", "brezza", "jimny"],
    "mercedes": ["c_class", "e_class", "gla", "glc", "a_class", "s_class"],
    "bmw": ["x1", "x3", "x5", "3_series", "5_series", "7_series"],
    "audi": ["a3", "a4", "q3", "q5", "q7"],
    "jeep": ["compass", "meridian", "wrangler", "fortuner"],  # compass/meridian
    "land_rover": ["defender", "discovery", "range_rover", "evoque"],
    "isuzu": ["v_cross", "d_max"],
}