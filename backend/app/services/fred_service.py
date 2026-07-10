import os
import json
import datetime
import requests
import random
from django.conf import settings

# Series mapping as defined in design_eco.md
INDICATORS = {
    "growth": {
        "GDP": {"series_id": "GDPC1", "note": "BEA"},
        "Retail_Sales": {"series_id": "RSAFS", "note": "Census Bureau"},
    },
    "employment": {
        "NFP": {"series_id": "PAYEMS", "note": "BLS"},
        "Initial_Jobless_Claims": {"series_id": "ICSA", "note": "DOL"},
        "Unemployment_Rate": {"series_id": "UNRATE", "note": "BLS"},
    },
    "inflation": {
        "CPI": {"series_id": "CPIAUCSL", "note": "BLS"},
        "Core_CPI": {"series_id": "CPILFESL", "note": "BLS"},
        "PPI": {"series_id": "PPIACO", "note": "BLS"},
        "Core_PCE": {"series_id": "PCEPILFE", "note": "BEA"},
    }
}

DATA_FILE_PATH = os.path.join(settings.BASE_DIR, 'data', 'macro_data.json')

def generate_mock_macro_data() -> dict:
    """Generates realistic mock macroeconomic data for fallback/development use."""
    today = datetime.date.today()
    
    # 24 monthly dates
    dates_monthly = []
    for i in range(24):
        d = today - datetime.timedelta(days=i * 30.5)
        first_day = datetime.date(d.year, d.month, 1)
        dates_monthly.append(first_day)
    dates_monthly.reverse()
    
    # 8 quarterly dates (GDP)
    dates_quarterly = [dates_monthly[i] for i in range(0, 24, 3)]
    
    # 24 weekly dates (Jobless Claims)
    dates_weekly = [today - datetime.timedelta(weeks=i) for i in range(24)]
    dates_weekly.reverse()
    
    # Helper to create observations list
    def make_obs(dates, start_val, growth_rate, noise_range):
        obs = []
        for idx, d in enumerate(dates):
            noise = random.uniform(-noise_range, noise_range)
            # trend over time
            val = start_val + (idx * growth_rate) + noise
            obs.append({
                "date": d.isoformat(),
                "value": round(val, 2)
            })
        return obs

    # Helper for Unemployment Rate which doesn't growth trend but fluctuates
    def make_rate_obs(dates, base_val, noise_range):
        obs = []
        prev = base_val
        for d in dates:
            change = random.uniform(-noise_range, noise_range)
            prev = max(3.4, min(6.0, prev + change))
            obs.append({
                "date": d.isoformat(),
                "value": round(prev, 1)
            })
        return obs

    result = {
        "growth": {
            "GDP": {
                "series_id": "GDPC1",
                "note": "BEA (Mock Data)",
                "observations": make_obs(dates_quarterly, 21200.0, 150.0, 40.0)
            },
            "Retail_Sales": {
                "series_id": "RSAFS",
                "note": "Census Bureau (Mock Data)",
                "observations": make_obs(dates_monthly, 675.0, 1.8, 5.0)
            }
        },
        "employment": {
            "NFP": {
                "series_id": "PAYEMS",
                "note": "BLS (Mock Data)",
                "observations": make_obs(dates_monthly, 156500.0, 160.0, 90.0)
            },
            "Initial_Jobless_Claims": {
                "series_id": "ICSA",
                "note": "DOL (Mock Data)",
                "observations": make_obs(dates_weekly, 215.0, 0.2, 12.0)
            },
            "Unemployment_Rate": {
                "series_id": "UNRATE",
                "note": "BLS (Mock Data)",
                "observations": make_rate_obs(dates_monthly, 3.8, 0.15)
            }
        },
        "inflation": {
            "CPI": {
                "series_id": "CPIAUCSL",
                "note": "BLS (Mock Data)",
                "observations": make_obs(dates_monthly, 310.0, 0.65, 0.4)
            },
            "Core_CPI": {
                "series_id": "CPILFESL",
                "note": "BLS (Mock Data)",
                "observations": make_obs(dates_monthly, 315.0, 0.70, 0.3)
            },
            "PPI": {
                "series_id": "PPIACO",
                "note": "BLS (Mock Data)",
                "observations": make_obs(dates_monthly, 235.0, 0.25, 0.8)
            },
            "Core_PCE": {
                "series_id": "PCEPILFE",
                "note": "BEA (Mock Data)",
                "observations": make_obs(dates_monthly, 121.0, 0.22, 0.15)
            }
        },
        "updated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "is_mock": True
    }
    return result

def fetch_fred_data() -> dict:
    """Fetches macroeconomic indicators from the FRED API or fallback mock data."""
    api_key = os.getenv("FRED_API_KEY")
    
    # Check if a valid API key is present
    if not api_key or api_key.strip() in ("", "<your_fred_api_key>", "dummy"):
        print("FRED_API_KEY is not configured or is a placeholder. Generating mock data...")
        result_data = generate_mock_macro_data()
    else:
        try:
            # Observations for the last 2 years
            start_date = (datetime.date.today() - datetime.timedelta(days=730)).isoformat()
            result_data = {}
            
            for category, metrics in INDICATORS.items():
                result_data[category] = {}
                for metric_name, info in metrics.items():
                    series_id = info["series_id"]
                    url = "https://api.stlouisfed.org/fred/series/observations"
                    params = {
                        "series_id": series_id,
                        "api_key": api_key,
                        "file_type": "json",
                        "observation_start": start_date,
                    }
                    
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    observations = []
                    for obs in data.get("observations", []):
                        val_str = obs.get("value", "")
                        # Filter out missing value strings like '.'
                        if val_str and val_str != ".":
                            try:
                                val = float(val_str)
                                observations.append({
                                    "date": obs.get("date"),
                                    "value": val
                                })
                            except ValueError:
                                pass
                    
                    # Store parsed observations (limit to recent 24 for chart/UI optimization)
                    result_data[category][metric_name] = {
                        "series_id": series_id,
                        "note": info["note"],
                        "observations": observations[-24:] if len(observations) > 24 else observations
                    }
            
            result_data["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result_data["is_mock"] = False
            
        except Exception as e:
            print(f"Error fetching FRED API: {e}. Falling back to mock data...")
            result_data = generate_mock_macro_data()
            
    return result_data

def fetch_and_save_macro_data() -> dict:
    """Legacy helper for backward compatibility that fetches and caches the FRED data."""
    result_data = fetch_fred_data()
    os.makedirs(os.path.dirname(DATA_FILE_PATH), exist_ok=True)
    with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    return result_data

