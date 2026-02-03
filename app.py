import streamlit as st
import pandas as pd

# 1. 페이지 설정 및 디자인 (경남지사 명칭 적용)
st.set_page_config(page_title="세방(주) 경남지사 통합 관리", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    h1 { color: #003366; border-bottom: 2px solid #003366; padding-bottom: 10px; }
    .total-card { 
        background-color: #ffffff; padding: 20px; border-radius: 10px; 
        border-left: 5px solid #003366; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .merged-table { width: 100%; border-collapse: collapse; background: white; }
    .merged-table th { background-color: #003366; color: white; padding: 12px; border: 1px solid #ddd; }
    .merged-table td { padding: 10px; border: 1px solid #ddd; text-align: center; }
    .cat-cell { background-color: #f0f2f6; font-weight: bold; width: 120px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏗️ 세방(주) 경남지사 통합 작업 관리 시스템")

# 2. 사이드바 파일 업로드
st.sidebar.header("📁 팀별 일보 업로드")
heavy_file = st.sidebar.file_uploader("🚚 경남중량팀", type=['xlsx'])
dock_file = st.sidebar.file_uploader("⚓ 경남하역팀", type=['xlsx'])

# 3. 데이터 추출 엔진
def extract_data_final(file, team_name):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    try:
        df = pd.read_excel(file, header=None)
        
        # 키워드 위치 찾기 함수
        def find_anchor(kw):
            clean_kw = kw.replace(" ", "")
            for col in range(min(df.shape[1], 2)): # A, B열 검색
                mask = df.iloc[:, col].astype(str).str.replace(" ", "").str.contains(clean_kw, na=False)
                if mask.any(): return df[mask].index[0]
            return None

        # 정확한 인덱스 찾기
        idx_w = find_anchor("[금일작업]")
        idx_p = find_anchor("[예정작업]")
        idx_a = find_anchor("[근태현황]")
        
        all_idxs = sorted([i for i in [idx_w, idx_p, idx_a, len(df)] if i is not None])
        def get_end(s):
            for i in all_idxs:
                if i > s: return i
            return len(df)

        # 공통 정제 함수
        def clean_df(target_df, check_col):
            if target_df.empty: return target_df
            # 제목이나 구분자 줄
