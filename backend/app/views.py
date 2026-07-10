import os
import json
import threading
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

from .pipeline import get_latest_state, run_analysis
from .models import AnalysisLog, Company
from .config import (
    DEFAULT_LOOKBACK_DAYS,
    RECENT_POLICIES_LIMIT,
    TOP_COMPANIES_LIMIT,
    TOP_INDUSTRIES_LIMIT,
)

ANALYSIS_LOCK = threading.Lock()
ANALYSIS_JOB = {
    "status": "idle",
    "started_at": None,
    "finished_at": None,
    "error": None,
}


def _analysis_worker(lookback_days: int, offline: bool) -> None:
    try:
        run_analysis(lookback_days=lookback_days, offline=offline)
        with ANALYSIS_LOCK:
            state = get_latest_state()
            ANALYSIS_JOB.update({
                "status": "completed",
                "finished_at": time.time(),
                "error": None,
                "summary": {
                    "policies": len(state.get("policies", [])),
                    "industries": len(state.get("industries", [])),
                    "companies": len(state.get("companies", [])),
                },
            })
    except Exception as exc:
        with ANALYSIS_LOCK:
            ANALYSIS_JOB.update({
                "status": "failed",
                "finished_at": time.time(),
                "error": str(exc),
            })


def health_view(request):
    state = get_latest_state()
    return JsonResponse({
        "status": "ok",
        "updated_at": state.get("updated_at"),
        "lookback_days": DEFAULT_LOOKBACK_DAYS,
        "root_dir": str(settings.ROOT_DIR),
    })


def dashboard_view(request):
    state = get_latest_state()
    return JsonResponse({
        "updated_at": state.get("updated_at"),
        "lookback_days": DEFAULT_LOOKBACK_DAYS,
        "summary": {
            "policies": len(state.get("policies", [])),
            "industries": len(state.get("industries", [])),
            "companies": len(state.get("companies", [])),
        },
        "top_industries": state.get("industries", [])[:TOP_INDUSTRIES_LIMIT],
        "top_companies": state.get("companies", [])[:TOP_COMPANIES_LIMIT],
        "recent_policies": state.get("policies", [])[:RECENT_POLICIES_LIMIT],
    })


def policies_view(request):
    state = get_latest_state()
    return JsonResponse({"results": state.get("policies", [])})


def industries_ranking_view(request):
    state = get_latest_state()
    return JsonResponse({"results": state.get("industries", [])})


def companies_ranking_view(request):
    state = get_latest_state()
    return JsonResponse({"results": state.get("companies", [])})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def run_analysis_view(request):
    lookback = request.GET.get("lookback_days") or request.POST.get("lookback_days")
    if not lookback:
        lookback = DEFAULT_LOOKBACK_DAYS
    else:
        try:
            lookback = int(lookback)
        except ValueError:
            lookback = DEFAULT_LOOKBACK_DAYS

    offline = request.GET.get("offline") or request.POST.get("offline")
    if offline is None:
        offline = False
    else:
        offline = str(offline).lower() == "true"

    with ANALYSIS_LOCK:
        if ANALYSIS_JOB.get("status") == "running":
            return JsonResponse(dict(ANALYSIS_JOB), status=202)

        ANALYSIS_JOB.clear()
        ANALYSIS_JOB.update({
            "status": "running",
            "started_at": time.time(),
            "finished_at": None,
            "error": None,
            "lookback_days": lookback,
            "offline": offline,
        })

    thread = threading.Thread(
        target=_analysis_worker,
        args=(lookback, offline),
        daemon=True,
    )
    thread.start()
    return JsonResponse(dict(ANALYSIS_JOB), status=202)


def analysis_status_view(request):
    with ANALYSIS_LOCK:
        return JsonResponse(dict(ANALYSIS_JOB))


def stockcomps_view(request):
    latest_analysis = AnalysisLog.objects.order_by('-ana_id').first()
    if not latest_analysis:
        return JsonResponse([], safe=False)
    
    companies = Company.objects.filter(analysis=latest_analysis)
    
    data = []
    for c in companies:
        data.append({
            "ticker": c.ticker,
            "name": c.name,
            "exchange": c.exchange,
            "industry_code": c.industry_code,
            "industry_name": c.industry_name,
            "sector": c.sector,
        })
    return JsonResponse(data, safe=False)


DATA_FILE_PATH = os.path.join(settings.BASE_DIR, 'data', 'macro_data.json')

# API 1: 網頁載入時呼叫，自資料庫讀取指標數據
def get_macro_data(request):
    from .models import MacroObservation
    
    # 查詢所有數據，按日期升序排列以維持時間序列順序
    obs_list = MacroObservation.objects.all().order_by('date')
    
    if not obs_list.exists():
        return JsonResponse({'message': '尚未有資料，請點擊更新'}, status=404)
        
    combined_data = {
        'growth': {},
        'employment': {},
        'inflation': {}
    }
    
    max_fetched_at = ""
    is_mock = False
    
    for obs in obs_list:
        category = obs.category
        metric_name = obs.metric_name
        
        # 確保分類存在
        if category not in combined_data:
            combined_data[category] = {}
            
        # 確保指標字典存在
        if metric_name not in combined_data[category]:
            combined_data[category][metric_name] = {
                'series_id': obs.series_id,
                'note': obs.source,
                'source': obs.source,
                'observations': []
            }
            
        # 加入觀測點數據
        combined_data[category][metric_name]['observations'].append({
            'date': obs.date,
            'value': obs.value
        })
        
        # 追蹤最新更新時間 (String 比較)
        if obs.fetched_at > max_fetched_at:
            max_fetched_at = obs.fetched_at
            
        # 偵測是否使用模擬數據 (排除始終為模擬的 ISM 指標)
        if 'Mock' in obs.source and obs.metric_name not in ('ISM_Manufacturing_PMI', 'ISM_Services_PMI'):
            is_mock = True
            
    combined_data['updated_at'] = max_fetched_at
    combined_data['is_mock'] = is_mock
    
    return JsonResponse(combined_data)


# API 2: 按鈕點擊時呼叫，強制爬取最新資料並覆寫 JSON
@csrf_exempt
def update_macro_data(request):
    if request.method == 'POST':
        import datetime
        from .services.fred_service import fetch_fred_data
        from .services.other_sources_service import fetch_ism_data, fetch_adp_data
        
        # 1. Fetch FRED data
        fred_data = fetch_fred_data()
        
        # 2. Fetch ISM data
        ism_data = fetch_ism_data()
        
        # 3. Fetch ADP data
        adp_data = fetch_adp_data()
        
        # Combine indicators
        combined_data = {
            'growth': {**fred_data.get('growth', {}), **ism_data},
            'employment': {**fred_data.get('employment', {}), **adp_data},
            'inflation': fred_data.get('inflation', {}),
            'updated_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'is_mock': fred_data.get('is_mock', True)
        }
        
        # Save cache
        os.makedirs(os.path.dirname(DATA_FILE_PATH), exist_ok=True)
        with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=2)
            
        # Sync to stockai.db database
        try:
            save_macro_data_to_db(combined_data)
        except Exception as e:
            print(f"Error syncing macro observations to database: {e}")
            
        return JsonResponse({'message': '更新成功', 'data': combined_data})
    return JsonResponse({'message': 'Method not allowed'}, status=405)


def save_macro_data_to_db(combined_data):
    from .models import MacroObservation
    import datetime
    from zoneinfo import ZoneInfo
    taipei_now = datetime.datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d %H:%M:%S")
    
    for category, metrics in combined_data.items():
        if category in ('updated_at', 'is_mock'):
            continue
        for metric_name, info in metrics.items():
            series_id = info.get('series_id')
            source = info.get('source') or info.get('note') or 'FRED'
            observations = info.get('observations', [])
            for obs in observations:
                MacroObservation.objects.update_or_create(
                    series_id=series_id,
                    date=obs['date'],
                    defaults={
                        'category': category,
                        'metric_name': metric_name,
                        'source': source,
                        'value': obs['value'],
                        'fetched_at': taipei_now
                    }
                )





