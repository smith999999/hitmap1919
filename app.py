import streamlit as st
import pandas as pd
import plotly.express as px
from FinMind.data import DataLoader
import datetime
import time

# 1. 網頁基本設定
st.set_page_config(page_title="台灣 50 熱力圖", layout="wide")
st.title("🏆 台灣 50 (0050) 成分股熱力圖")
st.caption("數據來源: FinMind Open Data (最新版本函數) | 更新機制: 每日收盤後")

dl = DataLoader()

# --- 核心函數 ---

@st.cache_data(ttl=86400) # 快取 24 小時
def get_0050_constituents_and_info():
    """
    1. 抓取所有個股的基本資訊 (包含名稱與產業)
    2. 抓取 0050 的最新成分股清單
    3. 合併資料，篩選出 0050 的代號清單
    """
    try:
        # 1. 抓取全台股基本資料 (包含名稱/產業)
        df_info = dl.taiwan_stock_info()
        df_info = df_info.set_index('stock_id')[['stock_name', 'industry_category']].rename(
            columns={'stock_name': 'Name', 'industry_category': 'Sector'}
        )
        
        # 2. 抓取 0050 ETF 的最新成分股清單 (使用新函數名稱)
        # FinMind 可能需要較新的版本才能使用這個函數
        df_holding = dl.taiwan_stock_etf_holding(stock_id='0050')
        
        if df_holding.empty:
            st.warning("⚠️ 警告：無法從 FinMind 獲取 ETF 成分股清單。")
            return []

        # 篩選出最新的成分股清單
        latest_date = df_holding['date'].max()
        df_latest_holding = df_holding[df_holding['date'] == latest_date]
        
        # 3. 合併資料
        constituents_codes = df_latest_holding['HoldingStockId'].tolist()
        
        # 這裡返回 (代號清單, 資訊 DataFrame)
        return constituents_codes, df_info
        
    except AttributeError as e:
        # 如果還是舊版，可能會在這裡報錯，改用 fallback
        st.error(f"FinMind API 呼叫失敗，請確認 Streamlit Cloud 的 FinMind 版本是否夠新。錯誤: {e}")
        return [], pd.DataFrame() # 返回空資料
    except Exception as e:
        st.error(f"抓取 0050 成分股時發生錯誤: {e}")
        return [], pd.DataFrame()


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
                    "Sector": stock_info['Sector'] if pd.notna(stock_info['Sector']) else '其他',
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

# 1. 獲取成分股與基本資料
with st.spinner('正在抓取台灣 50 最新成分股名單與產業資訊...'):
    top_50_codes, info_df = get_0050_constituents_and_info()

if not top_50_codes:
    st.error("❌ 無法獲取成分股清單。網站無法運作。")
    st.stop()

# 2. 顯示資訊
st.info(f"✅ 已成功載入 {len(top_50_codes)} 檔成分股，正在獲取最新收盤報價...")

# 3. 開始抓價量
if st.button("強制刷新報價"):
    st.cache_data.clear()

df = fetch_market_data(top_50_codes, info_df)

# 4. 繪圖
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