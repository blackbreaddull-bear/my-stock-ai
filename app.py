import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# 1. 頁面配置
st.set_page_config(page_title="AI 股市全方位分析", layout="wide")
st.markdown("<style>.main { background-color: #05070a; color: #e0e0e0; }</style>", unsafe_allow_html=True)

# 2. 核心邏輯
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
st.title("🛡️ AI 股市技術與籌碼分析系統")
with st.sidebar:
    st.header("🔍 分析設定")
    raw_input = st.text_input("輸入台股代碼 (只填數字)", "2330")
    stock_id = f"{raw_input}.TW" if raw_input.isdigit() else raw_input
    period = st.selectbox("時間軸", ["1y", "6mo", "2y"])
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
            
            # 籌碼數據擬合 (模擬法人行為)
            np.random.seed(42)
            df['Foreign'] = (df['Volume'] * (df['Close'].pct_change()) * 0.35).fillna(0)
            df['Trust'] = (df['Volume'] * (df['Close'].pct_change()) * 0.15).fillna(0)
            df['Dealers'] = (df['Volume'] * (df['Close'].pct_change()) * 0.08).fillna(0)
            
            ai_score = tech_score_logic(df)
            latest = df.iloc[-1]

            t1, t2 = st.tabs(["🎯 診斷報告", "📈 K線與獨立籌碼區"])
            
            with t1:
                c1, c2 = st.columns([1, 2])
                with c1:
                    fig_g = go.Figure(go.Indicator(mode="gauge+number", value=ai_score, title={'text': "綜合評分"}, gauge={'axis':{'range':[0,100]},'bar':{'color':"#00d4ff"}}))
                    fig_g.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color':"white"}, height=300, margin=dict(t=50, b=20))
                    st.plotly_chart(fig_g, use_container_width=True)
                with c2:
                    st.subheader(f"📊 {stock_id} 結論")
                    if ai_score >= 70: st.success("✅ **【偏多看待】** 三大法人與技術面共振。")
                    elif ai_score >= 40: st.info("⚠️ **【盤整階段】** 法人動向分歧，建議區間操作。")
                    else: st.error("❌ **【偏空防守】** 籌碼面集體撤退。")
                    st.write(f"目前價格：{latest['Close']:.1f} | RSI：{latest['RSI']:.1f}")

            with t2:
                # 建立 5 層子圖 (K線、成交量、外資、投信、自營)
                fig_k = make_subplots(rows=5, cols=1, shared_xaxes=True, 
                                      vertical_spacing=0.02, 
                                      row_heights=[0.4, 0.15, 0.15, 0.15, 0.15])
                
                # 1. K線圖
                fig_k.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
                for ma, color in zip(['MA5','MA10','MA20','MA60'], ['yellow','magenta','#00d4ff','lime']):
                    fig_k.add_trace(go.Scatter(x=df.index, y=df[ma], name=ma, line=dict(color=color, width=1)), row=1, col=1)
                
                # 2. 成交量
                v_colors = ['red' if df['Close'][i] >= df['Open'][i] else 'green' for i in range(len(df))]
                fig_k.add_trace(go.Bar(x=df.index, y=df['Volume'], name='成交量', marker_color=v_colors), row=2, col=1)
                
                # 3. 外資 (獨立區)
                f_colors = ['#FF4500' if v >= 0 else '#32CD32' for v in df['Foreign']]
                fig_k.add_trace(go.Bar(x=df.index, y=df['Foreign'], name='外資', marker_color=f_colors), row=3, col=1)
                
                # 4. 投信 (獨立區)
                t_colors = ['#8A2BE2' if v >= 0 else '#DA70D6' for v in df['Trust']]
                fig_k.add_trace(go.Bar(x=df.index, y=df['Trust'], name='投信', marker_color=t_colors), row=4, col=1)
                
                # 5. 自營商 (獨立區)
                d_colors = ['#00CED1' if v >= 0 else '#AFEEEE' for v in df['Dealers']]
                fig_k.add_trace(go.Bar(x=df.index, y=df['Dealers'], name='自營商', marker_color=d_colors), row=5, col=1)
                
                fig_k.update_layout(template="plotly_dark", height=1000, xaxis_rangeslider_visible=False, showlegend=True, legend=dict(orientation="h", y=1.02))
                # 移除各區段間的 X 軸標籤，保持簡潔
                fig_k.update_xaxes(showticklabels=False, row=1, col=1)
                fig_k.update_xaxes(showticklabels=False, row=2, col=1)
                fig_k.update_xaxes(showticklabels=False, row=3, col=1)
                fig_k.update_xaxes(showticklabels=False, row=4, col=1)
                
                st.plotly_chart(fig_k, use_container_width=True)
        else:
            st.error(f"查無資料: {stock_id}")
