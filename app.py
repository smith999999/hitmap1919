import streamlit as st
import pandas as pd
import plotly.express as px
from FinMind.data import DataLoader
import datetime

# 1. 網頁設定
st.set_page_config(page_title="台灣股市熱力圖", layout="wide")
st.title("🇹🇼 台灣股市熱力圖 (FinMind 版)")
st.caption("數據來源: FinMind Open Data | 資料更新: 收盤後 (每日更新)")

# 2. 定義股票清單
STOCKS_MAP = {
    "2330": {"name": "台積電", "sector": "半導體"},
    "2317": {"name": "鴻海", "sector": "電子代工"},
    "2454": {"name": "聯發科", "sector": "半導體"},
    "2308": {"name": "台達電", "sector": "電子零組件"},
    "2881": {"name": "富邦金", "sector": "金融"},
    "2882": {"name": "國泰金", "sector": "金融"},
    "2412": {"name": "中華電", "sector": "通信網路"},
    "1301": {"name": "台塑", "sector": "塑膠"},
    "1303": {"name": "南亞", "sector": "塑膠"},
    "2603": {"name": "長榮", "sector": "航運"},
    "2303": {"name": "聯電", "sector": "半導體"},
    "3711": {"name": "日月光", "sector": "半導體"},
    "2886": {"name": "兆豐金", "sector": "金融"},
    "1216": {"name": "統一", "sector": "食品"},
    "2002": {"name": "中鋼", "sector": "鋼鐵"},
}

# 3. 抓取資料函數 (加上快取，TTL=3600秒，即1小時更新一次)
@st.cache_data(ttl=3600)
def fetch_stock_data():
    dl = DataLoader()
    end_date = datetime.date.today().strftime("%Y-%m-%d")
    # 抓取過去 7 天以確保涵蓋週末或連假
    start_date = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    all_data = []
    stock_ids = list(STOCKS_MAP.keys())
    
    # 顯示進度條 (只會在第一次抓取時顯示)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, stock_id in enumerate(stock_ids):
        info = STOCKS_MAP[stock_id]
        status_text.text(f"正在下載資料: {info['name']}...")
        
        try:
            df_stock = dl.taiwan_stock_daily(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if not df_stock.empty and len(df_stock) > 0:
                latest = df_stock.iloc[-1]
                
                # 計算成交金額 (估算)
                current_price = latest['close']
                turnover = current_price * latest['Trading_Volume']
                
                # 計算漲跌幅
                change_pct = 0.0
                if len(df_stock) >= 2:
                    prev_close = df_stock.iloc[-2]['close']
                    if prev_close > 0:
                        change_pct = ((current_price - prev_close) / prev_close) * 100
                elif 'spread' in latest:
                     # 備用方案：用價差反推
                     prev_close = current_price - latest['spread']
                     if prev_close > 0:
                        change_pct = (latest['spread'] / prev_close) * 100

                all_data.append({
                    "Code": stock_id,
                    "Name": info['name'],
                    "Sector": info['sector'],
                    "Size": turnover,
                    "Price": current_price,
                    "ChangePct": round(change_pct, 2),
                    "LabelInfo": f"{info['name']}<br>{current_price} ({round(change_pct, 2)}%)"
                })
        except Exception as e:
            print(f"Error fetching {stock_id}: {e}")
            
        progress_bar.progress((i + 1) / len(stock_ids))
        
    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(all_data)

# 4. 執行與繪圖
if st.button("強制刷新數據"):
    st.cache_data.clear()

try:
    df = fetch_stock_data()
    
    if not df.empty:
        fig = px.treemap(
            df,
            path=[px.Constant("台股市場"), 'Sector', 'LabelInfo'],
            values='Size',
            color='ChangePct',
            color_continuous_scale=[
                [0.0, '#006400'], [0.4, '#90EE90'], 
                [0.5, '#D3D3D3'], 
                [0.6, '#F08080'], [1.0, '#8B0000']
            ],
            range_color=[-3, 3],
        )
        
        fig.update_traces(
            textinfo="label+value",
            hovertemplate='<b>%{label}</b><br>估算成交額: %{value:,.0f}<br>漲跌幅: %{color:.2f}%'
        )
        
        fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        st.success(f"資料載入成功！共顯示 {len(df)} 檔股票。")
    else:
        st.warning("目前沒有獲取到資料，可能是非交易日或資料源暫時無回應。")
        
except Exception as e:
    st.error(f"系統發生錯誤: {e}")