version: '1.2'

system_architecture:
  backend: Django (Python)
  frontend: Next.js (React)
  data_source: FRED API, ISM 官方, ADP 官方

environment_variables:
  backend:
    - FRED_API_KEY=<your_fred_api_key>
  frontend:
    - NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api

data_modules:
  growth:
    GDP:
      fred_series_id: GDPC1
      note: BEA
    Retail_Sales:
      fred_series_id: RSAFS
      note: Census Bureau
    ISM_Manufacturing_PMI:
      source: ISM 官方
      note: 需串接 ISM 官方數據源或爬蟲
    ISM_Services_PMI:
      source: ISM 官方
      note: 需串接 ISM 官方數據源或爬蟲
  employment:
    NFP:
      fred_series_id: PAYEMS
      note: BLS
    Initial_Jobless_Claims:
      fred_series_id: ICSA
      note: DOL
    Unemployment_Rate:
      fred_series_id: UNRATE
      note: BLS
    ADP_Employment:
      source: ADP 官方
      note: 需串接 ADP 官方數據源或爬蟲
  inflation:
    CPI:
      fred_series_id: CPIAUCSL
      note: BLS
    Core_CPI:
      fred_series_id: CPILFESL
      note: BLS
    PPI:
      fred_series_id: PPIACO
      note: BLS
    Core_PCE:
      fred_series_id: PCEPILFE
      note: BEA

core_code_implementation:
  django_backend_api:
    filepath: views.py
    description: 整合 FRED 與其他官方來源 (ISM/ADP) 的更新 API
    code: |
      import os
      import json
      from django.http import JsonResponse
      from django.conf import settings
      from .services.fred_service import fetch_fred_data
      from .services.other_sources_service import fetch_ism_data, fetch_adp_data

      DATA_FILE_PATH = os.path.join(settings.BASE_DIR, 'data', 'macro_data.json')

      # API 1: 讀取既有快取
      def get_macro_data(request):
          if os.path.exists(DATA_FILE_PATH):
              with open(DATA_FILE_PATH, 'r') as f:
                  return JsonResponse(json.load(f))
          return JsonResponse({'message': '尚未有資料，請點擊更新'}, status=404)

      # API 2: 強制爬取最新資料並覆寫 JSON
      def update_macro_data(request):
          if request.method == 'POST':
              # 1. 抓取 FRED 數據
              fred_data = fetch_fred_data()
              
              # 2. 抓取 ISM 官方數據 (預留擴充)
              ism_data = fetch_ism_data()
              
              # 3. 抓取 ADP 官方數據 (預留擴充)
              adp_data = fetch_adp_data()
              
              # 合併資料
              combined_data = {
                  'growth': {**fred_data.get('growth', {}), **ism_data},
                  'employment': {**fred_data.get('employment', {}), **adp_data},
                  'inflation': fred_data.get('inflation', {})
              }
              
              # 儲存合併後的 JSON
              os.makedirs(os.path.dirname(DATA_FILE_PATH), exist_ok=True)
              with open(DATA_FILE_PATH, 'w') as f:
                  json.dump(combined_data, f)
                  
              return JsonResponse({'message': '更新成功', 'data': combined_data})

  nextjs_frontend_dashboard:
    filepath: components/MacroDashboard.tsx
    description: 帶有手動更新按鈕的前端元件
    code: |
      'use client';
      import { useState, useEffect } from 'react';

      export default function MacroDashboard() {
        const [data, setData] = useState(null);
        const [loading, setLoading] = useState(false);

        useEffect(() => {
          fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/get-macro-data/`)
            .then(res => res.json())
            .then(setData)
            .catch(console.error);
        }, []);

        const handleFetchNewData = async () => {
          setLoading(true);
          try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/update-macro-data/`, {
              method: 'POST',
            });
            const result = await res.json();
            if (result.data) {
              setData(result.data);
              alert('資料更新成功！');
            }
          } catch (error) {
            console.error(error);
          } finally {
            setLoading(false);
          }
        };

        return (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <h2>總體經濟數據看板</h2>
              <button onClick={handleFetchNewData} disabled={loading}>
                {loading ? '抓取中...' : '手動更新最新數據'}
              </button>
            </div>
            
            {data ? (
               <pre>{JSON.stringify(data, null, 2)}</pre> 
            ) : (
               <p>無快取資料，請點擊上方按鈕獲取。</p>
            )}
          </div>
        );
      }