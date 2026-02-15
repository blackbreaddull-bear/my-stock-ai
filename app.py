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

# 2. 核心評分邏輯 (已取消歷史避讓機制)
def tech_score_logic(df):
    latest = df.iloc[-1]
    score = 0
    
    # 均線判定 (40%)
    if latest['Close'] > latest['MA20']: 
        score += 40
        
    # RSI 強弱判定 (30%)
    if latest['RSI'] < 30: # 超跌
        score += 30
    elif 30 <= latest['RSI'] <= 60: # 合理區間
        score += 15
        
    # 布林通道位階 (30%)
    bbl_col = [c for c in df.columns if 'BBL' in c][0]
    if latest['Close'] < latest[bbl_col] * 1.02: # 接近底線
        score += 30
        
    return min(score, 100)

# 3. 介面
st.title("🛡️ AI 股市技術分析系統")
with st.sidebar:
    st.header("🔍 分析設定")
    stock_id = st.text_input("輸入台股代碼", "2330.TW")
    period = st.selectbox("分析時間軸", ["1y", "6mo", "2y"])
    analyze_btn = st.button("🚀 執行深度技術驗證")

if analyze_btn:
    with st.spinner('AI 數據計算中...'):
        df = yf.download(stock_id, period=period, auto_adjust=True)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): 
                df.columns = df.columns.get_level_values(0)
            
            # 計算基礎技術指標
            df['MA20'] = ta.sma(df['Close'], length=20)
            bbands = ta.bbands(df['Close'], length=20, std=2)
            df = pd.concat([df, bbands], axis=1)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            
            ai_score = tech_score_logic(df)
            latest = df.iloc[-1]

            tab1, tab2 = st.tabs(["🎯 技術診斷報告", "📈 K線走勢"])
            with tab1:
                col1, col2 = st.columns([1, 2])
                with col1:
                    fig_gauge = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = ai_score,
                        title = {'text': "技術面評分"},
                        gauge = {
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "#00d4ff"},
                            'steps': [
                                {'range': [0, 40], 'color': '#3b3b3b'},
                                {'range': [40, 70], 'color': '#1a3a4a'},
                                {'range': [70, 100], 'color': '#005f73'}]
                        }
                    ))
                    fig_gauge.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white"}, height=300)
                    st.plotly_chart(fig_gauge, use_container_width=True)
                
                with col2:
                    st.subheader(f"📊 {stock_id} 分析結論")
                    if ai_score >= 70:
                        st.success("✅ **【偏多看待】** 技術指標呈現集體轉強訊號。")
                    elif ai_score >= 40:
                        st.info("⚠️ **【盤整階段】** 指標中性，建議分批觀察。")
                    else:
                        st.error("❌ **【偏空防守】** 多個指標走弱，建議保持謹慎。")
                    
                    st.write(f"目前價格：{latest['Close']:.1f}")
                    st.write(f"20日均線：{latest['MA20']:.1f}")
                    st.write(f"RSI (14)：{latest['RSI']:.1f}")

            with tab2:
                fig_main = go.Figure()
                fig_main.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low
