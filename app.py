import streamlit as st
from pykrx import stock
import pandas as pd
import plotly.graph_objects as go
import datetime

# ---1. 기본셋팅
st.set_page_config(
    page_title = "주식 차트",
    page_icon = "📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---2. 사이드바(주식 종목 선택)
st.sidebar.markdown("## 주식 종목 선택")
today = datetime.date.today()
tickers = stock.get_market_ticker_list(market = "ALL", date = today.strftime("%Y%m%d"))
ticker_names = [stock.get_market_ticker_name(t) for t in tickers]
ticker_dict = dict(zip(ticker_names, tickers))
select_name = st.sidebar.selectbox("종목 선택", ticker_names, index = ticker_names.index("삼성전자"))
select_ticker = ticker_dict[select_name]

date_from = st.sidebar.date_input("시작일", today - datetime.timedelta(days=365))
date_to = st.sidebar.date_input("종료일", today)
date_from_str = date_from.strftime("%Y%m%d")
date_to_str = date_to.strftime("%Y%m%d")

st.sidebar.markdown("---")

# ---3. 주식 데이터 가져오기
@st.cache_data(show_spinner=False)
def get_data(ticker, start, end):
    df = stock.get_market_ohlcv_by_date(start, end, ticker)
    df_fund = stock.get_market_fundamental_by_date(start, end, ticker)
    df_all = df.merge(df_fund, left_index=True, right_index=True)
    df_all.index = pd.to_datetime(df_all.index)
    return df_all

with st.spinner("주식 데이터를 가져오는 중..."):
    data = get_data(select_ticker, date_from_str, date_to_str)


# ---- 4. 메인 레이아웃(기업형)
st.markdown(f"""
# <span style="color:#5055fd;font-size:2.2rem;">{select_name} ({select_ticker})</span> Dashboard  
<div style='color:#aaa;'>기업/스타트업을 위한 실시간 대시보드</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([2,1,1])

with col1:
    st.markdown("### 📈 시세 & 거래량 차트")
    fig1 = go.Figure()
    fig1.add_trace(go.Candlestick(
        x=data.index, open=data['시가'], high=data['고가'],
        low=data['저가'], close=data['종가'], name="주가"))
    fig1.add_trace(go.Bar(
        x=data.index, y=data['거래량'], name='거래량', yaxis='y2',
        marker=dict(opacity=0.3, color='#64b5f6')))
    fig1.update_layout(
        xaxis_rangeslider_visible=False,
        yaxis=dict(title='주가(원)', side='left'),
        yaxis2=dict(title='거래량', overlaying='y', side='right', showgrid=False),
        legend=dict(orientation='h'), height=420, margin=dict(t=25,b=25,l=10,r=10))
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("### 💡 주요 재무지표")
    st.metric("PER", f"{data['PER'][-1]:.2f}")
    st.metric("PBR", f"{data['PBR'][-1]:.2f}")
    st.metric("EPS", f"{data['EPS'][-1]:,.0f}")
    st.metric("BPS", f"{data['BPS'][-1]:,.0f}")
    st.metric("배당수익률(%)", f"{data['DIV'][-1]:.2f}")
    st.metric("DPS", f"{data['DPS'][-1]:,.0f}")

with col3:
    st.markdown("### 🏦 시가총액/거래 정보")
    cap_df = stock.get_market_cap_by_ticker(date_to_str)
    st.metric("시가총액(억원)", f"{cap_df.loc[select_ticker,'시가총액'] // 100000000:,}")
    st.metric("상장주식수", f"{cap_df.loc[select_ticker,'상장주식수']:,}")
    st.metric("52주 최고가", f"{data['고가'][-252:].max():,.0f}")
    st.metric("52주 최저가", f"{data['저가'][-252:].min():,.0f}")

st.markdown("---")

# ---- 5. 세부 차트/분석 (Tabs)
tab1, tab2, tab3, tab4 = st.tabs(["📉 가격/재무추이", "📊 공매도/거래", "🧮 멀티종목 비교", "📝 Raw Data"])

with tab1:
    st.subheader("가격·재무지표 트렌드")
    st.line_chart(data[["종가", "PER", "PBR"]])
    st.bar_chart(data[["EPS", "BPS"]])
    st.area_chart(data[["DIV"]])

with tab2:
    st.subheader("공매도/거래 분석")
    # 공매도 데이터 예시
    from pykrx.stock import get_shorting_volume_by_date
    shorting = get_shorting_volume_by_date(date_from_str, date_to_str, select_ticker)
    if len(shorting) > 0:
        # st.write(shorting.head())  # 컬럼명 확인용, 한 번만 실행해보세요
        st.line_chart(shorting["공매도"])  # 또는 실제 컬럼명
    else:
        st.info("공매도 데이터 없음.")

with tab3:
    st.subheader("종목 비교")
    # 2개 종목 선택해서 종가 비교
    compare_names = st.multiselect("비교할 종목 2~3개 선택", ticker_names, default=[select_name, "LG에너지솔루션"] if "LG에너지솔루션" in ticker_names else [select_name])
    for comp_name in compare_names:
        comp_ticker = ticker_dict[comp_name]
        comp_data = get_data(comp_ticker, date_from_str, date_to_str)
        st.line_chart(comp_data['종가'].rename(comp_name))

with tab4:
    st.subheader("원본 데이터")
    st.dataframe(data.tail(50), use_container_width=True)

# ---- 6. 푸터/스타트업스러운 디자인
st.markdown("""
<style>
[data-testid="stSidebar"] {background-color: #f6f7fb;}
.big-font {font-size:2.2rem; font-weight:700; color:#5055fd;}
.stMetric {border-radius: 1rem; border:1px solid #eaeaea;}
</style>
""", unsafe_allow_html=True)

st.caption("🚀 Powered by pykrx, Streamlit, Plotly | 디자인 및 개발: 하재욱")