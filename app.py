import streamlit as st
import pandas as pd
import plotly.express as px
from FinMind.data import DataLoader
import datetime
import time

# 1. 網頁基本設定
st.set_page_config(page_title="台灣 50 熱力圖", layout="wide")
st.title("🏆 台灣 50 (0050) 成分股熱力圖 (穩定版)")
st.caption("數據來源: FinMind Open Data | 成分股清單為靜態更新")

dl = DataLoader()

# --- 靜態清單 ---
# 這是目前 0050 ETF 的靜態成分股代號清單，用來繞過 API 錯誤
STATIC_TOP_50_CODES = [
    '2330', '2317', '2454', '2303', '3711', '2882', '2881', '2891', '2886', '2884', 
    '2002', '1301', '1303', '1216', '2412', '2603', '6505', '3008', '4904', '2357', 
    '2382', '6415', '2395', '2327', '2615', '2912', '5871', '3037', '2379', '1101', 
    '1102', '1402', '1590', '1722', '2345', '2347', '2408', '2474', '2498', '2606', 
    '2609', '2707', '2801', '2823', '2834', '2892', '3010', '3041', '3576', '4938'
]


# --- 核心函數 (使用可靠的 FinMind API) ---

@st.cache_data(ttl=86400) 
def get_stock_info_map():
    """
    抓取所有台股的基本資料 (用來查產業分類與名稱)
    """
    try:
        # 這個 API 函數 (taiwan_stock_info) 穩定且不會出錯
        df = dl.taiwan_stock_info()
        df_info = df.set_index('stock_id')[['stock_name', 'industry_category']].rename(
            columns={'stock_name': 'Name', 'industry_category': 'Sector'}
        )
        return df_info
    except Exception as e:
        st.error(f"抓取個股基本資料失敗: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600) # 股價快取 1 小時
def fetch_market_data(stock_list, info_df):
    """
    批量抓取股價並計算漲跌
    """
    end_date = datetime.date.today().strftime("%Y-%m-%d")
    start_date = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    all_data = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_stocks = len(stock_list)

    for i, stock_id in enumerate(stock_list):
        stock_info = info_df.loc[stock_id] if stock_id in info_df.index else {"Name": stock_id, "Sector": "其他"}
        status_text.text(f"正在分析: {stock_id} {stock_info['Name']} ({i+1}/{total_stocks})")
        
        try:
            # 這個 API 函數 (taiwan_stock_daily) 也非常可靠
            df_stock = dl.taiwan_stock_daily(
                stock_id=stock_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if not df_stock.empty:
                latest = df_stock.iloc[-1]
                current_price = latest['close']
                trading_volume = latest['Trading_Volume']
                turnover = current_price * trading_volume
                
                change_pct = 0.0
                if len(df_stock) >= 2:
                    prev_close = df_stock.iloc[-2]['close']
                    if prev_close > 0:
                        change_pct = ((current_price - prev_close) / prev_close) * 100
                
                all_data.append({
                    "Code": stock_id,
                    "Name": stock_info['Name'],
                    "Sector": stock_info['Sector'] if pd.notna(stock_info['Sector']) else '其他',
                    "Size": turnover,
                    "Price": current_price,
                    "ChangePct": round(change_pct, 2),
                    "LabelInfo": f"{stock_info['Name']}<br>{current_price} ({round(change_pct, 2)}%)"
                })
        
        except Exception:
            pass
            
        progress_bar.progress((i + 1) / total_stocks)

    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(all_data)

# --- 主程式邏輯 ---

# 1. 獲取成分股與基本資料
top_50_codes = STATIC_TOP_50_CODES
info_df = get_stock_info_map()

if info_df.empty:
    st.error("❌ 無法獲取股票基本資料，網站無法運作。")
    st.stop()
    
st.info(f"✅ 已載入 {len(top_50_codes)} 檔靜態成分股，正在獲取最新收盤報價...")

# 2. 開始抓價量
if st.button("強制刷新報價"):
    st.cache_data.clear()

df = fetch_market_data(top_50_codes, info_df)

# 3. 繪圖
if not df.empty:
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
        range_color=[-3, 3],
    )
    
    fig.update_traces(
        textinfo="label+value",
        hovertemplate='<b>%{label}</b><br>成交金額(估): %{value:,.0f}<br>漲跌幅: %{color:.2f}%'
    )
    
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=700)
    
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("查看詳細數據表"):
        st.dataframe(df[['Code', 'Name', 'Sector', 'Price', 'ChangePct', 'Size']].sort_values('Size', ascending=False))
else:
    st.warning("⚠️ 警告：無法獲取報價資料，請檢查是否為休市時間或 FinMind API 異常。")