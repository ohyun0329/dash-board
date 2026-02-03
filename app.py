import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 작업 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바 파일 업로드
st.sidebar.header("📁 팀별 작업일보 업로드")
heavy_file = st.sidebar.file_uploader("🚚 경남중량팀 일보", type=['xlsx'])
logis_file = st.sidebar.file_uploader("📦 경남물류운영팀 일보", type=['xlsx'])
dock_file = st.sidebar.file_uploader("⚓ 경남하역팀 일보", type=['xlsx'])

# 3. 데이터 추출 엔진 (팀별 양식 자동 대응)
def extract_team_data(file, team_name):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        df = pd.read_excel(file, header=None)
        
        # 키워드 위치 찾기 (A열 우선 검색, 이후 전체 검색)
        def find_row(keywords):
            for kw in keywords:
                # 1. A열에서 먼저 찾기 (사용자 협의 사항)
                match = df[df.iloc[:, 0].astype(str).str.replace(" ", "").str.contains(kw.replace(" ", ""), na=False)].index
                if not match.empty: return match[0]
                # 2. 전체 열에서 찾기 (기존 양식 대비)
                for col in range(df.shape[1]):
                    match = df[df.iloc[:, col].astype(str).str.replace(" ", "").str.contains(kw.replace(" ", ""), na=False)].index
                    if not match.empty: return match[0]
            return None

        # 위치 추적
        idx_w = find_row(["[금일 작업]", "1. 본선 작업", "1. 금일 작업"])
        idx_p = find_row(["[예정 작업]", "2. 예정 작업", "3. 예정 작업"])
        idx_a = find_row(["[근태 현황]", "4. 근태 현황", "2. 근태 현황"])

        # --- 데이터 추출 로직 ---
        
        # 1. 금일 작업 (하역팀은 0번, 8번, 11번, 12번 열 사용)
        if idx_w is not None:
            raw = df.iloc[idx_w+2:idx_w+12, :].dropna(subset=[0, 8, 10], how='all')
            if "중량" in team_name:
                w_df = pd.DataFrame({
                    '팀명': team_name, '화주/본선': raw.iloc[:, 0], '작업내용': raw.iloc[:, 1],
                    '비고': raw.iloc[:, 14]
                })
            else: # 하역팀/물류팀 특화
                w_df = pd.DataFrame({
                    '팀명': team_name, 
                    '화주/본선': raw.iloc[:, 8].fillna(raw.iloc[:, 0]), # 화주명 우선, 없으면 본선명
                    '작업상세': raw.iloc[:, 11].astype(str) + " / " + raw.iloc[:, 12].astype(str), # 작업형태 + 투입인원
                    '비고': raw.iloc[:, 14]
                })
        else: w_df = pd.DataFrame()

        # 2. 근태 현황 (하역팀은 10번, 12번 열 사용)
        if idx_a is not None:
            if "하역" in team_name:
                raw_a = df.iloc[idx_a+1:idx_a+10, [10, 12]].dropna(subset=[10])
            else:
                raw_a = df.iloc[idx_a+2:idx_a+10, [0, 4]].dropna(subset=[0])
            a_df = pd.DataFrame(raw_a.values, columns=['구분', '현황'])
            a_df.insert(0, '팀명', team_name)
        else: a_df = pd.DataFrame()

        # 3. 예정 작업
        if idx_p is not None:
            raw_p = df.iloc[idx_p+2:idx_p+15, :].dropna(subset=[0, 8, 10], how='all')
            if "중량" in team_name:
                p_df = pd.DataFrame({
                    '팀명': team_name, '화주/본선': raw_p.iloc[:, 0], '예정내용': raw_p.iloc[:, 1], '일정': raw_p.iloc[:, 2]
                })
            else:
                p_df = pd.DataFrame({
                    '팀명': team_name, 
                    '화주/본선': raw_p.iloc[:, 8].fillna(raw_p.iloc[:, 0]),
                    '예정내용': raw_p.iloc[:, 11], '일정': raw_p.iloc[:, 2], '비고': raw_p.iloc[:, 14]
                })
        else: p_df = pd.DataFrame()

        # 공통 필터링 (제목줄 제거)
        def clean(d, col_idx):
            if d.empty: return d
            stop_words = ["화주", "본선", "구분", "내용", "입항", "nan", "None"]
            mask = d.iloc[:, col_idx].astype(str).apply(lambda x: not any(s in x for s in stop_words))
            return d[mask].reset_index(drop=True)

        return clean(w_df, 1), clean(a_df, 1), clean(p_df, 1)

    except Exception as e:
        st.error(f"{team_name} 처리 중 오류: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로드
h_w, h_a, h_p = extract_team_data(heavy_file, "경남중량팀")
l_w, l_a, l_p = extract_team_data(logis_file, "경남물류운영팀")
d_w, d_a, d_p = extract_team_data(dock_file, "경남하역팀")

# 탭 구성
tabs = st.tabs(["📊 종합 현황", "🚚 중량팀", "📦 물류팀", "⚓ 하역팀"])

with tabs[0]:
    if any([heavy_file, logis_file, dock_file]):
        st.subheader("🗓️ 1. 전사 금일 작업 현황")
        st.dataframe(pd.concat([h_w, l_w, d_w], ignore_index=True), use_container_width=True)
        st.subheader("👥 2. 전사 근태 현황")
        st.dataframe(pd.concat([h_a, l_a, d_a], ignore_index=True), use_container_width=True)
        st.subheader("📅 3. 전사 향후 예정 작업")
        st.dataframe(pd.concat([h_p, l_p, d_p], ignore_index=True), use_container_width=True)
    else: st.info("사이드바에서 파일을 업로드해 주세요.")

with tabs[1]: st.write("### 중량팀 상세", h_w, h_a, h_p)
with tabs[3]: st.write("### 하역팀 상세", d_w, d_a, d_p)
