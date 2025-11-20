import streamlit as st
import pandas as pd
import plotly.express as px
from FinMind.data import DataLoader
import datetime
import time

# 1. 網頁基本設定
st.set_page_config(page_title="台灣 50 熱力圖", layout="wide")
st.title("🏆 台灣 50 (0050) 成分股熱力圖 (產業優化版)")
st.caption("數據來源: FinMind Open Data | 成分股清單為靜態更新 | 電子股產業分類優化")

dl = DataLoader()

# --- 靜態清單 ---
STATIC_TOP_50_CODES = [
    '2330', '2317', '2454', '2303', '3711', '2882', '2881', '2891', '2886', '2884',
    '2002', '1301', '1303', '1216', '2412', '2603', '6505', '3008', '4904', '2357',
    '2382', '6415', '2395', '2327', '2615', '2912', '5871', '3037', '2379', '1101',
    '1102', '1402', '1590', '1722', '2345', '2347', '2408', '2474', '2498', '2606',
    '2609', '2707', '2801', '2823', '2834', '2892', '3010', '3041', '3576', '4938'
]

# --- 常用電子股手動定義產業類別 (用於優化 FinMind 分類不準確的部分) ---
# 這個映射會覆蓋 FinMind 抓到的分類，確保核心電子股正確顯示
ELECTRONIC_SECTOR_OVERRIDE = {
    '2330': '半導體-晶圓代工',
    '2454': '半導體-IC設計',
    '2317': '電子代工-組裝',
    '2303': '半導體-晶圓代工',
    '3711': '半導體-封測',
    '2308': '電子零組件', # 例如台達電
    '3008': '光學鏡頭', # 大立光
    '4904': '網通設備', # 遠傳 (雖然是電信，但通常會與電子一起看)
    '2357': '電腦及週邊設備', # 華碩
    '2382': '電腦及週邊設備', # 廣達
    '6415': '半導體-IC設計', # 矽力*-KY
    '2395': '電子零組件', # 研華
    '2327': '半導體-記憶體', # 群聯
    '2408': '被動元件', # 南亞科
    '2474': '半導體-記憶體', # 華邦電
    '2498': '網通設備', # 宏達電 (通常分在電子)
    '3037': '面板', # 欣興
    '4938': '電子代工-組裝', # 和碩
    '6505': '電子通路', # 台塑 (台塑集團的股票通常是綜合性，這裡先分類)
    # 更多電子股可以手動加入，確保分類精準
}


# --- 核心函數 (使用可靠的 FinMind API) ---

@st.cache_data(ttl=86400)
def get_stock_info_map():
    """
    抓取所有台股的基本資料 (用來查產業分類與名稱)
    """
    try:
        df = dl.taiwan_stock_info()
        df_info = df.set_index('stock_id')[['stock_name', 'industry_category']].rename(
            columns={'stock_name': 'Name', 'industry_category': 'Sector'}
        )
        # 對於 FinMind 抓不到或分類不準確的，我們在這裡進行手動優化
        for code, sector in ELECTRONIC_SECTOR_OVERRIDE.items():
            if code in df_info.index:
                df_info.loc[code, 'Sector'] = sector
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
                    "Sector": stock_info['Sector'] if pd.notna(stock_info['Sector']) else '其他', # 確保空值也處理
                    "Size": turnover,
                    "Price": current_price,
                    "ChangePct": round(change_pct, 2),
                    "LabelInfo": f"{stock_info['Name']}<br>{current_price} ({round(change_pct, 2)}%)"
                })
        
        except Exception:
            pass # 略過錯誤的個股
            
        progress_bar.progress((i + 1) / total_stocks)

    progress_bar.empty()
    status_text.empty()
    
    return pd.DataFrame(all_data)

# --- 主程式邏輯 ---

top_50_codes = STATIC_TOP_50_CODES
info_df = get_stock_info_map()

if info_df.empty:
    st.error("❌ 無法獲取股票基本資料，網站無法運作。")
    st.stop()
    
st.info(f"✅ 已載入 {len(top_50_codes)} 檔靜態成分股，正在獲取最新收盤報價...")

if st.button("強制刷新報價"):
    st.cache_data.clear()

df = fetch_market_data(top_50_codes, info_df)

if not df.empty:
    # 確保產業分類非空，並轉換為字串
    df['Sector'] = df['Sector'].fillna('未分類').astype(str)
    
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