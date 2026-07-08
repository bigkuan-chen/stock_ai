from __future__ import annotations


INDUSTRIES = [
    {
        "code": "defense_aerospace_military",
        "name": "國防 / 航太 / 軍工",
        "keywords": [
            "defense", "aerospace", "military", "national security", "procurement",
            "missile", "shipbuilding", "drone", "space", "weapon", "arms", "ammunition",
            "tactical", "Department of Defense", "Pentagon",
        ],
    },
    {
        "code": "ai_datacenter_power",
        "name": "AI / 資料中心 / 電力基建",
        "keywords": [
            "artificial intelligence", "AI", "cybersecurity", "cloud", "data center",
            "compute", "software", "critical infrastructure", "privacy", "gpu", "server",
            "grid", "transmission", "electricity", "generator", "power infrastructure",
            "substation", "utility", "transformer",
        ],
    },
    {
        "code": "semiconductors",
        "name": "半導體",
        "keywords": [
            "semiconductor", "chip", "microelectronics", "foundry", "fab",
            "lithography", "ASML", "wafer", "packaging", "integrated circuit",
            "CHIPS Act", "advanced manufacturing", "export control",
        ],
    },
    {
        "code": "critical_minerals_rare_earth",
        "name": "關鍵礦物 / 稀土 / 金屬材料",
        "keywords": [
            "critical mineral", "rare earth", "lithium", "cobalt", "nickel",
            "graphite", "manganese", "copper", "metal", "mining", "refining",
            "raw materials", "processing", "extraction", "aluminum", "steel",
        ],
    },
    {
        "code": "nuclear_uranium_smr",
        "name": "核能 / 鈾 / SMR",
        "keywords": [
            "nuclear", "uranium", "SMR", "small modular reactor", "fission",
            "reactor", "nuclear fuel", "enrichment", "atomic", "radioactive", "fusion",
        ],
    },
    {
        "code": "traditional_energy_lng_oil",
        "name": "傳統能源 / LNG / 媒 / 油服",
        "keywords": [
            "oil", "gas", "LNG", "liquefied natural gas", "coal", "drilling",
            "refinery", "fracking", "fossil fuel", "petroleum", "pipeline",
            "oilfield services", "offshore drilling",
        ],
    },
    {
        "code": "ev_battery_charging",
        "name": "EV / 電池 / 充電",
        "keywords": [
            "EV", "electric vehicle", "battery cell", "battery pack", "charging station",
            "charger", "electrification", "anode", "cathode", "gigafactory",
        ],
    },
    {
        "code": "pharma_reshoring",
        "name": "製藥 / 製造回流",
        "keywords": [
            "pharmaceutical", "drug", "biotech", "manufacturing reshoring", "onshoring",
            "reshoring", "domestic production", "supply chain resilience", "factory",
            "facility", "medicine", "active pharmaceutical ingredient", "API",
            "health", "FDA", "medical device", "vaccine", "public health",
        ],
    },
]


POSITIVE_POLICY_TERMS = [
    "funding", "grant", "investment", "procurement", "tax credit", "subsidy",
    "domestic production", "accelerate", "permit", "modernize", "award",
]

RISK_POLICY_TERMS = [
    "ban", "restriction", "penalty", "investigation", "enforcement",
    "tariff", "export control", "compliance", "sanction",
]
