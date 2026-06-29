from __future__ import annotations


INDUSTRIES = [
    {
        "code": "semiconductors",
        "name": "半導體與先進製造",
        "keywords": [
            "semiconductor", "chip", "microelectronics", "advanced manufacturing",
            "CHIPS", "foundry", "supply chain", "export control",
        ],
    },
    {
        "code": "clean_energy",
        "name": "潔淨能源與電網",
        "keywords": [
            "clean energy", "renewable", "solar", "wind", "battery", "grid",
            "transmission", "hydrogen", "carbon", "emissions", "energy storage",
        ],
    },
    {
        "code": "defense_aerospace",
        "name": "國防航太",
        "keywords": [
            "defense", "aerospace", "missile", "shipbuilding", "drone", "space",
            "national security", "procurement", "Department of Defense",
        ],
    },
    {
        "code": "ai_cloud",
        "name": "AI、雲端與資安",
        "keywords": [
            "artificial intelligence", "AI", "cybersecurity", "cloud", "data center",
            "compute", "software", "critical infrastructure", "privacy",
        ],
    },
    {
        "code": "healthcare_biotech",
        "name": "醫療生技",
        "keywords": [
            "health", "drug", "biotech", "pharmaceutical", "Medicare", "FDA",
            "medical device", "vaccine", "public health",
        ],
    },
    {
        "code": "infrastructure",
        "name": "基礎建設與工程",
        "keywords": [
            "infrastructure", "bridge", "rail", "highway", "construction",
            "permitting", "water", "broadband", "transportation",
        ],
    },
]


COMPANIES = [
    {
        "ticker": "NVDA",
        "name": "NVIDIA",
        "exchange": "NASDAQ",
        "industry_code": "ai_cloud",
        "keywords": ["AI", "compute", "data center", "semiconductor", "chip"],
        "risk": 8,
    },
    {
        "ticker": "MSFT",
        "name": "Microsoft",
        "exchange": "NASDAQ",
        "industry_code": "ai_cloud",
        "keywords": ["cloud", "cybersecurity", "AI", "software"],
        "risk": 6,
    },
    {
        "ticker": "TSM",
        "name": "Taiwan Semiconductor Manufacturing",
        "exchange": "NYSE",
        "industry_code": "semiconductors",
        "keywords": ["semiconductor", "foundry", "chip", "advanced manufacturing"],
        "risk": 10,
    },
    {
        "ticker": "INTC",
        "name": "Intel",
        "exchange": "NASDAQ",
        "industry_code": "semiconductors",
        "keywords": ["CHIPS", "semiconductor", "foundry", "manufacturing"],
        "risk": 12,
    },
    {
        "ticker": "FSLR",
        "name": "First Solar",
        "exchange": "NASDAQ",
        "industry_code": "clean_energy",
        "keywords": ["solar", "clean energy", "domestic production"],
        "risk": 9,
    },
    {
        "ticker": "NEE",
        "name": "NextEra Energy",
        "exchange": "NYSE",
        "industry_code": "clean_energy",
        "keywords": ["renewable", "wind", "solar", "grid", "energy storage"],
        "risk": 8,
    },
    {
        "ticker": "LMT",
        "name": "Lockheed Martin",
        "exchange": "NYSE",
        "industry_code": "defense_aerospace",
        "keywords": ["defense", "missile", "aerospace", "procurement"],
        "risk": 7,
    },
    {
        "ticker": "RTX",
        "name": "RTX",
        "exchange": "NYSE",
        "industry_code": "defense_aerospace",
        "keywords": ["defense", "aerospace", "missile", "supply chain"],
        "risk": 7,
    },
    {
        "ticker": "LLY",
        "name": "Eli Lilly",
        "exchange": "NYSE",
        "industry_code": "healthcare_biotech",
        "keywords": ["drug", "pharmaceutical", "FDA", "Medicare"],
        "risk": 10,
    },
    {
        "ticker": "CAT",
        "name": "Caterpillar",
        "exchange": "NYSE",
        "industry_code": "infrastructure",
        "keywords": ["construction", "infrastructure", "mining", "equipment"],
        "risk": 9,
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
