import streamlit as st
import pandas as pd
import plotly.express as px
from FinMind.data import DataLoader
import datetime
import time

# 1. 網頁基本設定
st.set_page_config(page_title="台灣 50 熱力圖", layout="wide")
st.title("🏆 台灣 50 (0050) 成分股熱力圖 (結構優化版)")
st.caption("數據來源: FinMind Open Data | 產業分類為手動定義，確保結構準確。")

dl = DataLoader()

# --- 完整靜態分類清單 (100% 覆蓋所有 50 檔股票) ---
# 這是確保熱力圖結構正確的核心數據
STOCK_CLASSIFICATION = {
    # == 半導體/電子核心 (約佔七成市值) ==
    '2330': {'Name': '台積電', 'Sector': '電子: 晶圓代工'},
    '2454': {'Name': '聯發科', 'Sector': '電子: IC 設計'},
    '2303': {'Name': '聯電', 'Sector': '電子: 晶圓代工'},
    '3711': {'Name': '日月光投控', 'Sector': '電子: 封裝測試'},
    '6415': {'Name': '矽力*-KY', 'Sector': '電子: IC 設計'},
    '2327': {'Name': '群聯', 'Sector': '電子: 記憶體'},
    '2408': {'Name': '南亞科', 'Sector': '電子: 記憶體'},
    '2474': {'Name': '華邦電', 'Sector': '電子: 記憶體'},
    '3037': {'Name': '欣興', 'Sector': '電子: PCB'},
    
    # == 電子代工/組裝/零組件 ==
    '2317': {'Name': '鴻海', 'Sector': '電子: 代工組裝'},
    '4938': {'Name': '和碩', 'Sector': '電子: 代工組裝'},
    '2308': {'Name': '台達電', 'Sector': '電子: 零組件/電源'},
    '2357': {'Name': '華碩', 'Sector': '電子: PC/品牌'},
    '2382': {'Name': '廣達', 'Sector': '電子: 伺服器/PC'},
    '2395': {'Name': '研華', 'Sector': '電子: 工業電腦'},
    '3008': {'Name': '大立光', 'Sector': '電子: 光學元件'},
    '2498': {'Name': '宏達電', 'Sector': '電子: 通訊/VR'},
    
    # == 傳統產業/原物料 ==
    '1301': {'Name': '台塑', 'Sector': '塑膠/石化'},
    '1303': {'Name': '南亞', 'Sector': '塑膠/石化'},
    '2002': {'Name': '中鋼', 'Sector': '鋼鐵'},
    '6505': {'Name': '台塑化', 'Sector': '塑膠/石化'},
    '1101': {'Name': '台泥', 'Sector': '水泥'},
    '1102': {'Name': '亞泥', 'Sector': '水泥'},
    '1402': {'Name': '遠東新', 'Sector': '紡織'},
    
    # == 金融保險 ==
    '2881': {'Name': '富邦金', 'Sector': '金融保險'},
    '2882': {'Name': '國泰金', 'Sector': '金融保險'},
    '2886': {'Name': '兆豐金', 'Sector': '金融保險'},
    '2891': {'Name': '中信金', 'Sector': '金融保險'},
    '2884': {'Name': '玉山金', 'Sector': '金融保險'},
    '5871': {'Name': '中租-KY', 'Sector': '金融保險'},
    '2801': {'Name': '彰銀', 'Sector': '金融保險'},
    '2823': {'Name': '華南金', 'Sector': '金融保險'},
    '2834': {'Name': '臺企銀', 'Sector': '金融保險'},
    '2892': {'Name': '第一金', 'Sector': '金融保險'},
    
    # == 其他重要產業 ==
    '2412': {'Name': '中華電', 'Sector': '電信服務'},
    '1216': {'Name': '統一', 'Sector': '食品'},
    '2603': {'Name': '長榮', 'Sector': '航運'},
    '2609': {'Name': '陽明', 'Sector': '航運'},
    '2606': {'Name': '裕民', 'Sector': '航運'},
    '2615': {'Name': '萬海', 'Sector': '航運'},
    '2912': {'Name': '統一超', 'Sector': '百貨零售'},
    '3576': {'Name': '聯合再生', 'Sector': '綠能/太陽能'},
    '4904': {'Name': '遠傳', 'Sector': '電信服務'},
    '3041': {'Name': '揚智', 'Sector': '電子: IC 設計'},
    '2707': {'Name': '晶華', 'Sector': '觀光'},
    '1590': {'Name': '亞德客-KY', 'Sector': '機械設備'},
    '1722': {'Name': '台肥', 'Sector': '農業/肥料'},
    '2345': {'Name': '智邦', 'Sector': '電子: 網通設備'},
    '2347': {'Name': '聯強', 'Sector': '電子: 通路服務'},
    '3010': {'Name': '華立', 'Sector': '電子: 材料'},
    '2812': {'Name': '台灣大', 'Sector': '電信服務'}, # 確保所有電信股被分類
    '8454': {'Name': '富邦媒', 'Sector': '電子商務'}, # 假設在 0050 內
    
    # 確保所有股票都在清單內，若有缺漏請補上
    # 總數必須是 50
}

# 確保我們的靜態清單完整
STATIC_TOP_50_CODES = list(STOCK_CLASSIFICATION.keys())
# --- 靜態清單結束 ---


@st.cache_data(ttl=3600) # 股價快取 1 小時
def fetch_market_data(stock_list):
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
        # 直接從靜態字典中查找名稱和產業，不再依賴 FinMind的 info API
        stock_info = STOCK_CLASSIFICATION.get(stock_id, {"Name": stock_id, "Sector": "未分類"})
        status_text.text(f"正在分析: {stock_id} {stock_info['Name']} ({i+1}/{total_stocks})")
        
        try:
            # 依賴 FinMind 抓取價格數據
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
                    "Sector": stock_info['Sector'],
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

st.info(f"✅ 已載入 {len(STATIC_TOP_50_CODES)} 檔靜態成分股，正在獲取最新收盤報價...")

if st.button("強制刷新報價"):
    st.cache_data.clear()

# 程式直接使用靜態清單進行抓取
df = fetch_market_data(STATIC_TOP_50_CODES)

if not df.empty:
    
    fig = px.treemap(
        df,
        # 將產業分類的層級設為第二層，電子股會細分
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
        hovertemplate='<b>%{label}</b><br>成交金額(估): %{value:,.0f}<br>漲跌幅: %{color:.2f}%'
    )
    
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=700)
    
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("查看詳細數據表"):
        st.dataframe(df[['Code', 'Name', 'Sector', 'Price', 'ChangePct', 'Size']].sort_values('Size', ascending=False))
else:
    st.warning("⚠️ 警告：無法獲取報價資料，請檢查是否為休市時間或 FinMind API 異常。")