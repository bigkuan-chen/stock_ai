version: '1.1'

system_architecture:
  backend: Django (Python)
  frontend: Next.js (React)
  data_source: FRED API

environment_variables:
  backend:
    - FRED_API_KEY=<your_fred_api_key>
  frontend:
    - NEXT_PUBLIC_API_BASE_URL=http://localhost:8080/api

data_modules:
  growth:
    GDP:
      fred_series_id: GDPC1
      note: BEA
    Retail_Sales:
      fred_series_id: RSAFS
      note: Census Bureau
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
    description: 提供「讀取舊檔快取」與「手動觸發更新」兩支 API
    code: |
      import os
      import json
      from django.http import JsonResponse
      from django.conf import settings
      from .services.fred_service import fetch_and_save_macro_data # 負責實際打 FRED API 的函式

      DATA_FILE_PATH = os.path.join(settings.BASE_DIR, 'data', 'macro_data.json')

      # API 1: 網頁載入時呼叫，只讀取既有 JSON，不消耗 API 額度
      def get_macro_data(request):
          if os.path.exists(DATA_FILE_PATH):
              with open(DATA_FILE_PATH, 'r') as f:
                  return JsonResponse(json.load(f))
          return JsonResponse({'message': '尚未有資料，請點擊更新'}, status=404)

      # API 2: 按鈕點擊時呼叫，強制爬取最新資料並覆寫 JSON
      def update_macro_data(request):
          if request.method == 'POST':
              new_data = fetch_and_save_macro_data()
              return JsonResponse({'message': '更新成功', 'data': new_data})

  nextjs_frontend_dashboard:
    filepath: components/MacroDashboard.tsx
    description: 帶有手動更新按鈕，控制資料抓取頻率的前端元件
    code: |
      'use client';
      import { useState, useEffect } from 'react';

      export default function MacroDashboard() {
        const [data, setData] = useState(null);
        const [loading, setLoading] = useState(false);

        // 1. 初次渲染：自動撈取舊資料快取 (不觸發爬蟲)
        useEffect(() => {
          fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/get-macro-data/`)
            .then(res => res.json())
            .then(setData)
            .catch(console.error);
        }, []);

        // 2. 按鈕事件：呼叫更新 API (觸發爬蟲)
        const handleFetchNewData = async () => {
          setLoading(true);
          try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/update-macro-data/`, {
              method: 'POST',
            });
            const result = await res.json();
            if (result.data) {
              setData(result.data); // 更新畫面顯示
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
            
            {/* 判斷並渲染資料 */}
            {data ? (
               <pre>{JSON.stringify(data, null, 2)}</pre> 
            ) : (
               <p>無快取資料，請點擊上方按鈕獲取。</p>
            )}
          </div>
        );
      }