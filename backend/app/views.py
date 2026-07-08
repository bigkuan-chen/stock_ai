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

