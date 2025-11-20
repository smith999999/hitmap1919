import streamlit as st
import pandas as pd
import plotly.express as px
from FinMind.data import DataLoader
import datetime
import time

# 1. 網頁基本設定
st.set_page_config(page_title="台灣 50 熱力圖", layout="wide")
st.title("🏆 台灣 50 (0050) 成分股熱力圖 (快取備援版)")
# 確保標題修正，避免誤導
st.caption("數據來源: FinMind Open Data | 失敗時將自動顯示上次成功抓取的資料。")

dl = DataLoader() 

# --- 核心數據結構 (保持不變) ---

# 1. 實際發行股數 (Issued Shares, 單位: 百萬股/仟張)
ISSUED_SHARES_MAP = {
    '2330': 25930, '2317': 13863, '2454': 1598, '2303': 12964, '3711': 4349, '2881': 14920,
    '2882': 13627, '2886': 13735, '2002': 15734, '1301': 9534, '1303': 7943, '2412': 9718,
    '2603': 2147, '6505': 10476, '3008': 131, '4904': 3450, '2357': 743, '2382': 2584,
    '6415': 635, '2395': 677, '2327': 2471, '2615': 4200, '5871': 1845, '3037': 982,
    '2379': 930, '1101': 7458, '1102': 7847, '1402': 4799, '1590': 790, '1722': 5163,
    '2345': 1650, '2347': 2474, '2408': 7421, '2474': 8125, '2498': 1673, '2606': 3740,
    '2609': 4216, '2707': 105, '2801': 9625, '2823': 12220, '2834': 9831, '2892': 13243,
    '3010': 354, '3041': 1488, '3576': 1184, '4938': 1657, '1216': 5373, '2308': 2614,
    '2891': 19576, '2603': 2147, '2812': 6703, '8454': 142,
}

# 2. 完整產業分類清單 (保持不變)
STOCK_CLASSIFICATION = {
    '2330': {'Name': '台積電', 'Sector': '電子: 晶圓代工'}, '2454': {'Name': '聯發科', 'Sector': '電子: IC 設計'},
    '2303': {'Name': '聯電', 'Sector': '電子: 晶圓代工'}, '3711': {'Name': '日月光投控', 'Sector': '電子: 封裝測試'},
    '6415': {'Name': '矽力*-KY', 'Sector': '電子: IC 設計'}, '2327': {'Name': '群聯', 'Sector': '電子: 記憶體'},
    '2408': {'Name': '南亞科', 'Sector': '電子: 記憶體'}, '2474': {'Name': '華邦電', 'Sector': '電子: 記憶體'},
    '3037': {'Name': '欣興', 'Sector': '電子: PCB'}, '2317': {'Name': '鴻海', 'Sector': '電子: 代工組裝'},
    '4938': {'Name': '和碩', 'Sector': '電子: 代工組裝'}, '2308': {'Name': '台達電', 'Sector': '電子: 零組件/電源'},
    '2357': {'Name': '華碩', 'Sector': '電子: PC/品牌'}, '2382': {'Name': '廣達', 'Sector': '電子: 伺服器/PC'},
    '2395': {'Name': '研華', 'Sector': '電子: 工業電腦'}, '3008': {'Name': '大立光', 'Sector': '電子: 光學元件'},
    '2498': {'Name': '宏達電', 'Sector': '電子: 通訊/VR'}, '1301': {'Name': '台塑', 'Sector': '塑膠/石化'},
    '1303': {'Name': '南亞', 'Sector': '塑膠/石化'}, '2002': {'Name': '中鋼', 'Sector': '鋼鐵'},
    '6505': {'Name': '台塑化', 'Sector': '塑膠/石化'}, '1101': {'Name': '台泥', 'Sector': '水泥'},
    '1102': {'Name': '亞泥', 'Sector': '水泥'}, '1402': {'Name': '遠東新', 'Sector': '紡織'},
    '2881': {'Name': '富邦金', 'Sector': '金融保險'}, '2882': {'Name': '國泰金', 'Sector': '金融保險'},
    '2886': {'Name': '兆豐金', 'Sector': '金融保險'}, '2891': {'Name': '中信金', 'Sector': '金融保險'},
    '2884': {'Name': '玉山金', 'Sector': '金融保險'}, '5871': {'Name': '中租-KY', 'Sector': '金融保險'},
    '2801': {'Name': '彰銀', 'Sector': '金融保險'}, '2823': {'Name': '華南金', 'Sector': '金融保險'},
    '2834': {'Name': '臺企銀', 'Sector': '金融保險'}, '2892': {'Name': '第一金', 'Sector': '金融保險'},
    '2412': {'Name': '中華電', 'Sector': '電信服務'}, '1216': {'Name': '統一', 'Sector': '食品'},
    '2603': {'Name': '長榮', 'Sector': '航運'}, '2609': {'Name': '陽明', 'Sector': '航運'},
    '2606': {'Name': '裕民', 'Sector': '航運'}, '2615': {'Name': '萬海', 'Sector': '航運'},
    '2912': {'Name': '統一超', 'Sector': '百貨零售'}, '3576': {'Name': '聯合再生', 'Sector': '綠能/太陽能'},
    '4904': {'Name': '遠傳', 'Sector': '電信服務'}, '3041': {'Name': '揚智', 'Sector': '電子: IC 設計'},
    '2707': {'Name': '晶華', 'Sector': '觀光'}, '1590': {'Name': '亞德客-KY', 'Sector': '機械設備'},
    '1722': {'Name': '台肥', 'Sector': '農業/肥料'}, '2345': {'Name': '智邦', 'Sector': '電子: 網通設備'},
    '2347': {'Name': '聯強', 'Sector': '電子: 通路服務'}, '3010': {'Name': '華立', 'Sector': '電子: 材料'},
    '2812': {'Name': '台灣大', 'Sector': '電信服務'}, '8454': {'Name': '富邦媒', 'Sector': '電子商務'},
}

STOCK_INFO_MAP = {k: v for k, v in STOCK_CLASSIFICATION.items()}
STATIC_TOP_50_CODES = list(ISSUED_SHARES_MAP.keys())


# --- 獨立函數：單純負責呼叫 API，處理錯誤 ---
def load_latest_data(stock_list):
    """
    僅負責向 FinMind 批量請求數據，若失敗則回報錯誤。
    """
    end_date = datetime.date.today().strftime("%Y-%m-%d")
    start_date = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    try:
        df_all_data = dl.taiwan_stock_daily(
            stock_id=stock_list,
            start_date=start_date,
            end_date=end_date
        )
        return df_all_data
    except Exception as e:
        # 顯示錯誤，但返回空 DataFrame
        st.error(f"❌ 批量抓取最新報價數據時發生錯誤，將嘗試載入上次成功資料。錯誤詳情: {e}")
        return pd.DataFrame()


# --- 主數據處理函數：包含快取邏輯 ---
@st.cache_data(ttl=3600)
def fetch_market_data(stock_list, current_time): 
    """
    嘗試載入最新數據。如果失敗，則從 st.session_state 載入上一次成功的結果。
    """
    # 1. 嘗試載入最新數據
    df_all_data = load_latest_data(stock_list)
    
    # 2. 數據處理 (如果成功獲取新數據)
    if not df_all_data.empty:
        processed_data = []

        for stock_id in stock_list:
            df_stock = df_all_data[df_all_data['stock_id'] == stock_id].sort_values('date')
            
            stock_info = STOCK_INFO_MAP.get(stock_id, {"Name": stock_id, "Sector": "未分類"})
            shares_count = ISSUED_SHARES_MAP.get(stock_id, 1.0) 

            if not df_stock.empty and len(df_stock) >= 1:
                try:
                    latest = df_stock.iloc[-1]
                    current_price = latest['close']
                    
                    actual_market_cap = current_price * shares_count 
                    
                    change_pct = 0.0
                    if len(df_stock) >= 2:
                        prev_close = df_stock.iloc[-2]['close']
                        if prev_close > 0:
                            change_pct = ((current_price - prev_close) / prev_close) * 100
                    
                    processed_data.append({
                        "Code": stock_id,
                        "Name": stock_info['Name'],
                        "Sector": stock_info['Sector'],
                        "Size": actual_market_cap,
                        "Price": current_price,
                        "ChangePct": round(change_pct, 2),
                        "LabelInfo": f"{stock_info['Name']}<br>{current_price} ({round(change_pct, 2)}%)"
                    })
                except Exception:
                    continue
        
        df_result = pd.DataFrame(processed_data)
        # 成功後儲存到 session state 作為備援
        st.session_state['last_successful_data'] = df_result
        return df_result
    
    # 3. 數據備援 (如果 API 抓取失敗)
    elif 'last_successful_data' in st.session_state and not st.session_state['last_successful_data'].empty:
        st.warning("⚠️ 警告：無法獲取最新報價，顯示上次成功快取的資料。")
        return st.session_state['last_successful_data']
        
    # 4. 首次運行失敗或無快取
    return pd.DataFrame()


# --- 主程式邏輯 ---
st.info(f"✅ 已載入 {len(STATIC_TOP_50_CODES)} 檔成分股，正在嘗試獲取最新報價...")

# 使用 session state 儲存一個 key 來控制快取刷新
if 'cache_key' not in st.session_state:
    st.session_state['cache_key'] = datetime.datetime.now()

if st.button("強制刷新報價"):
    # 更改 key，強制 fetch_market_data 重新執行 
    st.session_state['cache_key'] = datetime.datetime.now()
    # 清除 cache_data (會強制嘗試呼叫 API)
    st.cache_data.clear()

# 將 cache_key 傳入函數，讓按鈕可以控制快取刷新
df = fetch_market_data(STATIC_TOP_50_CODES, st.session_state['cache_key'])

if not df.empty:
    
    # 檢查數據完整性
    missing_stocks = len(STATIC_TOP_50_CODES) - len(df)
    if missing_stocks > 0 and 'last_successful_data' in st.session_state:
        st.error(f"❌ 最新數據僅抓取到 {len(df)} 檔股票數據，但已成功載入 {len(st.session_state['last_successful_data'])} 檔備援數據。")
    elif missing_stocks == 0:
         st.success(f"✅ 成功顯示 {len(df)} 檔股票數據。")
         
    fig = px.treemap(
        df,
        path=[px.Constant("台灣 50 市場結構"), 'Sector', 'LabelInfo'], 
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
        hovertemplate='<b>%{label}</b><br>實際市值(百萬): %{value:,.0f}<br>漲跌幅: %{color:.2f}%',
        textfont_size=24
    )
    
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=700)
    
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("查看詳細數據表"):
        st.dataframe(df[['Code', 'Name', 'Sector', 'Price', 'ChangePct', 'Size']].sort_values('Size', ascending=False).rename(columns={'Size': '實際市值(百萬)'}))
else:
    st.warning("⚠️ 警告：目前沒有任何快取或最新資料可用，無法繪製熱力圖。")