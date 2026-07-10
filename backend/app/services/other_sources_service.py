import os
import datetime
import requests
import random

def generate_mock_ism_data() -> dict:
    """Generates realistic mock ISM Manufacturing & Services PMI data."""
    today = datetime.date.today()
    dates_monthly = []
    for i in range(24):
        d = today - datetime.timedelta(days=i * 30.5)
        first_day = datetime.date(d.year, d.month, 1)
        dates_monthly.append(first_day)
    dates_monthly.reverse()
    
    def make_pmi_obs(dates, base_val):
        obs = []
        prev = base_val
        for d in dates:
            change = random.uniform(-1.2, 1.2)
            prev = max(42.0, min(59.0, prev + change))
            obs.append({
                "date": d.isoformat(),
                "value": round(prev, 1)
            })
        return obs

    return {
        "ISM_Manufacturing_PMI": {
            "source": "ISM 官方 (Mock Data)",
            "series_id": "NAPM",
            "note": "ISM Manufacturing PMI",
            "observations": make_pmi_obs(dates_monthly, 48.5)
        },
        "ISM_Services_PMI": {
            "source": "ISM 官方 (Mock Data)",
            "series_id": "NMI",
            "note": "ISM Services PMI",
            "observations": make_pmi_obs(dates_monthly, 51.2)
        }
    }

def generate_mock_adp_data() -> dict:
    """Generates realistic mock ADP Private Employment data."""
    today = datetime.date.today()
    dates_monthly = []
    for i in range(24):
        d = today - datetime.timedelta(days=i * 30.5)
        first_day = datetime.date(d.year, d.month, 1)
        dates_monthly.append(first_day)
    dates_monthly.reverse()
    
    obs = []
    for idx, d in enumerate(dates_monthly):
        # Trend matching non-farm payrolls but slightly lower level (private only)
        noise = random.uniform(-90.0, 90.0)
        val = 128000.0 + (idx * 150.0) + noise
        obs.append({
            "date": d.isoformat(),
            "value": round(val, 2)
        })

    return {
        "ADP_Employment": {
            "source": "ADP 官方 (Mock Data)",
            "series_id": "ADPMNUS",
            "note": "ADP Nonfarm Private Employment (Thousands)",
            "observations": obs
        }
    }

def fetch_ism_data() -> dict:
    """Fetches ISM PMIs from FRED API under the hood or fallbacks to mock data."""
    api_key = os.getenv("FRED_API_KEY")
    
    if not api_key or api_key.strip() in ("", "<your_fred_api_key>", "dummy"):
        return generate_mock_ism_data()
        
    try:
        start_date = (datetime.date.today() - datetime.timedelta(days=730)).isoformat()
        result = {}
        
        indicators = {
            "ISM_Manufacturing_PMI": {"series_id": "NAPM", "note": "ISM Manufacturing PMI"},
            "ISM_Services_PMI": {"series_id": "NMI", "note": "ISM Services PMI"}
        }
        
        for name, info in indicators.items():
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
                if val_str and val_str != ".":
                    try:
                        val = float(val_str)
                        observations.append({
                            "date": obs.get("date"),
                            "value": val
                        })
                    except ValueError:
                        pass
                        
            result[name] = {
                "source": "ISM 官方",
                "series_id": series_id,
                "note": info["note"],
                "observations": observations[-24:] if len(observations) > 24 else observations
            }
            
        return result
        
    except Exception as e:
        print(f"Error fetching ISM data: {e}. Falling back to mock data...")
        return generate_mock_ism_data()

def fetch_adp_data() -> dict:
    """Fetches ADP Private Employment from FRED API under the hood or fallbacks to mock data."""
    api_key = os.getenv("FRED_API_KEY")
    
    if not api_key or api_key.strip() in ("", "<your_fred_api_key>", "dummy"):
        return generate_mock_adp_data()
        
    try:
        start_date = (datetime.date.today() - datetime.timedelta(days=730)).isoformat()
        result = {}
        
        series_id = "ADPMNUSNERSA" # ADP Private Nonfarm Employment (ADPMNUSNERSA)
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
            if val_str and val_str != ".":
                try:
                    val = float(val_str)
                    observations.append({
                        "date": obs.get("date"),
                        "value": val
                    })
                except ValueError:
                    pass
                    
        result["ADP_Employment"] = {
            "source": "ADP 官方",
            "series_id": series_id,
            "note": "ADP Nonfarm Private Employment (Thousands)",
            "observations": observations[-24:] if len(observations) > 24 else observations
        }
        
        return result
        
    except Exception as e:
        print(f"Error fetching ADP data: {e}. Falling back to mock data...")
        return generate_mock_adp_data()
