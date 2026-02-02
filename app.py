import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바 파일 업로드
heavy_file = st.sidebar.file_uploader("합의된 양식의 엑셀 업로드", type=['xlsx'])

def extract_heavy_data_fixed(file):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # 엑셀 시트 전체 로드 (행 번호 유지를 위해 header=None)
    df = pd.read_excel(file, header=None)

    def get_eq(row, a_idx, p_idx, label):
        try:
            a = pd.to_numeric(row.iloc[a_idx], errors='coerce')
            p = pd.to_numeric(row.iloc[p_idx], errors='coerce')
            if a > 0: return f"{label}({int(a)}축, {int(p)}P.P)"
        except: pass
        return ""

    # --- 1. 금일 작업 (엑셀 4행 ~ 9행) ---
    # 파이썬 인덱스는 0부터이므로 엑셀 행번호 - 1 해줍니다.
    w_raw = df.iloc[3:9, :].dropna(subset=[0]) 
    w_df = pd.DataFrame({
        '화주명': w_raw.iloc[:, 0].astype(str).str.strip(),
        '작업내용': w_raw.iloc[:, 1].astype(str).str.strip(),
        '관리자': w_raw.iloc[:, 2].astype(str).str.strip(),
        '비고': w_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
    })
    # '화주' 제목행이나 '대기 장비' 텍스트 포함 행 제외
    w_df = w_df[~w_df['화주명'].str.contains("화주|대기 장비", na=False)].reset_index(drop=True)

    # --- 2. 근태 현황 (엑셀 15행 ~ 21행) ---
    a_raw = df.iloc[14:21, [0, 1, 4]].dropna(subset=[0])
    a_df = pd.DataFrame(a_raw.values, columns=['구분', '관리자', '현황'])
    a_df = a_df[~a_df['구분'].str.contains("구 분|구분", na=False)].reset_index(drop=True)

    # --- 3. 예정 작업 (엑셀 27행 이후) ---
    p_raw = df.iloc[26:, :].dropna(subset=[0])
    p_df = pd.DataFrame({
        '화주명': p_raw.iloc[:, 0].astype(str).str.strip(),
        '예정내용': p_raw.iloc[:, 1].astype(str).str.strip(),
        '예정일정': p_raw.iloc[:, 2].astype(str).str.strip(),
        '비고': p_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
    })
    p_df = p_df[~p_df['화주명'].str.contains("화주|차기", na=False)].reset_index(drop=True)

    return w_df, a_df, p_df

# 데이터 실행 및 출력
if heavy_file:
    w, a, p = extract_heavy_data_fixed(heavy_file)
    t1, t2, t3 = st.tabs(["📊 금일 작업", "👥 근태 현황", "📅 예정 작업"])
    with t1: st.dataframe(w, use_container_width=True)
    with t2: st.table(a) # 근태는 정적 테이블이 보기 좋습니다.
    with t3: st.dataframe(p, use_container_width=True)
