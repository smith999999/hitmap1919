import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf 
import datetime

# 1. 網頁基本設定 (必須是第一行指令)
st.set_page_config(
    page_title="台灣 50 市場熱力圖", 
    layout="wide",
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# --- CSS 優化 ---
st.markdown("""
    <style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
    .trace .text {
        font-size: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 核心數據結構 ---
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

STOCK_CLASSIFICATION = {
    '2330': {'Name': '台積電', 'Sector': '電子: 晶圓代工'}, '2454': {'Name': '聯發科', 'Sector': '電子: IC 設計'},
    '2303': {'Name': '聯電', 'Sector': '電子: 晶圓代工'}, '3711': {'Name': '日月光投控', 'Sector': '電子: 封裝測試'},
    '6415': {'Name': '矽力*-KY', 'Sector': '電子: IC 設計'}, '2327': {'Name': '群聯', 'Sector': '電子: 記憶體'},
    '2408': {'Name': '南亞科', 'Sector': '電子: 記憶體'}, '2474': {'Name': '華邦電', 'Sector': '電子: 記憶體'},
    '3037': {'Name': '欣興', 'Sector': '電子: PCB'}, '2317': {'Name': '鴻海', 'Sector': '電子: 代工組裝'},
    '4938': {'Name': '和碩', 'Sector': '電子: 代工組裝'}, '2308': {'Name': '台達電', 'Sector': '電子: 零組件'},
    '2357': {'Name': '華碩', 'Sector': '電子: PC/品牌'}, '2382': {'Name': '廣達', 'Sector': '電子: 伺服器'},
    '2395': {'Name': '研華', 'Sector': '電子: 工業電腦'}, '3008': {'Name': '大立光', 'Sector': '電子: 光學元件'},
    '2498': {'Name': '宏達電', 'Sector': '電子: 通訊/VR'}, '1301': {'Name': '台塑', 'Sector': '傳產: 塑膠'},
    '1303': {'Name': '南亞', 'Sector': '傳產: 塑膠'}, '2002': {'Name': '中鋼', 'Sector': '傳產: 鋼鐵'},
    '6505': {'Name': '台塑化', 'Sector': '傳產: 塑膠'}, '1101': {'Name': '台泥', 'Sector': '傳產: 水泥'},
    '1102': {'Name': '亞泥', 'Sector': '傳產: 水泥'}, '1402': {'Name': '遠東新', 'Sector': '傳產: 紡織'},
    '2881': {'Name': '富邦金', 'Sector': '金融保險'}, '2882': {'Name': '國泰金', 'Sector': '金融保險'},
    '2886': {'Name': '兆豐金', 'Sector': '金融保險'}, '2891': {'Name': '中信金', 'Sector': '金融保險'},
    '2884': {'Name': '玉山金', 'Sector': '金融保險'}, '5871': {'Name': '中租-KY', 'Sector': '金融保險'},
    '2801': {'Name': '彰銀', 'Sector': '金融保險'}, '2823': {'Name': '華南金', 'Sector': '金融保險'},
    '2834': {'Name': '臺企銀', 'Sector': '金融保險'}, '2892': {'Name': '第一金', 'Sector': '金融保險'},
    '2412': {'Name': '中華電', 'Sector': '電信服務'}, '1216': {'Name': '統一', 'Sector': '傳產: 食品'},
    '2603': {'Name': '長榮', 'Sector': '傳產: 航運'}, '2609': {'Name': '陽明', 'Sector': '傳產: 航運'},
    '2606': {'Name': '裕民', 'Sector': '傳產: 航運'}, '2615': {'Name': '萬海', 'Sector': '傳產: 航運'},
    '2912': {'Name': '統一超', 'Sector': '傳產: 百貨'}, '3576': {'Name': '聯合再生', 'Sector': '綠能'},
    '4904': {'Name': '遠傳', 'Sector': '電信服務'}, '3041': {'Name': '揚智', 'Sector': '電子: IC 設計'},
    '2707': {'Name': '晶華', 'Sector': '傳產: 觀光'}, '1590': {'Name': '亞德客-KY', 'Sector': '傳產: 機械'},
    '1722': {'Name': '台肥', 'Sector': '傳產: 化工'}, '2345': {'Name': '智邦', 'Sector': '電子: 網通'},
    '2347': {'Name': '聯強', 'Sector': '電子: 通路'}, '3010': {'Name': '華立', 'Sector': '電子: 材料'},
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
    """分批抓取並合併數據"""
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=4) # 抓多一天以防假日
    
    all_data_list = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_chunks = (len(yf_codes) // chunk_size) + 1
    
    for i, chunk in enumerate(chunks(yf_codes, chunk_size)):
        status_text.text(f"⏳ 正在更新數據: 第 {i+1}/{total_chunks} 批...")
        try:
            # 強制 auto_adjust=False 以確保 Close 和 Adj Close 分離
            df = yf.download(chunk, start=start_date, end=end_date, interval="1d", progress=False, auto_adjust=False)
            if not df.empty:
                all_data_list.append(df)
        except Exception:
            pass
        progress_bar.progress((i + 1) / total_chunks)
            
    status_text.empty()
    progress_bar.empty()
    
    if not all_data_list:
        return pd.DataFrame()
        
    return pd.concat(all_data_list, axis=1)

def process_stock_data(df_all, tw_codes):
    """處理原始數據為熱力圖格式"""
    processed = []
    
    # 確保 df_all 是 MultiIndex columns，避免 yfinance 抓單一股票時格式不同
    if not isinstance(df_all.columns, pd.MultiIndex):
        # 如果不是 MultiIndex，嘗試簡單處理 (通常批量抓取會是 MultiIndex)
        return pd.DataFrame(columns=['Code', 'Name', 'Sector', 'Price', 'ChangePct', 'Size', 'Label'])

    for code in tw_codes:
        yf_code = f"{code}.TW"
        try:
            # 嘗試抓取 Close 和 Adj Close
            # 注意：yfinance 的 MultiIndex 順序可能是 (Price Type, Ticker)
            # 使用 .xs 或 .loc 進行安全存取
            
            # 檢查 yf_code 是否在 columns 的第二層級中
            if yf_code not in df_all.columns.get_level_values(1):
                continue

            closes = df_all.xs(yf_code, axis=1, level=1)['Close'].dropna()
            
            # 嘗試獲取前一日收盤價 (優先用 Adj Close，若無則用 Close)
            if 'Adj Close' in df_all.columns.get_level_values(0):
                 prev_series = df_all.xs(yf_code, axis=1, level=1)['Adj Close'].dropna()
            else:
                 prev_series = closes

            if len(closes) > 0:
                price = closes.iloc[-1]
                shares = ISSUED_SHARES_MAP.get(code, 0)
                mkt_cap = price * shares
                
                change_pct = 0.0
                if len(prev_series) >= 2:
                    prev = prev_series.iloc[-2]
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
        except Exception as e:
            # 避免單一股票錯誤導致崩潰
            continue
    
    # 🚨 關鍵修正：如果沒有處理到任何數據，回傳一個空的 DataFrame 但帶有正確的 columns
    # 這能防止後續 df['Sector'] 報錯 KeyError
    if not processed:
        return pd.DataFrame(columns=['Code', 'Name', 'Sector', 'Price', 'ChangePct', 'Size', 'Label'])
            
    return pd.DataFrame(processed)

# --- 主頁面 UI ---

# 1. 側邊欄控制
with st.sidebar:
    st.header("⚙️ 設定")
    if st.button("🔄 強制刷新數據", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    
    st.subheader("🎨 顯示設定")
    color_threshold = st.slider("漲跌顏色敏感度 (%)", 1.0, 10.0, 3.0, 0.5)
    
    all_sectors = sorted(list(set([v['Sector'] for v in STOCK_CLASSIFICATION.values()])))
    selected_sectors = st.multiselect("🔍 篩選產業", all_sectors, default=all_sectors)
    
    st.markdown("---")
    st.caption("資料來源: Yahoo Finance (延遲報價)")

# 2. 標題區
col_title, col_date = st.columns([3, 1])
with col_title:
    st.title("🇹🇼 台灣 50 市值熱力圖")
with col_date:
    st.write("")
    st.markdown(f"**更新日期:** `{datetime.datetime.now().strftime('%Y-%m-%d')}`")

# 3. 數據獲取與處理
raw_data = fetch_data_batches(YF_STOCK_CODES, chunk_size=10)

# 建立預設的空 df，以防 raw_data 為空時報錯
df = pd.DataFrame(columns=['Code', 'Name', 'Sector', 'Price', 'ChangePct', 'Size', 'Label'])

if not raw_data.empty:
    df = process_stock_data(raw_data, STATIC_TW_CODES)

# 確保 df 不是空的再進行過濾，避免 KeyError
if not df.empty:
    # 過濾產業
    if selected_sectors:
        df = df[df['Sector'].isin(selected_sectors)]
    
    if not df.empty:
        # 4. 關鍵指標
        m1, m2, m3, m4 = st.columns(4)
        
        up_count = len(df[df['ChangePct'] > 0])
        down_count = len(df[df['ChangePct'] < 0])
        # 避免 idxmax 在空資料時報錯
        top_gainer = df.loc[df['ChangePct'].idxmax()] if not df.empty else None
        top_loser = df.loc[df['ChangePct'].idxmin()] if not df.empty else None
        
        m1.metric("📈 上漲家數", f"{up_count} 家", delta=f"{up_count - down_count} 淨變動", delta_color="off")
        m2.metric("📉 下跌家數", f"{down_count} 家", delta_color="off")
        if top_gainer is not None:
            m3.metric("🔥 最強個股", top_gainer['Name'], f"{top_gainer['ChangePct']:+.2f}%")
        if top_loser is not None:
            m4.metric("❄️ 最弱個股", top_loser['Name'], f"{top_loser['ChangePct']:+.2f}%")

        st.divider()

        # 5. 繪製熱力圖
        fig = px.treemap(
            df,
            path=[px.Constant("全市場"), 'Sector', 'Label'],
            values='Size',
            color='ChangePct',
            color_continuous_scale=['#00FF00', '#ccffcc', '#f0f0f0', '#ffcccc', '#FF0000'],
            range_color=[-color_threshold, color_threshold],
            hover_data={
                'Label': False,
                'Name': True,
                'Price': ':.2f',
                'ChangePct': ':.2f%',
                'Size': ':,.0f'
            }
        )

        fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=650, font=dict(size=16))
        fig.update_traces(textinfo="label", textfont=dict(size=20), hovertemplate="<b>%{customdata[0]}</b><br>價格: %{customdata[1]}<br>漲跌: %{customdata[2]}<br>市值權重: %{value:,.0f}")

        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("📊 查看詳細報價表"):
            display_df = df[['Code', 'Name', 'Sector', 'Price', 'ChangePct', 'Size']].copy()
            display_df['Size'] = display_df['Size'].apply(lambda x: f"{x/100:,.0f} 億")
            display_df.columns = ['代號', '名稱', '產業', '股價', '漲跌幅(%)', '市值(估)']
            st.dataframe(
                display_df.sort_values('漲跌幅(%)', ascending=False).style.map(
                    lambda x: 'color: red' if x > 0 else 'color: green', subset=['漲跌幅(%)']
                ),
                use_container_width=True,
                hide_index=True
            )
    else:
        st.warning("篩選條件下無資料，或該產業無成分股數據。")
else:
    st.error("❌ 目前無法獲取資料。這可能是 Yahoo Finance 暫時連線問題，請稍後點擊左側「強制刷新」按鈕。")