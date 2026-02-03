import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 작업 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바 파일 업로드
st.sidebar.header("📁 팀별 작업일보 업로드")
heavy_file = st.sidebar.file_uploader("경남중량팀 일보 ([금일 작업] 등 적용)", type=['xlsx'])
logis_file = st.sidebar.file_uploader("경남물류운영팀 일보", type=['xlsx'])
dock_file = st.sidebar.file_uploader("경남하역팀 일보", type=['xlsx'])

# 3. 데이터 추출 핵심 함수 (키워드 이정표 방식)
def extract_team_data(file, team_name):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        df = pd.read_excel(file, header=None)
        
        def get_eq(row, a_idx, p_idx, label):
            try:
                a = pd.to_numeric(row.iloc[a_idx], errors='coerce')
                p = pd.to_numeric(row.iloc[p_idx], errors='coerce')
                if a > 0: return f"{label}({int(a)}축, {int(p)}P.P)"
            except: pass
            return ""

        # 키워드 위치 찾기
        def find_row(keyword):
            match = df[df.iloc[:, 0].astype(str).str.contains(keyword, na=False, regex=False)].index
            return match[0] if not match.empty else None

        idx_w = find_row("[금일 작업]")
        idx_a = find_row("[근태 현황]")
        idx_p = find_row("[예정 작업]")

        # --- 1. 금일 작업 ---
        if idx_w is not None:
            start = idx_w + 2
            end = idx_a if idx_a else start + 10
            raw = df.iloc[start:end, :].dropna(subset=[0])
            w_df = pd.DataFrame({
                '팀명': team_name,
                '화주명': raw.iloc[:, 0].astype(str).str.strip(),
                '작업내용': raw.iloc[:, 1].astype(str).str.strip(),
                '관리자': raw.iloc[:, 2].astype(str).str.strip(),
                '비고': raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
            })
        else: w_df = pd.DataFrame()

        # --- 2. 근태 현황 ---
        if idx_a is not None:
            start = idx_a + 2
            end = idx_p if idx_p else start + 8
            raw = df.iloc[start:end, [0, 1, 4]].dropna(subset=[0])
            a_df = pd.DataFrame(raw.values, columns=['구분', '관리자', '현황'])
            a_df.insert(0, '팀명', team_name)
        else: a_df = pd.DataFrame()

        # --- 3. 예정 작업 ---
        if idx_p is not None:
            start = idx_p + 2
            raw = df.iloc[start:, :].dropna(subset=[0])
            p_df = pd.DataFrame({
                '팀명': team_name,
                '화주명': raw.iloc[:, 0].astype(str).str.strip(),
                '예정내용': raw.iloc[:, 1].astype(str).str.strip(),
                '예정일정': raw.iloc[:, 2].astype(str).str.strip(),
                '비고': raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
            })
        else: p_df = pd.DataFrame()

        # 제목줄 필터링
        def clean(d, col):
            if d.empty: return d
            return d[~d[col].str.contains("화주|구분|내용", na=False)].reset_index(drop=True)

        return clean(w_df, '화주명'), a_df, clean(p_df, '화주명')

    except Exception as e:
        st.error(f"{team_name} 처리 중 오류: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로드
h_w, h_a, h_p = extract_team_data(heavy_file, "경남중량팀")
l_w, l_a, l_p = extract_team_data(logis_file, "경남물류운영팀")
d_w, d_a, d_p = extract_team_data(dock_file, "경남하역팀")

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["📊 종합 현황", "🚚 경남중량팀", "📦 경남물류운영팀", "⚓ 경남하역팀"])

with tab1:
    if heavy_file or logis_file or dock_file:
        st.subheader("🗓️ 1. 전사 금일 작업 현황")
        st.dataframe(pd.concat([h_w, l_w, d_w], ignore_index=True), use_container_width=True)
        st.divider()
        st.subheader("👥 2. 전사 근태 현황")
        st.dataframe(pd.concat([h_a, l_a, d_a], ignore_index=True), use_container_width=True)
    else:
        st.info("사이드바에서 파일을 업로드해 주세요.")

with tab2:
    st.subheader("🚚 경남중량팀 상세")
    st.write("금일 작업", h_w)
    st.write("향후 예정", h_p)

with tab3:
    st.subheader("📦 경남물류운영팀 상세")
    st.write("금일 작업", l_w)

with tab4:
    st.subheader("⚓ 경남하역팀 상세")
    st.write("금일 작업", d_w)
