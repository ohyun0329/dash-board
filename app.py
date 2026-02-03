import streamlit as st
import pandas as pd

st.set_page_config(page_title="세방(주) 통합 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# ... (사이드바 및 extract_data 함수는 이전과 동일) ...

# 4. 데이터 로드 후 출력 부분
h_w, h_a, h_p = extract_data(heavy_file, "경남중량팀")
d_w, d_a, d_p = extract_data(dock_file, "경남하역팀")

tabs = st.tabs(["📊 종합 현황", "🚚 중량팀 상세", "⚓ 하역팀 상세"])

with tabs[0]:
    if heavy_file or dock_file:
        st.subheader("🗓️ 1. 전사 금일 작업")
        st.dataframe(pd.concat([h_w, d_w], ignore_index=True), use_container_width=True)
        
        st.divider()
        st.subheader("👥 2. 전사 근태 현황")
        total_att = pd.concat([h_a, d_a], ignore_index=True)
        
        if not total_att.empty:
            # 순서 정렬 (작업 -> 내무 -> 출장 -> 휴가)
            sort_order = {'작업': 0, '내무': 1, '출장': 2, '휴가': 3}
            total_att['order'] = total_att['구분'].map(sort_order)
            # 팀명과 구분을 기준으로 정렬 (그래야 뭉쳐 보임)
            total_att = total_att.sort_values(['order', '팀명']).drop('order', axis=1)
            
            # --- ✨ 시각적 병합 효과: 중복되는 '구분'은 빈칸 처리 ---
            # 사용자님, 엑셀을 병합하는 대신 출력할 때만 첫 줄 빼고 글자를 숨기는 방식입니다.
            display_att = total_att.copy()
            mask = display_att['구분'].duplicated()
            display_att.loc[mask, '구분'] = "" # 중복된 '작업', '내무' 등은 숨김
            
            st.table(display_att) # dataframe보다 table이 병합 느낌을 주기 좋습니다.
        
        st.divider()
        st.subheader("📅 3. 전사 예정 작업")
        st.dataframe(pd.concat([h_p, d_p], ignore_index=True), use_container_width=True)
