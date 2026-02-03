import streamlit as st
import pandas as pd

st.set_page_config(page_title="세방(주) 통합 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")

heavy_file = st.sidebar.file_uploader("🚚 경남중량팀 일보", type=['xlsx'])
dock_file = st.sidebar.file_uploader("⚓ 경남하역팀 일보 (공유양식)", type=['xlsx'])

def extract_team_data(file, team_name):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        df = pd.read_excel(file, header=None)
        
        # 키워드 위치 동적 검색 (공백 제거 후 비교)
        def find_row(keyword):
            mask = df.iloc[:, 0].astype(str).str.replace(" ", "").str.contains(keyword.replace(" ", ""), na=False)
            return df[mask].index[0] if not df[mask].empty else None

        idx_w = find_row("[금일 작업]")
        idx_p = find_row("[예정 작업]")
        idx_a = find_row("[근태 현황]")

        # 섹션 간 경계 자동 계산
        all_indices = sorted([i for i in [idx_w, idx_p, idx_a, len(df)] if i is not None])
        
        def get_end_idx(start_idx):
            for i in all_indices:
                if i > start_idx: return i
            return len(df)

        # 1. 금일 작업 (하역팀 전용 열: 화주6, 내용7, 인원8, 비고9)
        if idx_w is not None:
            raw_w = df.iloc[idx_w+2:get_end_idx(idx_w), :].dropna(subset=[0], how='all')
            if "중량" in team_name:
                w_df = pd.DataFrame({'팀명': team_name, '화주/본선': raw_w.iloc[:, 0], '작업내용': raw_w.iloc[:, 1], '관리자': raw_w.iloc[:, 2]})
            else:
                w_df = pd.DataFrame({
                    '팀명': team_name, '화주/본선': raw_w.iloc[:, 6].fillna(raw_w.iloc[:, 0]),
                    '작업내용': raw_w.iloc[:, 7], '투입인원': raw_w.iloc[:, 8], '비고': raw_w.iloc[:, 9]
                })
        else: w_df = pd.DataFrame()

        # 2. 예정 작업 (하역팀 전용 열: 일정1, 화주6, 내용7, 비고9)
        if idx_p is not None:
            raw_p = df.iloc[idx_p+2:get_end_idx(idx_p), :].dropna(subset=[0, 1], how='all')
            if "중량" in team_name:
                p_df = pd.DataFrame({'팀명': team_name, '화주/본선': raw_p.iloc[:, 0], '예정내용': raw_p.iloc[:, 1], '일정': raw_p.iloc[:, 2]})
            else:
                p_df = pd.DataFrame({
                    '팀명': team_name, '화주/본선': raw_p.iloc[:, 6].fillna(raw_p.iloc[:, 0]),
                    '예정내용': raw_p.iloc[:, 7], '일정': raw_p.iloc[:, 1], '비고': raw_p.iloc[:, 9]
                })
        else: p_df = pd.DataFrame()

        # 3. 근태 현황 (하역팀 공유양식: 구분0, 현황1)
        if idx_a is not None:
            raw_a = df.iloc[idx_a+2:get_end_idx(idx_a), [0, 1]].dropna(subset=[0])
            a_df = pd.DataFrame(raw_a.values, columns=['구분', '인원 현황'])
            a_df.insert(0, '팀명', team_name)
        else: a_df = pd.DataFrame()

        # 공통 정제 (불필요한 제목줄 삭제)
        def clean(d):
            if d.empty: return d
            stops = ["화주", "본선", "구분", "내용", "입항", "인원", "작업일보", "nan"]
            mask = d.iloc[:, 1].astype(str).apply(lambda x: not any(s in x for s in stops))
            return d[mask].reset_index(drop=True)

        return clean(w_df), a_df, clean(p_df)

    except Exception as e:
        st.error(f"오류 발생: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로드 및 출력
h_w, h_a, h_p = extract_team_data(heavy_file, "중량팀")
d_w, d_a, d_p = extract_team_data(dock_file, "하역팀")

tabs = st.tabs(["📊 종합 현황", "🚚 중량팀 상세", "⚓ 하역팀 상세"])

with tabs[0]:
    if heavy_file or dock_file:
        st.subheader("🗓️ 1. 전사 금일 작업")
        st.dataframe(pd.concat([h_w, d_w], ignore_index=True), use_container_width=True)
        st.subheader("👥 2. 전사 근태 현황")
        st.dataframe(pd.concat([h_a, d_a], ignore_index=True), use_container_width=True)
        st.subheader("📅 3. 전사 예정 작업")
        st.dataframe(pd.concat([h_p, d_p], ignore_index=True), use_container_width=True)
