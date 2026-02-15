import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# 1. 頁面配置
st.set_page_config(page_title="AI 技術分析系統", layout="wide")
st.markdown("<style>.main { background-color: #05070a; color: #e0e0e0; }</style>", unsafe_allow_html=True)

# 2. 技術評分邏輯
def tech_score_logic(df):
    latest = df.iloc[-1]
    score = 0
    if latest['Close'] > latest['MA20']: score += 40
    if latest['RSI'] < 30: score += 30
    elif 30 <= latest['RSI'] <= 60: score += 15
    bbl_col = [c for c in df.columns if 'BBL' in c][0]
    if latest['Close'] < latest[bbl_col] * 1.02: score += 30
    return min(score, 100)

# 3. 介面
st.title("🛡️ AI 股市技術分析系統")
with st.sidebar:
    st.header("🔍 分析設定")
    stock_id = st.text_input("輸入台股代碼", "2330.TW")
    period = st.selectbox("時間軸", ["1y", "6mo", "2y"])
    analyze_btn = st.button("🚀 執行技術驗證")

if analyze_btn:
    with st.spinner('計算中...'):
        df = yf.download(stock_id, period=period, auto_adjust=True)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            # 計算指標
            df['MA5'] = ta.sma(df['Close'], length=5)
            df['MA10'] = ta.sma(df['Close'], length=10)
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['MA60'] = ta.sma(df['Close'], length=60)
            df['RSI'] = ta.rsi(df['Close'], length=14)
            df = pd.concat([df, ta.bbands(df['Close'], length=20, std=2)], axis=1)
            
            ai_score = tech_score_logic(df)
            latest = df.iloc[-1]

            t1, t2 = st.tabs(["🎯 診斷報告", "📈 K線走勢"])
            with t1:
                c1, c2 = st.columns([1, 2])
                with c1:
                    fig = go.Figure(go.Indicator(mode="gauge+number", value=ai_score, title={'text': "技術評分"}, gauge={'axis':{'range':[0,100]},'bar':{'color':"#00d4ff"}}))
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color':"white"}, height=300, margin=dict(t=50, b=20))
                    st.plotly_chart(fig, use_container_width=True)
                with c2:
                    st.subheader(f"📊 {stock_id} 結論")
                    if ai_score >= 70: st.success("✅ **【偏多看待】** 指標轉強。")
                    elif ai_score >= 40: st.info("⚠️ **【盤整階段】** 建議觀察。")
                    else: st.error("❌ **【偏空防守】** 指標走弱。")
                    st.write(f"目前價格：{latest['Close']:.1f} / RSI：{latest['RSI']:.1f}")

            with t2:
                fig_k = go.Figure()
                fig_k.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'))
                fig_k.add_trace(go.Scatter(x=df.index, y=df['MA5'], name='5日', line=dict(color='yellow', width=1)))
                fig_k.add_trace(go.Scatter(x=df.index, y=df['MA10'], name='10日', line=dict(color='magenta', width=1)))
                fig_k.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='20日', line=dict(color='#00d4ff', width=2)))
                fig_k.add_trace(go.Scatter(x=df.index, y=df['MA60'], name='60日', line=dict(color='lime', width=2)))
                fig_k.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig_k, use_container_width=True)
        else:
            st.error("查無資料")
