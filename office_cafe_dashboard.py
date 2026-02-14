import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# 페이지 설정
st.set_page_config(
    page_title="오피스 상권 카페 창업 전략",
    page_icon="☕",
    layout="wide"
)

# 스타일링 (Premium Dark)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Pretendard', sans-serif; }
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    .main-title { font-size: 2.2rem; font-weight: 700; background: linear-gradient(90deg, #FFB74D, #FF8A65); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .metric-card { background-color: #1E2227; padding: 1.2rem; border-radius: 12px; border: 1px solid #30363D; text-align: center; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_master_data_v6():
    # v6: 세분화된 행정동 포함 (삼성1동, 삼성2동 등)
    path = 'dashboard_master_v6.parquet'
    if os.path.exists(path):
        df = pd.read_parquet(path)
        # 전체 순위 산출 (기회 지수 기준 내림차순)
        df['전체_순위'] = df['창업_기회_지수'].rank(ascending=False, method='min').astype(int)
        return df
    return pd.DataFrame()

df = load_master_data_v6()
total_dongs = len(df)

if df.empty:
    st.error("데이터(v6)를 찾을 수 없습니다. 파일 경로를 확인해주세요: dashboard_master_v6.parquet")
    st.stop()

# 사이드바
with st.sidebar:
    st.header("🔍 필터링 설정")
    # 평일 매출 비중 필터
    min_weekday_ratio = st.slider(
        "최소 평일 매출 비중 (%)",
        min_value=0,
        max_value=100,
        value=70,  # 기본값 70% (오피스 타겟)
        help="전체 매출 중 평일(월~금) 매출이 차지하는 최소 비중입니다."
    ) / 100.0

    st.markdown("---")
    st.header("🏢 상권 선택")
    
    # 데이터 필터링 적용
    filtered_df = df[df['평일_매출_비중'] >= min_weekday_ratio]
    
    if filtered_df.empty:
        st.warning(f"평일 비중 {min_weekday_ratio:.0%} 이상의 상권이 없습니다. 필터를 조절해주세요.")
        dong_list = []
    else:
        dong_list = sorted(filtered_df['표준_행정동_명'].unique())

    target_dong = st.selectbox("분석 대상 행정동", dong_list if dong_list else ["데이터 없음"])
    
    st.markdown("---")
    st.subheader(f"🏆 타겟팅 Top 10 (평일 {min_weekday_ratio:.0%}+)")
    # 필터링된 데이터 중 상위 10개 표시
    display_top10 = filtered_df.nsmallest(10, '전체_순위')[['전체_순위', '표준_행정동_명']] if not filtered_df.empty else pd.DataFrame()
    
    if not display_top10.empty:
        for _, row in display_top10.iterrows():
            st.write(f"**{row['전체_순위']}위** : {row['표준_행정동_명']}")
    else:
        st.write("해당 조건의 상권이 없습니다.")

st.markdown('<div class="main-title">오피스 상권 카페 창업 스카우터</div>', unsafe_allow_html=True)
st.markdown(f'<div style="color: #9E9E9E; margin-bottom: 20px;">서울시 {total_dongs}개 행정동 분석 기반 (Data v6 - 세분화 행정동 포함)</div>', unsafe_allow_html=True)

# 데이터 필터링 (정확한 매칭 확인)
selected_df = df[df['표준_행정동_명'] == target_dong]
if selected_df.empty:
    st.warning(f"'{target_dong}'에 대한 매칭 데이터를 찾을 수 없습니다.")
    st.stop()
selected_row = selected_df.iloc[0]

# KPI
c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.markdown(f'<div class="metric-card"><small>서울시 석차</small><br><b style="font-size:1.6rem; color:#FFB74D;">{selected_row["전체_순위"]}위</b><br><small>/{total_dongs}</small></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="metric-card"><small>기회 지수</small><br><b style="font-size:1.6rem;">{selected_row["창업_기회_지수"]:.1f}</b></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="metric-card"><small>오피스 종사자</small><br><b style="font-size:1.6rem;">{selected_row["총_종사자수"]:,}명</b></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="metric-card"><small>평일 매출 비중</small><br><b style="font-size:1.6rem; color:#64B5F6;">{selected_row["평일_매출_비중"]:.1%}</b></div>', unsafe_allow_html=True)
with c5: st.markdown(f'<div class="metric-card"><small>수혈 타임 비중</small><br><b style="font-size:1.6rem; color:#81C784;">{selected_row["수혈_시간대_매출_비중"]:.1%}</b></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 메인 콘텐츠
tab1, tab2, tab3, tab4 = st.tabs(["🚀 상권 정밀 분석", "📊 지수 산출 근거", "🔵 수요/공급 매트릭스", "📜 Top 10 리스트"])

with tab1:
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.subheader("⏰ 시간대별 매출 리듬")
        time_labels = ['00-06시', '06-11시', '11-14시', '14-17시', '17-21시', '21-24시']
        time_mapping = ['00~06', '06~11', '11~14', '14~17', '17~21', '21~24']
        time_values = [selected_row.get(f'시간대_{m}_매출_금액', 0) for m in time_mapping]
        fig_time = px.line(x=time_labels, y=time_values, markers=True, line_shape='spline')
        fig_time.update_traces(line_color='#FFB74D', line_width=4)
        fig_time.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#E0E0E0', xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_time, use_container_width=True)
    with col_t2:
        st.subheader("📅 요일별 수요 집중도")
        day_labels = ['월', '화', '수', '목', '금', '토', '일']
        day_values = [selected_row.get(f'{d}요일_매출_금액', 0) for d in day_labels]
        fig_day = px.bar(x=day_labels, y=day_values, color=day_values, color_continuous_scale='Oranges')
        fig_day.update_layout(showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#E0E0E0', xaxis_title="", yaxis_title="")
        st.plotly_chart(fig_day, use_container_width=True)

with tab2:
    st.subheader("🎯 기회 지수(Opportunity Index) 상세 분석")
    st.caption("기회 지수는 아래 4가지 핵심 요소의 서울시 내 상대적 위치(백분위)를 종합하여 산출됩니다.")
    
    # 레이더 차트 데이터
    categories = ['오피스 밀집도', '평일 매출 비중', '수혈 시간대 비중', '낮은 경쟁 강도']
    # 경쟁 강도는 카페 수가 적을수록 점수가 높으므로 1 - rank 적용 (혹은 역수)
    # 전처리 시 카페_수_rank는 카페가 많을수록 1에 가까움. 기배 추출 시 역수 활용했으므로 여기서도 보정.
    values = [
        selected_row['총_종사자수_rank'] * 100,
        selected_row['평일_매출_비중_rank'] * 100,
        selected_row['수혈_시간대_매출_비중_rank'] * 100,
        (1 - selected_row['카페_수_rank']) * 100
    ]
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(255, 183, 77, 0.3)',
        line_color='#FFB74D',
        name=target_dong
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color='#9E9E9E'),
            bgcolor='rgba(0,0,0,0)',
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#E0E0E0',
        height=500
    )
    
    c_r1, c_r2 = st.columns([1.5, 1])
    with c_r1:
        st.plotly_chart(fig_radar, use_container_width=True)
    with c_r2:
        st.markdown(f"""
        ### 🔍 {target_dong} 점수표
        - **오피스 밀집도**: {values[0]:.1f}점 (직장인 {selected_row['총_종사자수']:,}명)
        - **평일 매출 비중**: {values[1]:.1f}점 (매출의 {selected_row['평일_매출_비중']:.1%}가 주중 발생)
        - **수혈 시간대 비중**: {values[2]:.1f}점 (06~14시 매출 비중 {selected_row['수혈_시간대_매출_비중']:.1%})
        - **낮은 경쟁 강도**: {values[3]:.1f}점 (기존 카페 {selected_row['카페_수']:.0f}개 대비 잠재력)
        
        ---
        **[산출 공식]**
        `지수 = (오피스 밀집도/경쟁강도 * 0.4) + (평일 비중 * 0.3) + (수혈 비중 * 0.3)`
        """)

with tab3:
    st.subheader("🔵 블로오션 진단 (수요 vs 공급)")
    fig_scatter = px.scatter(df, x='카페_수', y='총_종사자수', size='창업_기회_지수', color='창업_기회_지수', 
                             hover_name='표준_행정동_명', color_continuous_scale='Viridis')
    fig_scatter.add_trace(go.Scatter(x=[selected_row['카페_수']], y=[selected_row['총_종사자수']],
                                     mode='markers+text', text=[f"★ {target_dong}"], 
                                     textposition="top center", marker=dict(color='red', size=15)))
    fig_scatter.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.02)', font_color='#E0E0E0')
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab4:
    st.subheader("📜 오피스 상권 유망 지역 Top 10")
    top10_full = df.nsmallest(10, '전체_순위')[['전체_순위', '표준_행정동_명', '창업_기회_지수', '총_종사자수', '평일_매출_비중', '카페_수']]
    top10_full.columns = ['순위', '행정동', '기회 지수', '직장인 수', '평일 매출 비중', '카페 수']
    st.dataframe(top10_full.style.format({'기회 지수': '{:.1f}', '직장인 수': '{:,}', '평일 매출 비중': '{:.1%}'}).background_gradient(subset=['기회 지수'], cmap='Oranges'), use_container_width=True)

st.markdown("---")
st.info(f"💡 **분석 결과**: **{target_dong}**은 서울시 {total_dongs}개 상권 중 기회 지수 **{selected_row['전체_순위']}위**를 기록한 핵심 요지입니다.")
