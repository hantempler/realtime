import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="집계현황", layout="wide")
st.title("📈시간별집계")

# 담당자 고정 순서
FIXED_ORDER = [
    '박상문', '임재일', '김영철', '박광근', '김정준', 
    '신정엽', '이진홍', '유영근', '전문수', '김병남', 
    '김택현', '윤덕화', '노호성'
]

FILE_PATH = 'https://drive.google.com/uc?export=download&id=1nB0o2BlZiKqDrMCIQ_uAGGaiYNxTR_AM'

# @st.cache_data(ttl=600)
def load_data(url):
    return pd.read_excel(url, engine='openpyxl')

try:
    df = load_data(FILE_PATH)
    
    # --- 데이터 전처리 ---
    df = df.dropna(subset=['날짜', '방문한 직원']) 
    df['날짜'] = pd.to_datetime(df['날짜']).dt.strftime('%Y-%m-%d')
    df['시간_tmp'] = pd.to_datetime(df['시간'], format='%H:%M', errors='coerce').dt.hour.fillna(0).astype(int)
    df['위임받은 주식의 수'] = pd.to_numeric(df['위임받은 주식의 수'], errors='coerce').fillna(0)
    
    df['방문한 직원'] = pd.Categorical(df['방문한 직원'], categories=FIXED_ORDER, ordered=True)

    bins = range(6, 26, 2) 
    labels = [f"{i:02d}시-{i+2:02d}시" for i in range(6, 24, 2)]
    df['시간대'] = pd.cut(df['시간_tmp'], bins=bins, labels=labels, right=False)

    # --- 데이터 계산 ---
    
    # [A] 당일 시간대별 피벗
    pivot_daily = df.pivot_table(
        index=['날짜', '방문한 직원'], 
        columns='시간대', 
        values='위임받은 주식의 수', 
        aggfunc='sum', 
        fill_value=0,
        observed=False
    )

    # [B] 누적 계산용 피벗 (날짜별)
    pivot_for_cum = df.pivot_table(
        index='날짜',
        columns='방문한 직원',
        values='위임받은 주식의 수',
        aggfunc='sum', 
        fill_value=0,
        observed=False
    ).sort_index()
    
    cumulative_df = pivot_for_cum.cumsum(axis=0)

    # --- UI 출력 ---
    available_dates = sorted(df['날짜'].unique())
    selected_date = st.selectbox("📅 조회 날짜 선택", available_dates, index=len(available_dates)-1)

    # 요약 지표 계산
    total_today = pivot_for_cum.loc[selected_date].sum()
    total_cumulative = cumulative_df.loc[selected_date].sum()

    st.divider()
    col_m1, col_m2 = st.columns(2)
    col_m1.metric(label=f"📅 {selected_date} 당일 총계", value=f"{total_today:,.0f} 주")
    col_m2.metric(label=f"🚀 프로젝트 누적 총계", value=f"{total_cumulative:,.0f} 주")
    st.divider()

    # --- 섹션 1: 시간대별 상세 및 시간대별 누적 합계 ---
    st.subheader(f"🔍 {selected_date} 시간대별 집계")
    
    daily_display = pivot_daily.xs(selected_date, level='날짜', drop_level=True)
    
    # 행 합계(담당자별 총합) 추가
    daily_display['담당자 총합'] = daily_display.sum(axis=1)
    
    # 열 합계(시간대별 총합) 및 **시간대별 누적 합계** 계산
    time_sum = daily_display.drop(columns='담당자 총합').sum(axis=0)
    # time_cumulative = time_sum.cumsum() # 시간대별로 누적해서 더함
    
    # 합계 및 누적 행을 데이터프레임 하단에 붙이기
    footer = pd.DataFrame([time_sum], index=['시간대별 합계'])
    # 담당자 총합 열에 해당하는 빈 칸 채우기 (마지막 누적값 유지)
    footer['담당자 총합'] = [time_sum.sum()]
    
    daily_final = pd.concat([daily_display, footer])

    st.dataframe(daily_final.style.format("{:,.0f}"), use_container_width=True)

    # # --- 섹션 2: 성과 요약 ---
    # st.divider()
    # st.subheader(f"🏆 {selected_date}누적 현황")
    
    # summary_comp = pd.DataFrame({
    #     '당일 실적': pivot_for_cum.loc[selected_date],
    #     '전체 누적 실적': cumulative_df.loc[selected_date]
    # }).sort_values(by='전체 누적 실적', ascending=False)
    
    # # 총 합계 행 추가
    # summary_total = pd.DataFrame({
    #     '당일 실적': [total_today],
    #     '전체 누적 실적': [total_cumulative]
    # }, index=['총 합계'])
    # summary_final = pd.concat([summary_comp, summary_total])
    
    # col_table, col_chart = st.columns([1, 1.2])
    # with col_table:
    #     st.dataframe(summary_final.style.format("{:,.0f}"), use_container_width=True)


except Exception as e:
    st.error(f"⚠️ 오류 발생: {e}")
