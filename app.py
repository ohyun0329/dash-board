import streamlit as st
import pandas as pd

st.set_page_config(page_title="세방(주) 통합 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")

heavy_file = st.sidebar.file_uploader("중량팀 일보 업로드", type=['xlsx'])

def process_heavy_data(file):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # 1. 원본 데이터 로드
    df = pd.read_excel(file, header=None)
    
    # 장비 정보 파싱 (축/PP 상세)
    def get_eq(row, a_idx, p_idx, label):
        try:
            a = pd.to_numeric(row.iloc[a_idx], errors='coerce')
            p = pd.to_numeric(row.iloc[p_idx], errors='coerce')
            if a > 0: return f"{label}({int(a)}축, {int(p)}P.P)"
        except: pass
        return ""

    # 2. 키워드 위치 추적
    # '화주' 단어가 들어있는 모든 위치를 찾음
    indices_hwaju = df[df.iloc[:, 0].astype(str).str.contains("화주", na=False)].index.tolist()
    # '2. 근태 현황' 제목 위치 찾기
    indices_title2 = df[df.iloc[:, 0].astype(str).str.contains("2. 근태 현황", na=False)].index.tolist()
    # '구분' 단어 위치 찾기
    indices_gubun = df[df.iloc[:, 0].astype(str).str.contains("구 분|구분", na=False)].index.tolist()

    # --- [1. 금일 작업] ---
    # 첫 번째 '화주' 행(3행) 다음부터 근태 제목 전까지
    w_start = indices_hwaju[0] + 1
    w_end = indices_title2[0] if indices_title2 else w_start + 10
    w_raw = df.iloc[w_start:w_end, :]
    w_df = pd.DataFrame({
        '화주명': w_raw.iloc[:, 0].astype(str).str.strip(),
        '작업내용': w_raw.iloc[:, 1].astype(str).str.strip(),
        '관리자': w_raw.iloc[:, 2].astype(str).str.strip(),
        '비고': w_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
    })

    # --- [2. 근태 현황] ---
    if indices_gubun:
        a_start = indices_gubun[0] + 1
        a_raw = df.iloc[a_start:a_start+8, [0, 1, 4]]
        a_df = pd.DataFrame(a_raw.values, columns=['구분', '관리자', '인원현황'])
    else: a_df = pd.DataFrame()

    # --- [3. 예정 작업] ---
    # 두 번째 '화주' 행(26행) 다음 줄인 27행부터 읽도록 +1을 추가함
    if len(indices_hwaju) >= 2:
        p_start = indices_hwaju[1] + 1
        p_raw = df.iloc[p_start:, :]
        p_df = pd.DataFrame({
            '화주명': p_raw.iloc[:, 0].astype(str).str.strip(),
            '예정내용': p_raw.iloc[:, 1].astype(str).str.strip(),
            '예정일정': p_raw.iloc[:, 2].astype(str).str.strip(),
            '비고': p_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
        })
    else: p_df = pd.DataFrame()

    # --- [최종 필터링: 텍스트 기반 삭제] ---
    # 혹시나 섞여 들어올 수 있는 모든 제목성 단어를 삭제함
    kill_list = ["화주", "작업 내용", "작업내용", "예상일정", "특이 사항", "3.", "차기", "nan", "None", "대기 장비"]
    
    def clean(target_df, col_name):
        if target_df.empty: return target_df
        # 해당 열에 금지 단어가 포함되어 있거나 빈 값인 행 제거
        mask = target_df[col_name].apply(lambda x: not any(k in str(x) for k in kill_list) and str(x) != "nan")
        return target_df[mask].reset_index(drop=True)

    return clean(w_df, '화주명'), clean(a_df, '구분'), clean(p_df, '화주명')

# 데이터 로드 및 출력
w, a, p = process_heavy_data(heavy_file)

if heavy_file:
    t1, t2, t3 = st.tabs(["📊 금일 작업", "👥 근태 현황", "📅 예정 작업"])
    with t1: st.dataframe(w, use_container_width=True)
    with t2: st.table(a) # 근태는 정적 테이블이 훨씬 깔끔하게 나옵니다
    with t3: st.dataframe(p, use_container_width=True)
else:
    st.info("파일을 업로드하면 통합 리포트가 생성됩니다.")
