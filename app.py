import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 작업 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바 파일 업로드
st.sidebar.header("📁 팀별 작업일보 업로드")
heavy_file = st.sidebar.file_uploader("🚚 경남중량팀 일보", type=['xlsx'])
dock_file = st.sidebar.file_uploader("⚓ 경남하역팀 일보", type=['xlsx'])

# 3. 데이터 추출 엔진 (필터링 강화 버전)
def extract_team_data_v2(file, team_name):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        df = pd.read_excel(file, header=None)
        
        # 키워드 위치 찾기 (A열 기준)
        def find_row(keyword):
            mask = df.iloc[:, 0].astype(str).str.replace(" ", "").str.contains(keyword.replace(" ", ""), na=False)
            match = df[mask].index
            return match[0] if not match.empty else None

        idx_w = find_row("[금일 작업]")
        idx_p = find_row("[예정 작업]")
        idx_a = find_row("[근태 현황]")

        # 데이터 범위 계산
        all_indices = sorted([i for i in [idx_w, idx_p, idx_a, len(df)] if i is not None])
        def get_end(s_idx):
            for i in all_indices:
                if i > s_idx: return i
            return len(df)

        # 공통 클리닝 함수 (대괄호 및 제목줄 삭제)
        def clean_data(d, col_idx):
            if d.empty: return d
            # 삭제할 키워드 리스트
            kill_list = ["[금일", "[예정", "[근태", "화주", "본선", "구분", "작업내용", "nan", "None"]
            mask = d.iloc[:, col_idx].astype(str).apply(
                lambda x: not any(k in x.replace(" ", "") for k in kill_list) and x.strip() != ""
            )
            return d[mask].reset_index(drop=True)

        # --- 1. 금일 작업 ---
        if idx_w is not None:
            # 키워드(0) -> 제목(1) -> 데이터(2) 이므로 +2부터 읽음
            raw_w = df.iloc[idx_w+2:get_end(idx_w), :]
            if "중량" in team_name:
                w_df = pd.DataFrame({
                    '팀명': team_name, '화주명': raw_w.iloc[:, 0], '작업내용': raw_w.iloc[:, 1], '관리자': raw_w.iloc[:, 2]
                })
            else: # 하역팀 (공유양식: 화주6, 내용7, 인원8, 비고9)
                w_df = pd.DataFrame({
                    '팀명': team_name, '화주/본선': raw_w.iloc[:, 6].fillna(raw_w.iloc[:, 0]),
                    '작업내용': raw_w.iloc[:, 7], '투입인원': raw_w.iloc[:, 8], '비고': raw_w.iloc[:, 9]
                })
            w_final = clean_data(w_df, 1)
        else: w_final = pd.DataFrame()

        # --- 2. 예정 작업 ---
        if idx_p is not None:
            raw_p = df.iloc[idx_p+2:get_end(idx_p), :]
            if "중량" in team_name:
                p_df = pd.DataFrame({
                    '팀명': team_name, '화주명': raw_p.iloc[:, 0], '예정내용': raw_p.iloc[:, 1], '일정': raw_p.iloc[:, 2]
                })
            else: # 하역팀 (일정1, 화주6, 내용7, 비고9)
                p_df = pd.DataFrame({
                    '팀명': team_name, '화주/본선': raw_p.iloc[:, 6].fillna(raw_p.iloc[:, 0]),
                    '예정내용': raw_p.iloc[:, 7], '일정': raw_p.iloc[:, 1], '비고': raw_p.iloc[:, 9]
                })
            p_final = clean_data(p_df, 1)
        else: p_final = pd.DataFrame()

        # --- 3. 근태 현황 ---
        if idx_a is not None:
            # 근태는 제목줄이 1줄인 경우가 많아 +1 혹은 +2 조절
            raw_a = df.iloc[idx_a+1:get_end(idx_a), [0, 1]].dropna(subset=[0])
            a_df = pd.DataFrame(raw_a.values, columns=['구분', '현황'])
            a_df.insert(0, '팀명', team_name)
            a_final = clean_data(a_df, 1)
        else: a_final = pd.DataFrame()

        return w_final, a_final, p_final

    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 실행 및 탭 구성
h_w, h_a, h_p = extract_team_data_v2(heavy_file, "중량팀")
d_w, d_a, d_p = extract_team_data_v2(dock_file, "하역팀")

tabs = st.tabs(["📊 종합 현황", "🚚 중량팀 상세", "⚓ 하역팀 상세"])

with tabs[0]:
    if heavy_file or dock_file:
        st.subheader("🗓️ 1. 전사 금일 작업")
        st.dataframe(pd.concat([h_w, d_w], ignore_index=True), use_container_width=True)
        st.subheader("👥 2. 전사 근태 현황")
        st.dataframe(pd.concat([h_a, d_a], ignore_index=True), use_container_width=True)
        st.subheader("📅 3. 전사 예정 작업")
        st.dataframe(pd.concat([h_p, d_p], ignore_index=True), use_container_width=True)
    else: st.info("파일을 업로드해 주세요.")

with tabs[1]:
    st.write("### 중량팀 상세", h_w, h_a, h_p)
with tabs[2]:
    st.write("### 하역팀 상세", d_w, d_a, d_p)
