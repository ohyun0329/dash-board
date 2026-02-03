import streamlit as st
import pandas as pd

# 1. 페이지 설정 및 디자인
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
    .merged-table { width: 100%; border-collapse: collapse; background: white; margin-bottom: 20px; table-layout: fixed; }
    .merged-table th { 
        background-color: #003366; color: white; padding: 12px; border: 1px solid #ddd; 
        text-align: center !important; vertical-align: middle !important;
    }
    .merged-table td { padding: 10px; border: 1px solid #ddd; text-align: center; vertical-align: middle; word-break: break-all; }
    .first-col { background-color: #f0f2f6; font-weight: bold; width: 150px !important; }
    .status-cell { width: 35%; }
    </style>
""", unsafe_allow_html=True)

st.title("🏗️ 세방(주) 경남지사 통합 작업 관리 시스템")

# 2. 구글 시트 연결 주소
SHEET_URLS = {
    "경남중량팀": "https://docs.google.com/spreadsheets/d/1yyfSsY7MEeOQkli8NL1Hd_A_ufpCU9_5EQufv4eLzD8/export?format=xlsx",
    "경남하역팀": "https://docs.google.com/spreadsheets/d/11mNUhbw3h_YUSUX_VugWiiNF4cQLMCFOVtQhJ6arkBU/export?format=xlsx",
    "경남물류운영팀": "https://docs.google.com/spreadsheets/d/1RY1Eevut6CTLR3r8g9OFXz4ZePkGRjE0LaclSjYMb_s/export?format=xlsx"
}

def count_names(val):
    val_str = str(val)
    if not val or val_str in ["-", "nan", "None", ""]: return 0
    return len([n for n in val_str.replace("/", ",").split(",") if n.strip()])

# 3. 데이터 추출 엔진
def load_data(url, team_name):
    try:
        xl = pd.ExcelFile(url)
        last_sheet = xl.sheet_names[-1]
        df = xl.parse(last_sheet, header=None)
        
        def find_anchor(kw):
            series = df.iloc[:, 0].astype(str).str.replace(" ", "")
            target = kw.replace(" ", "")
            match = df[series == target].index
            return match[0] if not match.empty else None

        idx_w = find_anchor("[금일 작업]")
        idx_p = find_anchor("[예정 작업]")
        idx_a = find_anchor("[근태 현황]")

        all_indices = sorted([i for i in [idx_w, idx_p, idx_a, len(df)] if i is not None])
        def get_end(start):
            for i in all_indices:
                if i > start: return i
            return len
