import streamlit as st
import pandas as pd
import plotly.express as px
from FinMind.data import DataLoader
import datetime
import time

# 1. 網頁基本設定
st.set_page_config(page_title="台灣 50 熱力圖", layout="wide")
st.title("🏆 台灣 50 (0050) 成分股熱力圖")
st.caption("數據來源: FinMind (自動抓取 0050 成分股) | 更新機制: 每日收盤後")

# 初始化 DataLoader
dl = DataLoader()

# --- 核心函數 ---

@st.cache_data(ttl=86400)  # 快取 24 小時，因為成分股不常變
def get_0050_constituents():
    """
    抓取 0050 ETF 的最新成分股清單
    """
    # 抓取過去 60 天的持股資料 (確保能抓到最新的月報)
    end_date = datetime.date.today().strftime("%Y-%m-%d")
    start_date = (datetime.date.today() - datetime.timedelta(days=60)).strftime("%Y-%m-%d")
    
    try:
        df = dl.taiwan_stock_holding(
            stock_id='0050',
            start_date=start_date,
            end_date=end_date
        )
        
        if df.empty:
            return []

        # 取資料中最新的日期
        latest_date = df['date'].max()
        # 篩選出該日期的所有成分股
        latest_holdings = df[df['date'] == latest_date]
        
        # 回傳股票代號清單 (List)
        return latest_holdings['holding_id'].tolist()
    except Exception as e:
        st.error(f"抓取 0050 成分股失敗: {e}")
        return []

@st.cache_data(ttl=86400)
def get_stock_info_map():
    """
    抓取所有台股的基本資料 (用來查產業分類與名稱)
    """
    try:
        df = dl.taiwan_stock_info()
        # 轉換成字典方便查詢: code -> {name, sector}
        # 注意: FinMind 的產業欄位通常是 'industry_category'
        info_map = {}
        for index, row in df.iterrows():
            info_map[row['stock_id']] = {
                "name": row['stock_name'],
                "sector": row['industry_category']
            }
        return info_map
    except Exception as e:
        st.error(f"抓取個股基本資料失敗: {e}")
        return {}

@st.cache_data(ttl=3600) # 股價快取 1 小時
def fetch_market_data(stock_list, info_map):
    """
    批量抓取股價並計算漲跌
    """
    end_date = datetime.date.today().strftime("%Y-%m-%d")
    # 抓 7 天確保涵蓋假日
    start_date = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    all_data = []
    
    # 進度條
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_stocks = len(stock_list)

    for i, stock_id in enumerate(stock_list):
        # 取得名稱與產業 (如果查不到就顯示未知)
        stock_info = info_map.get(stock_id, {"name": stock_id, "sector": "其他"})
        status_text.text(f"正在分析: {stock_id} {stock_info['name']} ({i+1}/{total_stocks})")
        
        try:
            df_stock = dl.taiwan_stock_daily(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if not df_stock.empty:
                latest = df_stock.iloc[-1]
                
                # 計算數據
                current_price = latest['close']
                trading_volume = latest['Trading_Volume']
                turnover = current_price * trading_volume # 估算成交金額
                
                # 計算漲跌幅
                change_pct = 0.0
                if len(df_stock) >= 2:
                    prev_close = df_stock.iloc[-2]['close']
                    if prev_close > 0:
                        change_pct = ((current_price - prev_close) / prev_close) * 100
                elif 'spread' in latest:
                    prev_close = current_price - latest['spread']
                    if prev_close > 0:
                        change_pct = (latest['spread'] / prev_close) * 100

                all_data.append({
                    "Code": stock_id,
                    "Name": stock_info['name'],
                    "Sector": stock_info['sector'],
                    "Size": turnover,
                    "Price": current_price,
                    "ChangePct": round(change_pct, 2),
                    "LabelInfo": f"{stock_info['name']}<br>{current_price} ({round(change_pct, 2)}%)"
                })
        
        except Exception:
            pass # 略過錯誤的個股
            
        # 更新進度
        progress_bar.progress((i + 1) / total_stocks)

    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(all_data)

# --- 主程式邏輯 ---

# 1. 獲取 0050 成分股
with st.spinner('正在抓取台灣 50 最新成分股名單...'):
    top_50_codes = get_0050_constituents()

if not top_50_codes:
    st.error("無法獲取成分股清單，請稍後再試。")
    st.stop()

# 2. 獲取全台股基本資料 (名稱/產業)
info_map = get_stock_info_map()

# 3. 顯示資訊
st.info(f"✅ 已成功載入 {len(top_50_codes)} 檔成分股，正在獲取最新報價...")

# 4. 開始抓價量
if st.button("強制刷新報價"):
    st.cache_data.clear()

df = fetch_market_data(top_50_codes, info_map)

# 5. 繪圖
if not df.empty:
    # 處理產業名稱為空的情況
    df['Sector'] = df['Sector'].fillna('其他產業')
    
    fig = px.treemap(
        df,
        path=[px.Constant("台灣 50 成分股"), 'Sector', 'LabelInfo'],
        values='Size',
        color='ChangePct',
        color_continuous_scale=[
            [0.0, '#006400'], [0.4, '#90EE90'], 
            [0.5, '#D3D3D3'], 
            [0.6, '#F08080'], [1.0, '#8B0000']
        ],
        range_color=[-3, 3], # 顏色範圍鎖定在 +/- 3%
    )
    
    fig.update_traces(
        textinfo="label+value",
        hovertemplate='<b>%{label}</b><br>成交金額(估): %{value:,.0f}<br>漲跌幅: %{color:.2f}%'
    )
    
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=700)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 顯示數據表供參考
    with st.expander("查看詳細數據表"):
        st.dataframe(df[['Code', 'Name', 'Sector', 'Price', 'ChangePct', 'Size']].sort_values('Size', ascending=False))
else:
    st.warning("無法獲取報價資料，請檢查是否為休市時間或 API 異常。")