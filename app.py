import streamlit as st
import pandas as pd
import plotly.express as px
from FinMind.data import DataLoader
import datetime
import time

# 1. 網頁基本設定
st.set_page_config(page_title="台灣 50 熱力圖", layout="wide")
st.title("🏆 台灣 50 (0050) 成分股熱力圖 (市值比例修正)")
st.caption("數據來源: FinMind Open Data | 比例基於相對市值權重計算。")

dl = DataLoader()

# --- 核心數據結構 ---

# 1. 相對市值權重 (Proxy Market Cap Weights)
# 數值僅用於決定相對比例，台積電的權重最大
MARKET_CAP_WEIGHTS = {
    '2330': 1000.0,  # 台積電：最大權重
    '2317': 150.0,   # 鴻海
    '2454': 100.0,   # 聯發科
    '2303': 50.0,    # 聯電
    '3711': 45.0,    # 日月光投控
    '2881': 40.0,    # 富邦金
    '2882': 38.0,    # 國泰金
    '2886': 35.0,    # 兆豐金
    '2002': 20.0,    # 中鋼
    '1301': 18.0,    # 台塑
    '1303': 17.0,    # 南亞
    '2412': 15.0,    # 中華電
    '2603': 12.0,    # 長榮
    '6505': 10.0,    # 台塑化
    '3008': 10.0,    # 大立光
    '4904': 8.0,     # 遠傳 (電信)
    '2357': 8.0,     # 華碩
    '2382': 7.0,     # 廣達
    '6415': 6.0,     # 矽力*-KY
    '2395': 6.0,     # 研華
    '2327': 5.0,     # 群聯
    '2615': 5.0,     # 萬海
    '5871': 5.0,     # 中租-KY
    '3037': 4.0,     # 欣興
    '2379': 4.0,     # 研華
    '1101': 3.5,     # 台泥
    '1102': 3.5,     # 亞泥
    '1402': 3.0,     # 遠東新
    '1590': 3.0,     # 亞德客-KY
    '1722': 3.0,     # 台肥
    '2345': 3.0,     # 智邦
    '2347': 3.0,     # 聯強
    '2408': 3.0,     # 南亞科
    '2474': 3.0,     # 華邦電
    '2498': 3.0,     # 宏達電
    '2606': 2.5,     # 裕民
    '2609': 2.5,     # 陽明
    '2707': 2.0,     # 晶華
    '2801': 2.0,     # 彰銀
    '2823': 2.0,     # 華南金
    '2834': 2.0,     # 臺企銀
    '2892': 2.0,     # 第一金
    '3010': 2.0,     # 華立
    '3041': 2.0,     # 揚智
    '3576': 2.0,     # 聯合再生
    '4938': 2.0,     # 和碩
    '1216': 5.0,     # 統一
    '2308': 10.0,    # 台達電
    '2891': 25.0,    # 中信金
    '2603': 18.0,    # 長榮
}

# 2. 完整產業分類清單 (與上一個版本相同，確保結構正確)
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

STATIC_TOP_50_CODES = list(STOCK_CLASSIFICATION.keys())

# --- 核心函數 (修正 Size 計算) ---

@st.cache_data(ttl=3600)
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
        stock_info = STOCK_CLASSIFICATION.get(stock_id, {"Name": stock_id, "Sector": "未分類"})
        
        # 獲取相對市值權重 (Weight)
        market_weight = MARKET_CAP_WEIGHTS.get(stock_id, 1.0) 
        
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
                
                # *** 修正：使用價格乘以權重來計算代理市值 ***
                proxy_market_cap = current_price * market_weight 
                
                change_pct = 0.0
                if len(df_stock) >= 2:
                    prev_close = df_stock.iloc[-2]['close']
                    if prev_close > 0:
                        change_pct = ((current_price - prev_close) / prev_close) * 100
                
                all_data.append({
                    "Code": stock_id,
                    "Name": stock_info['Name'],
                    "Sector": stock_info['Sector'],
                    "Size": proxy_market_cap,  # <--- 熱力圖依據這個數值決定大小
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

st.info(f"✅ 已載入 {len(STATIC_TOP_50_CODES)} 檔成分股，正在獲取最新報價並計算市值比例...")

if st.button("強制刷新報價"):
    st.cache_data.clear()

df = fetch_market_data(STATIC_TOP_50_CODES)

if not df.empty:
    
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
        hovertemplate='<b>%{label}</b><br>代理市值: %{value:,.0f}<br>漲跌幅: %{color:.2f}%'
    )
    
    fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=700)
    
    st.plotly_chart(fig, use_container_width=True)
    
    with st.expander("查看詳細數據表"):
        # 顯示代理市值 (Size) 供確認
        st.dataframe(df[['Code', 'Name', 'Sector', 'Price', 'ChangePct', 'Size']].sort_values('Size', ascending=False))
else:
    st.warning("⚠️ 警告：無法獲取報價資料，請檢查是否為休市時間或 FinMind API 異常。")