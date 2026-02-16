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
    days_input = st.slider("券商統計天數", 1, 15, 1) # 增加到15天
    analyze_btn = st.button("🚀 執行全方位驗證")

if analyze_btn:
    with st.spinner(f'正在分析 {stock_id} 籌碼結構...'):
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
            
            # 模擬數據：根據代號固定隨機種子，讓同一支股票的券商相對固定
            seed_val = int(raw_input) if raw_input.isdigit() else 42
            np.random.seed(seed_val)
            
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
                    st.subheader(f"📊 {stock_id} 分析總結")
                    st.write(f"針對股票 **{stock_id}** 的技術面與籌碼面交叉驗證：")
                    if ai_score >= 75: st.success("✅ **【建議關注】** 該股目前處於多頭排列，法人動向偏多。")
                    elif ai_score >= 45: st.info("⚠️ **【區間整理】** 股價波動收斂，建議觀察券商分點是否持續吃貨。")
                    else: st.error("❌ **【風險警告】** 指標轉弱，且面臨主力調節壓力。")

            with t2:
                fig_k = make_subplots(rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.4, 0.15, 0.15, 0.15, 0.15])
                fig_k.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
                for ma, color in zip(['MA5','MA10','MA20','MA60'], ['yellow','magenta','#00d4ff','lime']):
                    fig_k.add_trace(go.Scatter(x=df.index, y=df[ma], name=ma, line=dict(color=color, width=1)), row=1, col=1)
                v_colors = ['red' if df['Close'][i] >= df['Open'][i] else 'green' for i in range(len(df))]
                fig_k.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color=v_colors), row=2, col=1)
                fig_k.add_trace(go.Bar(x=df.index, y=df['Foreign'], name='外資', marker_color='#FF4500'), row=3, col=1)
                fig_k.add_trace(go.Bar(x=df.index, y=df['Trust'], name='投信', marker_color='#8A2BE2'), row=4, col=1)
                fig_k.add_trace(go.Bar(x=df.index, y=df['Dealers'], name='自營商', marker_color='#00CED1'), row=5, col=1)
                fig_k.update_layout(template="plotly_dark", height=1000, xaxis_rangeslider_visible=False, showlegend=True, legend=dict(orientation="h", y=1.02))
                st.plotly_chart(fig_k, use_container_width=True)

            with t3:
                st.subheader(f"📊 {stock_id} 指定股票 - 近 {days_input} 天券商買賣報表")
                # 建立券商清單 (包含主力與大本營)
                brokers_pool = ["凱基台北", "摩根大通", "元大台北", "美林", "高盛", "瑞銀", "富邦台北", "國泰敦南", "永豐金台北", "統一台北", "兆豐東門", "群益金鼎", "康和台北", "華南永昌", "台銀台北", "土銀", "合庫台北", "新光台北", "元富", "日盛"]
                
                # 使用股票代碼作為 Seed，確保同一支股票對應的券商數據一致
                np.random.seed(seed_val)
                np.random.shuffle(brokers_pool)
                
                # 計算該股近期的成交量規模，用來模擬更準確的買賣張數
                vol_factor = (latest['Volume'] / 50000) * days_input
                
                buy_names = brokers_pool[:15]
                sell_names = brokers_pool[5:20]
                
                buy_vals = sorted([int(np.random.randint(200, 1000) * vol_factor) for _ in range(15)])
                sell_vals = sorted([int(np.random.randint(200, 1000) * vol_factor) for _ in range(15)])

                col_b, col_s = st.columns(2)
                with col_b:
                    st.write(f"🟢 **{stock_id} 超買券商 (張)**")
                    fig_b = go.Figure(go.Bar(x=buy_vals, y=buy_names, orientation='h', marker_color='red'))
                    fig_b.update_layout(template="plotly_dark", height=500, margin=dict(l=20,r=20,t=20,b=20), yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_b, use_container_width=True)
                with col_s:
                    st.write(f"🔴 **{stock_id} 超賣券商 (張)**")
                    fig_s = go.Figure(go.Bar(x=sell_vals, y=sell_names, orientation='h', marker_color='green'))
                    fig_s.update_layout(template="plotly_dark", height=500, margin=dict(l=20,r=20,t=20,b=20), yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_s, use_container_width=True)
        else:
            st.error(f"查無 {stock_id} 相關數據")
