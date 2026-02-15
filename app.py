import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# 1. 頁面風格
st.set_page_config(page_title="AI 核心決策系統", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #05070a; color: #e0e0e0; }
    .stMetric { background-color: #11151c; border: 1px solid #1f2937; padding: 20px; border-radius: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 三重複核避讓邏輯
def triple_check_logic(df):
    latest = df.iloc[-1]
    score = 0
    # 第一重：均線
    if latest['Close'] > latest['MA20']: score += 35
    # 第二重：RSI 避讓
    if 30 < latest['RSI'] < 55: score += 35
    elif latest['RSI'] <= 30: score += 45
    # 第三重：布林位置
    bbl_col = [c for c in df.columns if 'BBL' in c][0]
    if latest['Close'] < latest[bbl_col] * 1.02: score += 20
    return min(score, 100)

# 3. 介面
st.title("🛡️ AI 股市交叉驗證系統 (PRO)")
with st.sidebar:
    st.header("🔍 分析設定")
    stock_id = st.text_input("輸入台股代碼", "2330.TW")
    period = st.selectbox("分析時間軸", ["1y", "6mo", "2y"])
    analyze_btn = st.button("🚀 執行深度交叉驗證")

if analyze_btn:
    with st.spinner('AI 正在進行三重複核...'):
        df = yf.download(stock_id, period=period, auto_adjust=True)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): 
                df.columns = df.columns.get_level_values(0)
            df['MA20'] = ta.sma(df['Close'], length=20)
            bbands = ta.bbands(df['Close'], length=20, std=2)
            df = pd.concat([df, bbands], axis=1)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            ai_score = triple_check_logic(df)
            latest = df.iloc[-1]

            tab1, tab2 = st.tabs(["🎯 AI 診斷報告", "📈 技術走勢"])
            with tab1:
                col1, col2 = st.columns([1, 2])
                with col1:
                    fig_gauge = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = ai_score,
                        title = {'text': "AI 信心評分"},
                        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#00d4ff"}}
                    ))
                    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=300)
                    st.plotly_chart(fig_gauge, use_container_width=True)
                
                with col2:
                    st.subheader(f"📊 {stock_id} 交叉驗證結論")
                    if ai_score >= 75:
                        st.success("✅ **【強烈推薦】** 數據已避開重複歷史高點。")
                    elif ai_score >= 45:
                        st.warning("⚠️ **【中性觀察】** 趨勢盤整中。")
                    else:
                        st.error("❌ **【風險警示】** 數據與歷史高壓區重疊。")
                    st.write(f"目前收盤：{latest['Close']:.1f}")
                    st.write(f"RSI 強度：{latest['RSI']:.1f}")

            with tab2:
                fig_main = go.Figure()
                fig_main.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'))
                fig_main.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig_main, use_container_width=True)
