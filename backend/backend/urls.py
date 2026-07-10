from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from app import views

urlpatterns = [
    path('stock_ai_admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('macro.html', TemplateView.as_view(template_name='macro.html'), name='macro'),
    path('api/health', views.health_view, name='health'),
    path('api/dashboard', views.dashboard_view, name='dashboard'),
    path('api/policies', views.policies_view, name='policies'),
    path('api/industries/ranking', views.industries_ranking_view, name='industries_ranking'),
    path('api/companies/ranking', views.companies_ranking_view, name='companies_ranking'),
    path('api/run-analysis', views.run_analysis_view, name='run-analysis'),
    path('api/analysis-status', views.analysis_status_view, name='analysis-status'),
    path('api/stockcomps', views.stockcomps_view, name='stockcomps'),
    path('api/get-macro-data/', views.get_macro_data, name='get_macro_data'),
    path('api/update-macro-data/', views.update_macro_data, name='update_macro_data'),
]

if settings.DEBUG:
    urlpatterns += static('/', document_root=settings.FRONTEND_DIR)
