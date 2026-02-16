import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# 1. 頁面配置
st.set_page_config(page_title="AI 股市全方位分析系統", layout="wide")
st.markdown("<style>.main { background-color: #05070a; color: #e0e0e0; }</style>", unsafe_allow_html=True)

# 2. 核心邏輯
def tech_score_logic(df):
    latest = df.iloc[-1]
    score = 0
    if latest['Close'] > latest['MA20']: score += 40
    if latest['RSI'] < 35: score += 30
    elif 35 <= latest['RSI'] <= 65: score += 15
    bbl_col = [c for c in df.columns if 'BBL' in c][0]
    if latest['Close'] < latest[bbl_col] * 1.02: score += 30
    return min(score, 100)

# 3. 介面
st.title("🛡️ AI 股市技術、法人與券商分析系統")
with st.sidebar:
    st.header("🔍 分析設定")
    raw_input = st.text_input("輸入台股代碼 (只填數字)", "2330")
    stock_id = f"{raw_input}.TW" if raw_input.isdigit() else raw_input
    period = st.selectbox("時間軸", ["1y", "6mo", "2y"])
    st.divider()
    days_input = st.slider("券商統計天數", 1, 10, 1) # 新增天數篩選器
    analyze_btn = st.button("🚀 執行全方位驗證")

if analyze_btn:
    with st.spinner('數據交叉驗證中...'):
        df = yf.download(stock_id, period=period, auto_adjust=True)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            # 指標計算
            df['MA5'] = ta.sma(df['Close'], length=5)
            df['MA10'] = ta.sma(df['Close'], length=10)
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['MA60'] = ta.sma(df['Close'], length=60)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df = pd.concat([df, ta.bbands(df['Close'], length=20, std=2)], axis=1)
            
            # 模擬數據：法人與券商 (因免費源無細節)
            np.random.seed(42 + int(raw_input)) # 固定該代碼的模擬隨機值
            df['Foreign'] = (df['Volume'] * (df['Close'].pct_change()) * 0.35).fillna(0)
            df['Trust'] = (df['Volume'] * (df['Close'].pct_change()) * 0.15).fillna(0)
            df['Dealers'] = (df['Volume'] * (df['Close'].pct_change()) * 0.08).fillna(0)
            
            ai_score = tech_score_logic(df)
            latest = df.iloc[-1]

            t1, t2, t3 = st.tabs(["🎯 診斷報告", "📈 K線獨立籌碼區", "🔍 券商籌碼追蹤"])
            
            with t1:
                c1, c2 = st.columns([1, 2])
                with c1:
                    fig_g = go.Figure(go.Indicator(mode="gauge+number", value=ai_score, title={'text': "綜合評分"}, gauge={'axis':{'range':[0,100]},'bar':{'color':"#00d4ff"}}))
                    fig_g.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color':"white"}, height=300, margin=dict(t=50, b=20))
                    st.plotly_chart(fig_g, use_container_width=True)
                with c2:
                    st.subheader(f"📊 {stock_id} 結論")
                    if ai_score >= 75: st.success("✅ **【強烈多頭】** 指標全數轉強，適合觀察進場點。")
                    elif ai_score >= 45: st.info("⚠️ **【中性震盪】** 建議在支撐與壓力區間操作。")
                    else: st.error("❌ **【風險防守】** 趨勢轉弱且籌碼散亂。")
                    st.write(f"目前價格：{latest['Close']:.1f} | 20日線：{latest['MA20']:.1f}")

            with t2:
                fig_k = make_subplots(rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.4, 0.15, 0.15, 0.15, 0.15])
                fig_k.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
                for ma, color in zip(['MA5','MA10','MA20','MA60'], ['yellow','magenta','#00d4ff','lime']):
                    fig_k.add_trace(go.Scatter(x=df.index, y=df[ma], name=ma, line=dict(color=color, width=1)), row=1, col=1)
                v_colors = ['red' if df['Close'][i] >= df['Open'][i] else 'green' for i in range(len(df))]
                fig_k.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color=v_colors), row=2, col=1)
                fig_k.add_trace(go.Bar(x=df.index, y=df['Foreign'], name='外資', marker_color='#FF4500'), row=3, col=1)
                fig_k.add_trace(go.Bar(x=df.index, y=df['Trust'], name['投信'], marker_color='#8A2BE2'), row=4, col=1)
                fig_k.add_trace(go.Bar(x=df.index, y=df['Dealers'], name='自營商', marker_color='#00CED1'), row=5, col=1)
                fig_k.update_layout(template="plotly_dark", height=1000, xaxis_rangeslider_visible=False, legend=dict(orientation="h", y=1.02))
                st.plotly_chart(fig_k, use_container_width=True)

            with t3:
                st.subheader(f"📅 近 {days_input} 天券商分點買賣排行榜 (模擬統計)")
                # 模擬券商名稱與數據
                brokers = ["摩根大通", "美林", "高盛", "瑞銀", "元大", "凱基台北", "富邦", "國泰", "港商野村", "新加坡商瑞銀", "瑞士信貸", "美商高盛", "美林", "元大台北", "永豐金", "兆豐", "統一", "亞東", "台銀", "華南永昌"]
                np.random.shuffle(brokers)
                
                # 根據自選天數調整買賣張數
                scale = days_input * (latest['Volume'] / 100000)
                buy_data = sorted([int(np.random.randint(500, 3000) * scale) for _ in range(15)], reverse=True)
                sell_data = sorted([int(np.random.randint(500, 3000) * scale) for _ in range(15)], reverse=True)
                
                col_buy, col_sell = st.columns(2)
                with col_buy:
                    st.write("🟢 **前 15 大買超券商**")
                    fig_buy = go.Figure(go.Bar(x=buy_data, y=brokers[:15], orientation='h', marker_color='red'))
                    fig_buy.update_layout(template="plotly_dark", yaxis={'autorange': "reversed"}, height=500, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_buy, use_container_width=True)
                
                with col_sell:
                    st.write("🔴 **前 15 大賣超券商**")
                    fig_sell = go.Figure(go.Bar(x=sell_data, y=brokers[5:20], orientation='h', marker_color='green'))
                    fig_sell.update_layout(template="plotly_dark", yaxis={'autorange': "reversed"}, height=500, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_sell, use_container_width=True)
        else:
            st.error(f"查無資料: {stock_id}")
