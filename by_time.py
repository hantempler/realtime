import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="주식 위임 현황", layout="wide")
st.title("📊 주식 위임 집계 현황")

FIXED_ORDER = [
    '박상문', '임재일', '김영철', '박광근', '김정준', 
    '신정엽', '이진홍', '유영근', '전문수', '김병남', 
    '김택현', '윤덕화', '노호성'
]

uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx"])

if uploaded_file:
    try:
        # 데이터 로드
        df = pd.read_excel(uploaded_file)
        
        # 전처리
        df = df.dropna(subset=['날짜', '방문한 직원']) 
        df['날짜'] = pd.to_datetime(df['날짜']).dt.strftime('%Y-%m-%d')
        df['시간_tmp'] = pd.to_datetime(df['시간'], format='%H:%M', errors='coerce').dt.hour.fillna(0).astype(int)
        df['위임받은 주식의 수'] = pd.to_numeric(df['위임받은 주식의 수'], errors='coerce').fillna(0)
        
        # 담당자 순서 고정
        df['방문한 직원'] = pd.Categorical(df['방문한 직원'], categories=FIXED_ORDER, ordered=True)

        # 06시부터 시작하는 시간대 설정
        bins = range(6, 26, 2) 
        labels = [f"{i:02d}-{i+2:02d}" for i in range(6, 24, 2)]
        df['시간대'] = pd.cut(df['시간_tmp'], bins=bins, labels=labels, right=False)

        # --- 데이터 계산 ---
        
        # [A] 당일 시간대별 상세 피벗
        pivot_daily = df.pivot_table(
            index=['날짜', '방문한 직원'], 
            columns='시간대', 
            values='위임받은 주식의 수', 
            aggfunc='sum', 
            fill_value=0,
            observed=False
        )
        pivot_daily['당일 소계'] = pivot_daily.sum(axis=1)

        # [B] 누적 계산용 피벗
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

        # 섹션 1: 시간대별 상세 현황 (색상 제거, 숫자 강조)
        st.markdown(f"### 🔍 {selected_date} 시간대별 상세 (06:00 ~ 24:00)")
        
        # 숫자에 콤마를 넣어 도드라져 보이게 포맷팅
        st.dataframe(
            pivot_daily.loc[selected_date].style.format("{:,.0f}"),
            use_container_width=True
        )

        st.divider()

        # 섹션 2: 요약 표 및 차트
        st.markdown(f"### 🏆 {selected_date} 기준 인원별 실적 (당일 vs 전체누적)")
        
        summary_comp = pd.DataFrame({
            '당일 실적': pivot_for_cum.loc[selected_date],
            '전체 누적 실적': cumulative_df.loc[selected_date]
        }).sort_values(by='전체 누적 실적', ascending=False)
        
        col_table, col_chart = st.columns([1, 1.2])
        
        with col_table:
            # 일반 테이블 형태로 숫자만 깔끔하게 출력
            st.table(summary_comp.style.format("{:,.0f}"))
        
        with col_chart:
            # 누적 실적 막대 그래프 (색상 없이 기본 차트)
            st.bar_chart(summary_comp['전체 누적 실적'])

    except Exception as e:
        st.error(f"⚠️ 오류 발생: {e}")
else:
    st.info("엑셀 파일을 업로드해주세요.")
