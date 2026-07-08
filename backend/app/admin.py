from django.contrib import admin
from .models import SubsidiaryMapping

@admin.register(SubsidiaryMapping)
class SubsidiaryMappingAdmin(admin.ModelAdmin):
    list_display = ('subsidiary_name', 'parent_company_name')
    search_fields = ('subsidiary_name', 'parent_company_name')
