import streamlit as st
import pandas as pd
import os

# 1. 페이지 설정
st.set_page_config(page_title="주식 위임 현황", layout="wide")

# CSS: 테이블 간격 및 디자인 최적화
st.markdown("""
    <style>
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    td, th { padding: 2px 8px !important; font-size: 14px; text-align: center !important; }
    tr { line-height: 1.1 !important; }
    div[data-testid="stTable"] { width: fit-content; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 실시간 주식 위임 집계 현황")

# --- [수정] 파일 경로 자동 지정 ---
FILE_PATH = 'matched_result.xlsx'

# 파일 존재 여부 확인 후 로드
if os.path.exists(FILE_PATH):
    try:
        # 데이터 로드
        df = pd.read_excel(FILE_PATH)
        
        # [데이터 전처리]
        df = df.dropna(subset=['날짜', '방문한 직원']) 
        df['날짜'] = pd.to_datetime(df['날짜']).dt.strftime('%Y-%m-%d')
        df['시간_tmp'] = pd.to_datetime(df['시간'], format='%H:%M', errors='coerce').dt.hour.fillna(0).astype(int)
        df['위임받은 주식의 수'] = pd.to_numeric(df['위임받은 주식의 수'], errors='coerce').fillna(0)
        
        fixed_order = ['박상문', '임재일', '김영철', '박광근', '김정준', '신정엽', '이진홍', '유영근', '전문수', '김병남', '김택현', '윤덕화', '노호성']
        df['방문한 직원'] = pd.Categorical(df['방문한 직원'], categories=fixed_order, ordered=True)

        # 시간대 설정 (06:00 시작)
        bins = range(6, 26, 2) 
        labels = [f"{i:02d}-{i+2:02d}" for i in range(6, 24, 2)]
        df['시간대'] = pd.cut(df['시간_tmp'], bins=bins, labels=labels, right=False)

        # --- 데이터 계산 ---
        pivot_daily = df.pivot_table(index=['날짜', '방문한 직원'], columns='시간대', 
                                    values='위임받은 주식의 수', aggfunc='sum', fill_value=0, observed=False)
        pivot_daily['당일 소계'] = pivot_daily.sum(axis=1)

        pivot_for_cum = df.pivot_table(index='날짜', columns='방문한 직원', 
                                      values='위임받은 주식의 수', aggfunc='sum', fill_value=0, observed=False).sort_index()
        cumulative_df = pivot_for_cum.cumsum(axis=0)

        # --- UI 출력 ---
        available_dates = sorted(df['날짜'].unique())
        selected_date = st.selectbox("📅 조회 날짜 선택", available_dates, index=len(available_dates)-1)

        # 섹션 1: 상세 현황
        st.markdown(f"##### 🔍 {selected_date} 시간대별 상세 (06:00 ~ 24:00)")
        st.table(pivot_daily.loc[selected_date].style.format("{:,.0f}"))

        # 섹션 2: 누적 성과
        st.divider()
        st.markdown(f"##### 🏆 {selected_date} 기준 누적 실적 현황")
        
        summary_comp = pd.DataFrame({
            '당일 실적': pivot_for_cum.loc[selected_date],
            '전체 누적 실적': cumulative_df.loc[selected_date]
        }).sort_values(by='전체 누적 실적', ascending=False)
        
        col_table, col_chart = st.columns([1, 1.5])
        with col_table:
            st.table(summary_comp.style.format("{:,.0f}"))
        with col_chart:
            st.bar_chart(summary_comp['전체 누적 실적'], height=350)

    except Exception as e:
        st.error(f"⚠️ 데이터를 처리하는 중 오류가 발생했습니다: {e}")
else:
    st.warning(f"'{FILE_PATH}' 파일을 찾을 수 없습니다. 서버의 실행 경로를 확인해주세요.")
