import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 작업 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바 파일 업로드
st.sidebar.header("📁 팀별 작업일보 업로드")
heavy_file = st.sidebar.file_uploader("🚚 경남중량팀 일보", type=['xlsx'])
dock_file = st.sidebar.file_uploader("⚓ 경남하역팀 일보 (공유양식 적용)", type=['xlsx'])

# 3. 데이터 추출 엔진
def extract_data(file, team_name):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        # 엑셀을 헤더 없이 통째로 로드
        df = pd.read_excel(file, header=None)
        
        # 3-1. 이정표(Anchor) 위치 찾기 (A열 기준, 공백 제거 후 비교)
        def find_anchor(keyword):
            series = df.iloc[:, 0].astype(str).str.replace(" ", "")
            target = keyword.replace(" ", "")
            match = df[series == target].index
            return match[0] if not match.empty else None

        idx_w = find_anchor("[금일 작업]")
        idx_p = find_anchor("[예정 작업]")
        idx_a = find_anchor("[근태 현황]")

        # 3-2. 섹션별 종료 지점 계산
        all_indices = sorted([i for i in [idx_w, idx_p, idx_a, len(df)] if i is not None])
        def get_end(start):
            for i in all_indices:
                if i > start: return i
            return len(df)

        # 3-3. 데이터 추출 및 정제 함수 (정확히 일치하는 제목만 필터링)
        def clean_output(target_df, check_col):
            if target_df.empty: return target_df
            # 데이터가 아닌 제목줄 텍스트들 (정확히 일치할 때만 삭제)
            kill_list = ["nan", "None", "화주", "화주명", "작업구분", "작업 구분", "본선명", "구분", "구 분"]
            mask = target_df[check_col].astype(str).str.strip().apply(lambda x: x not in kill_list)
            return target_df[mask].reset_index(drop=True)

        # --- [금일 작업] ---
        if idx_w is not None:
            raw_w = df.iloc[idx_w+2:get_end(idx_w), :] # 제목줄 다음(+2)부터
            if "중량" in team_name:
                w_df = pd.DataFrame({
                    '팀명': team_name, '구분/화주': raw_w.iloc[:, 0], '작업내용': raw_w.iloc[:, 1], '비고': raw_w.iloc[:, 2]
                })
            else: # 하역팀 (공유양식: 화주6, 내용7, 비고9)
                w_df = pd.DataFrame({
                    '팀명': team_name, 
                    '구분/화주': raw_w.iloc[:, 6].fillna(raw_w.iloc[:, 0]), # 화주명 없으면 본선명 사용
                    '작업내용': raw_w.iloc[:, 7], 
                    '비고': raw_w.iloc[:, 9]
                })
            w_final = clean_output(w_df, '구분/화주')
        else: w_final = pd.DataFrame()

        # --- [예정 작업] ---
        if idx_p is not None:
            raw_p = df.iloc[idx_p+2:get_end(idx_p), :]
            if "중량" in team_name:
                p_df = pd.DataFrame({
                    '팀명': team_name, '구분/화주': raw_p.iloc[:, 0], '예정내용': raw_p.iloc[:, 1], '일정': raw_p.iloc[:, 2]
                })
            else: # 하역팀 (일정1, 화주6, 내용7, 비고9)
                p_df = pd.DataFrame({
                    '팀명': team_name, '구분/화주': raw_p.iloc[:, 6].fillna(raw_p.iloc[:, 0]),
                    '예정내용': raw_p.iloc[:, 7], '일정': raw_p.iloc[:, 1], '비고': raw_p.iloc[:, 9]
                })
            p_final = clean_output(p_df, '구분/화주')
        else: p_final = pd.DataFrame()

        # --- [근태 현황] ---
        if idx_a is not None:
            raw_a = df.iloc[idx_a+2:get_end(idx_a), [0, 1]].dropna(subset=[0])
            a_df = pd.DataFrame(raw_a.values, columns=['구분', '인원 현황'])
            a_df.insert(0, '팀명', team_name)
            a_final = clean_output(a_df, '구분')
        else: a_final = pd.DataFrame()

        return w_final, a_final, p_final

    except Exception:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 4. 데이터 로드 및 UI 출력
h_w, h_a, h_p = extract_data(heavy_file, "경남중량팀")
d_w, d_a, d_p = extract_data(dock_file, "경남하역팀")

tabs = st.tabs(["📊 종합 현황", "🚚 중량팀 상세", "⚓ 하역팀 상세"])

with tabs[0]:
    if heavy_file or dock_file:
        st.subheader("🗓️ 1. 전사 금일 작업")
        st.dataframe(pd.concat([h_w, d_w], ignore_index=True), use_container_width=True)
        st.subheader("👥 2. 전사 근태 현황")
        st.dataframe(pd.concat([h_a, d_a], ignore_index=True), use_container_width=True)
        st.subheader("📅 3. 전사 예정 작업")
        st.dataframe(pd.concat([h_p, d_p], ignore_index=True), use_container_width=True)
    else:
        st.info("사이드바에서 파일을 업로드해 주세요.")

with tabs[1]:
    st.write("### 중량팀 데이터", h_w, h_a, h_p)
with tabs[2]:
    st.write("### 하역팀 데이터", d_w, d_a, d_p)
