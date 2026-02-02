import streamlit as st
import pandas as pd

st.set_page_config(page_title="세방 통합 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")

st.sidebar.header("📁 엑셀 업로드")
heavy_file = st.sidebar.file_uploader("경남중량팀 일보 업로드", type=['xlsx'])

def process_heavy_team(file):
    if file is None: return None, None, None
    
    # 1. 엑셀 전체를 읽어옴
    df_all = pd.read_excel(file, header=None)
    
    # 장비 정보 파싱 함수
    def get_eq(row, a_idx, p_idx, label):
        try:
            a = pd.to_numeric(row.iloc[a_idx], errors='coerce')
            p = pd.to_numeric(row.iloc[p_idx], errors='coerce')
            if a > 0: return f"{label}({int(a)}축, {int(p)}PP)"
        except: pass
        return ""

    # 섹션별 위치 찾기 (키워드 매칭)
    indices = df_all[df_all.iloc[:, 0].astype(str).str.contains("화주", na=False)].index.tolist()
    
    # --- [1. 금일 작업] ---
    w_start = indices[0] + 1
    w_raw = df_all.iloc[w_start:w_start+10].dropna(subset=[0]) # 최대 10행
    w_df = pd.DataFrame({
        '화주명': w_raw.iloc[:, 0].astype(str).str.strip(),
        '작업내용': w_raw.iloc[:, 1].astype(str).str.strip(),
        '관리자': w_raw.iloc[:, 2].astype(str).str.strip(),
        '비고': w_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
    })

    # --- [3. 예정 작업] ---
    # 화주 키워드가 두 번째로 등장하는 곳부터 시작
    if len(indices) >= 2:
        p_start = indices[1] + 1
        p_raw = df_all.iloc[p_start:].dropna(subset=[0])
        p_df = pd.DataFrame({
            '화주명': p_raw.iloc[:, 0].astype(str).str.strip(),
            '예정내용': p_raw.iloc[:, 1].astype(str).str.strip(),
            '예정일정': p_raw.iloc[:, 2].astype(str).str.strip(),
            '비고': p_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
        })
    else: p_df = pd.DataFrame()

    # --- [공통: 0번 행이 제목이면 무조건 삭제] ---
    # '화주'라는 글자가 데이터 칸에 들어와 있으면 그 행은 날려버림
    for df in [w_df, p_df]:
        if not df.empty:
            # 첫 번째 행의 '화주명'이 '화주'라면 삭제
            if df.iloc[0, 0] == "화주":
                df.drop(df.index[0], inplace=True)
            # '대기 장비' 텍스트 포함 행도 삭제
            df = df[~df['화주명'].str.contains("대기 장비|마산항|화주", na=False)]
            df.reset_index(drop=True, inplace=True)

    return w_df, p_df

# 실행 및 출력
work, plan = process_heavy_team(heavy_file)

if heavy_file:
    t1, t2 = st.tabs(["📊 금일 작업", "📅 예정 작업"])
    with t1: st.dataframe(work, use_container_width=True)
    with t2: st.dataframe(plan, use_container_width=True)
