'use client';
import { useState, useEffect } from 'react';

export default function MacroDashboard() {
  const [data, setData] = useState<any>(null);
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
