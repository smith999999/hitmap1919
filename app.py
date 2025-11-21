import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf # ⭐️ 核心修正: 切換到更穩定的 yfinance
import datetime

# 1. 網頁基本設定 (必須是第一行指令)
st.set_page_config(
    page_title="台灣 50 市場熱力圖", 
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# --- CSS 優化 (讓指標數字更好看) ---
st.markdown("""
    <style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
    /* Treemap 內的文字 */
    .trace .text {
        font-size: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 核心數據結構 (使用您提供的 51 檔股票清單) ---

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
    '2891': 19576, '2812': 6703, '8454': 142,
}

# 2. 完整產業分類清單
STOCK_CLASSIFICATION = {
    '2330': {'Name': '台積電', 'Sector': '電子: 晶圓代工'}, '2454': {'Name': '聯發科', 'Sector': '電子: IC 設計'},
    '2303': {'Name': '聯電', 'Sector': '電子: 晶圓代工'}, '3711': {'Name': '日月光投控', 'Sector': '電子: 封裝測試'},
    '6415': {'Name': '矽力*-KY', 'Sector': '電子: IC 設計'}, '2327': {'Name': '群聯', 'Sector': '電子: 記憶體'},
    '2408': {'Name': '南亞科', 'Sector': '電子: 記憶體'}, '2474': {'Name': '華邦電', 'Sector': '電子: 記憶體'},
    '3037': {'Name': '欣興', 'Sector': '電子: PCB'}, '2317': {'Name': '鴻海', 'Sector': '電子: 代工組裝'},
    '4938': {'Name': '和碩', 'Sector': '電子: 代工組裝'}, '2308': {'Name': '台達電', 'Sector': '電子: 零組件/電源'},
    '2357': {'Name': '華碩', 'Sector': '電子: PC/品牌'}, '2382': {'Name': '廣達', 'Sector': '電子: 伺服器/PC'},
    '2395': {'Name': '研華', 'Sector': '電子: 工業電腦'}, '3008': {'Name': '大立光', 'Sector': '電子: 光學元件'},
    '2498': {'Name': '宏達電', 'Sector': '電子: 通訊/VR'}, '1301': {'Name': '台塑', 'Sector': '傳產: 塑膠/石化'},
    '1303': {'Name': '南亞', 'Sector': '傳產: 塑膠/石化'}, '2002': {'Name': '中鋼', 'Sector': '傳產: 鋼鐵'},
    '6505': {'Name': '台塑化', 'Sector': '傳產: 塑膠/石化'}, '1101': {'Name': '台泥', 'Sector': '傳產: 水泥'},
    '1102': {'Name': '亞泥', 'Sector': '傳產: 水泥'}, '1402': {'Name': '遠東新', 'Sector': '傳產: 紡織'},
    '2881': {'Name': '富邦金', 'Sector': '金融保險'}, '2882': {'Name': '國泰金', 'Sector': '金融保險'},
    '2886': {'Name': '兆豐金', 'Sector': '金融保險'}, '2891': {'Name': '中信金', 'Sector': '金融保險'},
    '2884': {'Name': '玉山金', 'Sector': '金融保險'}, '5871': {'Name': '中租-KY', 'Sector': '金融保險'},
    '2801': {'Name': '彰銀', 'Sector': '金融保險'}, '2823': {'Name': '華南金', 'Sector': '金融保險'},
    '2834': {'Name': '臺企銀', 'Sector': '金融保險'}, '2892': {'Name': '第一金', 'Sector': '金融保險'},
    '2412': {'Name': '中華電', 'Sector': '電信服務'}, '1216': {'Name': '統一', 'Sector': '傳產: 食品'},
    '2603': {'Name': '長榮', 'Sector': '傳產: 航運'}, '2609': {'Name': '陽明', 'Sector': '傳產: 航運'},
    '2606': {'Name': '裕民', 'Sector': '傳產: 航運'}, '2615': {'Name': '萬海', 'Sector': '傳產: 航運'},
    '2912': {'Name': '統一超', 'Sector': '傳產: 百貨零售'}, '3576': {'Name': '聯合再生', 'Sector': '綠能/太陽能'},
    '4904': {'Name': '遠傳', 'Sector': '電信服務'}, '3041': {'Name': '揚智', 'Sector': '電子: IC 設計'},
    '2707': {'Name': '晶華', 'Sector': '傳產: 觀光'}, '1590': {'Name': '亞德客-KY', 'Sector': '傳產: 機械設備'},
    '1722': {'Name': '台肥', 'Sector': '傳產: 農業/肥料'}, '2345': {'Name': '智邦', 'Sector': '電子: 網通設備'},
    '2347': {'Name': '聯強', 'Sector': '電子: 通路服務'}, '3010': {'Name': '華立', 'Sector': '電子: 材料'},
    '2812': {'Name': '台灣大', 'Sector': '電信服務'}, '8454': {'Name': '富邦媒', 'Sector': '電子商務'},
}

STATIC_TW_CODES = list(ISSUED_SHARES_MAP.keys())
YF_STOCK_CODES = [f"{code}.TW" for code in STATIC_TW_CODES]


# --- 輔助函數 ---
def chunks(lst, n):
    """將列表切分成小塊"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

@st.cache_data(ttl=3600)
def fetch_data_batches(yf_codes, chunk_size=10):
    """
    ⭐️ 修正獲取方式：使用 yfinance 分批抓取，大幅提高在 Streamlit Cloud 的成功率。
    """
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=3) # 只抓取 3 天，縮短請求時間
    
    all_data_list = []
    
    # 設置進度條和狀態顯示
    progress_bar = st.progress(0)
    status_text = st.empty()
    total_chunks = (len(yf_codes) + chunk_size - 1) // chunk_size # 計算總批數
    
    for i, chunk in enumerate(chunks(yf_codes, chunk_size)):
        status_text.text(f"⏳ 正在更新數據: 第 {i+1}/{total_chunks} 批 ({len(chunk)} 檔)...")
        try:
            # yfinance 批量抓取
            df = yf.download(chunk, start=start_date, end=end_date, interval="1d", progress=False)
            if not df.empty:
                all_data_list.append(df)
        except Exception:
            # 即使某批失敗，也不影響其他批次的數據
            st.warning(f"⚠️ 請求第 {i+1} 批數據失敗，已跳過該批次。")
            pass
        progress_bar.progress((i + 1) / total_chunks)
            
    status_text.empty()
    progress_bar.empty()
    
    if not all_data_list:
        return pd.DataFrame()
        
    # 合併所有成功的批次數據
    return pd.concat(all_data_list, axis=1)

def process_stock_data(df_all, tw_codes):
    """處理原始數據為熱力圖格式"""
    processed = []
    
    # 處理 FinMind/YFinance 兩種數據結構
    # YFinance 數據是 MultiIndex，需要使用 .loc[:, ('欄位名', '股票代碼.TW')] 存取
    
    for code in tw_codes:
        yf_code = f"{code}.TW"
        try:
            # 嘗試使用 Adj Close 獲取昨日收盤價，如果不存在則使用 Close
            if 'Adj Close' in df_all.columns.get_level_values(0):
                 prev_closes = df_all.loc[:, ('Adj Close', yf_code)].dropna()
            else:
                 prev_closes = df_all.loc[:, ('Close', yf_code)].dropna()
                 
            closes = df_all.loc[:, ('Close', yf_code)].dropna()

            if len(closes) > 0:
                price = closes.iloc[-1]
                shares = ISSUED_SHARES_MAP.get(code, 0)
                mkt_cap = price * shares # 實際市值
                
                change_pct = 0.0
                if len(prev_closes) >= 2:
                    prev = prev_closes.iloc[-2]
                    if prev > 0:
                        change_pct = ((price - prev) / prev) * 100
                
                info = STOCK_CLASSIFICATION.get(code, {'Name': code, 'Sector': '其他'})
                
                processed.append({
                    'Code': code,
                    'Name': info['Name'],
                    'Sector': info['Sector'],
                    'Price': price,
                    'ChangePct': change_pct,
                    'Size': mkt_cap,
                    'Label': f"{info['Name']}\n{price:.1f}\n({change_pct:+.2f}%)"
                })
        except KeyError:
            continue
            
    return pd.DataFrame(processed)

# --- 主頁面 UI ---

# 1. 側邊欄控制
with st.sidebar:
    st.header("⚙️ 熱力圖設定")
    if st.button("🔄 強制刷新數據", use_container_width=True, help="清除快取並重新從 YFinance 抓取最新報價"):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    
    st.subheader("🎨 視覺調整")
    # 讓使用者決定顏色區間
    color_threshold = st.slider("漲跌顏色敏感度 (%)", 1.0, 10.0, 3.0, 0.5, help="設定漲跌幅超過多少%時顯示最深色（例如設定 3.0，代表漲跌超過 3% 才顯示最深紅/綠）")
    
    # 產業過濾
    all_sectors = sorted(list(set([v['Sector'] for v in STOCK_CLASSIFICATION.values()])))
    selected_sectors = st.multiselect("🔍 篩選產業", all_sectors, default=all_sectors)
    
    st.markdown("---")
    st.caption("數據來源: Yahoo Finance (延遲報價)")
    st.caption(f"成分股總數: {len(STATIC_TW_CODES)} 檔")

# 2. 標題區
col_title, col_date = st.columns([3, 1])
with col_title:
    st.title("🇹🇼 台灣 50 (0050) 市場熱力圖")
with col_date:
    st.write("") # Spacer
    st.markdown(f"**報價日期:** `{datetime.datetime.now().strftime('%Y-%m-%d')}`")

# 3. 數據獲取與處理
st.info(f"✅ 已載入 {len(STATIC_TW_CODES)} 檔成分股，正在從 YFinance 獲取最新報價...")
raw_data = fetch_data_batches(YF_STOCK_CODES, chunk_size=10)

if not raw_data.empty:
    df = process_stock_data(raw_data, STATIC_TW_CODES)
    
    # 過濾產業
    if selected_sectors:
        df = df[df['Sector'].isin(selected_sectors)]
    
    # 4. 關鍵指標 (Metrics)
    if not df.empty:
        m1, m2, m3, m4 = st.columns(4)
        
        up_count = len(df[df['ChangePct'] > 0])
        down_count = len(df[df['ChangePct'] < 0])
        top_gainer = df.loc[df['ChangePct'].idxmax()]
        top_loser = df.loc[df['ChangePct'].idxmin()]
        
        m1.metric("📈 上漲家數", f"{up_count} 家", delta=f"{up_count - down_count} 淨變動", delta_color="off")
        m2.metric("📉 下跌家數", f"{down_count} 家", delta_color="off")
        m3.metric("🔥 最強個股", top_gainer['Name'], f"{top_gainer['ChangePct']:+.2f}%")
        m4.metric("❄️ 最弱個股", top_loser['Name'], f"{top_loser['ChangePct']:+.2f}%")

        st.divider()

        # 5. 繪製熱力圖
        # 確保 Size 大於 0
        df_plot = df[df['Size'] > 0]
        
        fig = px.treemap(
            df_plot,
            path=[px.Constant("全市場"), 'Sector', 'Label'],
            values='Size',
            color='ChangePct',
            # 台股慣例：紅漲綠跌
            color_continuous_scale=['#00FF00', '#7CFC00', '#f0f0f0', '#ff6666', '#FF0000'],
            # 根據使用者設定的敏感度調整顏色區間
            range_color=[-color_threshold, color_threshold],
            hover_data={
                'Label': False,
                'Name': True,
                'Price': ':.2f',
                'ChangePct': ':.2f%',
                'Size': ':,.0f'
            }
        )

        fig.update_layout(
            margin=dict(t=0, l=0, r=0, b=0),
            height=650,
            uniformtext=dict(minsize=10, mode='hide') # 優化文字顯示
        )
        
        # 區塊內的文字顯示 (Name + ChangePct)
        fig.update_traces(
            textinfo="label",
            hovertemplate="<b>%{customdata[0]}</b><br>價格: %{customdata[1]}<br>漲跌: %{customdata[2]}<br>市值(百萬): %{value:,.0f}"
        )

        st.plotly_chart(fig, use_container_width=True)
        
        # 6. 詳細數據表 (可展開)
        with st.expander("📊 查看詳細報價表"):
            # 讓市值以億為單位顯示，增加可讀性
            display_df = df[['Code', 'Name', 'Sector', 'Price', 'ChangePct', 'Size']].copy()
            display_df['市值(估)'] = display_df['Size'].apply(lambda x: f"{x/100:,.0f} 億")
            display_df = display_df.drop(columns=['Size'])
            display_df.columns = ['代號', '名稱', '產業', '股價', '漲跌幅(%)', '市值(估)']
            
            st.dataframe(
                display_df.sort_values('市值(估)', ascending=False).style.format({'股價': '{:.2f}', '漲跌幅(%)': '{:+.2f}'}).map(
                    lambda x: 'color: red; font-weight: bold' if x > 0 else ('color: green; font-weight: bold' if x < 0 else ''), subset=['漲跌幅(%)']
                ),
                use_container_width=True,
                hide_index=True
            )

    else:
        st.warning("篩選條件下無資料。")
else:
    st.error("❌ 無法獲取股價資料。請檢查網路連線或稍後重試。如果問題持續，可能是 Yahoo Finance API 暫時限制。")