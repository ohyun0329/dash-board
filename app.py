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

# 3. 데이터 추출 엔진 (공유해주신 새 양식 최적화)
def extract_team_data(file, team_name):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        df = pd.read_excel(file, header=None)
        
        # 키워드 위치 찾기 (A열 검색)
        def find_row(keyword):
            mask = df.iloc[:, 0].astype(str).str.replace(" ", "").str.contains(keyword.replace(" ", ""), na=False)
            match = df[mask].index
            return match[0] if not match.empty else None

        idx_w = find_row("[금일 작업]")
        idx_p = find_row("[예정 작업]")
        idx_a = find_row("[근태 현황]")

        # 데이터 범위 설정을 위한 인덱스 리스트 (정렬)
        indices = sorted(filter(lambda x: x is not None, [idx_w, idx_p, idx_a, len(df)]))
        
        def get_range_end(start_idx):
            for i in indices:
                if i > start_idx: return i
            return len(df)

        # --- 1. 금일 작업 추출 ---
        if idx_w is not None:
            end = get_range_end(idx_w)
            raw_w = df.iloc[idx_w+2:end, :].dropna(subset=[0], how='all')
            if "중량" in team_name:
                # 중량팀 기존 열 구조 유지
                w_df = pd.DataFrame({
                    '팀명': team_name, '화주/본선': raw_w.iloc[:, 0], '작업내용': raw_w.iloc[:, 1], '관리자': raw_w.iloc[:, 2]
                })
            else: # 하역팀 (공유해주신 양식 열 번호: 화주6, 내용7, 인원8, 비고9)
                w_df = pd.DataFrame({
                    '팀명': team_name, 
                    '화주/본선': raw_w.iloc[:, 6].fillna(raw_w.iloc[:, 0]), # 화주명 우선, 없으면 본선명
                    '작업내용': raw_w.iloc[:, 7], 
                    '투입인원': raw_w.iloc[:, 8],
                    '비고': raw_w.iloc[:, 9]
                })
        else: w_df = pd.DataFrame()

        # --- 2. 예정 작업 추출 ---
        if idx_p is not None:
            end = get_range_end(idx_p)
            raw_p = df.iloc[idx_p+2:end, :].dropna(subset=[0, 6], how='all')
            if "중량" in team_name:
                p_df = pd.DataFrame({
                    '팀명': team_name, '화주/본선': raw_p.iloc[:, 0], '예정내용': raw_p.iloc[:, 1], '일정': raw_p.iloc[:, 2]
                })
            else: # 하역팀 (본선0, 일정1, 화주6, 내용7, 비고9)
                p_df = pd.DataFrame({
                    '팀명': team_name,
                    '화주/본선': raw_p.iloc[:, 6].fillna(raw_p.iloc[:, 0]),
                    '예정내용': raw_p.iloc[:, 7],
                    '예정일정': raw_p.iloc[:, 1],
                    '비고': raw_p.iloc[:, 9]
                })
        else: p_df = pd.DataFrame()

        # --- 3. 근태 현황 추출 ---
        if idx_a is not None:
            end = get_range_end(idx_a)
            raw_a = df.iloc[idx_a+2:end, [0, 1]].dropna(subset=[0])
            a_df = pd.DataFrame(raw_a.values, columns=['구분', '인원 현황'])
            a_df.insert(0, '팀명', team_name)
        else: a_df = pd.DataFrame()

        # 공통 필터링
        def clean(d):
            if d.empty: return d
            # 제목줄이 데이터로 들어온 경우 삭제
            stop_words = ["화주", "본선", "구분", "내용", "입항", "인원", "작업일보"]
            mask = d.iloc[:, 1].astype(str).apply(lambda x: not any(s in x for s in stop_words))
            return d[mask].reset_index(drop=True)

        return clean(w_df), a_df, clean(p_df)

    except Exception as e:
        st.error(f"{team_name} 처리 중 오류: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로드
h_w, h_a, h_p = extract_team_data(heavy_file, "경남중량팀")
d_w, d_a, d_p = extract_team_data(dock_file, "경남하역팀")

# 탭 구성
tabs = st.tabs(["📊 종합 현황", "🚚 중량팀 상세", "⚓ 하역팀 상세"])

with tabs[0]:
    if heavy_file or dock_file:
        st.subheader("🗓️ 1. 전사 금일 작업")
        st.dataframe(pd.concat([h_w, d_w], ignore_index=True), use_container_width=True)
        st.subheader("👥 2. 전사 근태 현황")
        st.dataframe(pd.concat([h_a, d_a], ignore_index=True), use_container_width=True)
        st.subheader("📅 3. 전사 향후 예정")
        st.dataframe(pd.concat([h_p, d_p], ignore_index=True), use_container_width=True)
    else: st.info("사이드바에서 파일을 업로드해 주세요.")

with tabs[1]:
    st.subheader("🚚 경남중량팀 상세")
    st.write("금일 작업", h_w)
    st.write("근태 현황", h_a)
    st.write("예정 작업", h_p)

with tabs[2]:
    st.subheader("⚓ 경남하역팀 상세")
    st.write("금일 작업", d_w)
    st.write("근태 현황", d_a)
    st.write("예정 작업", d_p)
