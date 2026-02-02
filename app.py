import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바
heavy_file = st.sidebar.file_uploader("중량팀 일보 (.xlsx)", type=['xlsx'])

def process_data(file):
    if file is None: return pd.DataFrame(), pd.DataFrame()
    
    try:
        # 헤더 없이 생으로 읽기 (원본 엑셀의 모든 줄을 다 가져옴)
        df = pd.read_excel(file, header=None)

        # 장비 정보 변환 보조 함수
        def get_eq(row, a_idx, p_idx, label):
            try:
                a = pd.to_numeric(row.iloc[a_idx], errors='coerce')
                p = pd.to_numeric(row.iloc[p_idx], errors='coerce')
                if a > 0: return f"{label}({int(a)}축, {int(p)}P.P)"
            except: pass
            return ""

        # --- 키워드 위치 추적 ---
        # 엑셀 시트 전체에서 '화주'라는 글자가 있는 행 번호들을 다 찾습니다.
        indices = df[df.iloc[:, 0].astype(str).str.contains("화주", na=False)].index.tolist()
        
        # --- [1. 금일 작업] ---
        # 첫 번째 '화주' 단어 다음 줄부터 추출
        w_start = indices[0] + 1
        w_raw = df.iloc[w_start:w_start+10, :].dropna(subset=[0])
        
        work_df = pd.DataFrame({
            '팀명': '경남중량팀',
            '화주명': w_raw.iloc[:, 0].astype(str).str.strip(),
            '작업내용': w_raw.iloc[:, 1].astype(str).str.strip(),
            '관리자': w_raw.iloc[:, 2].astype(str).str.strip(),
            '비고': w_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
        })

        # --- [3. 예정 작업] ---
        # 두 번째 '화주' 단어 다음 줄부터 추출
        if len(indices) >= 2:
            p_start = indices[1] + 1
            p_raw = df.iloc[p_start:, :].dropna(subset=[0])
            plan_df = pd.DataFrame({
                '팀명': '경남중량팀',
                '화주명': p_raw.iloc[:, 0].astype(str).str.strip(),
                '예정내용': p_raw.iloc[:, 1].astype(str).str.strip(),
                '예정일정': p_raw.iloc[:, 2].astype(str).str.strip(),
                '비고': p_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
            })
        else: plan_df = pd.DataFrame()

        # --- 🔥 핵심: 제목 행 강제 삭제 로직 🔥 ---
        # 화주명 칸에 아래 단어들이 포함되어 있으면 '데이터'가 아닌 '제목'이므로 삭제합니다.
        stop_words = ["화주", "작업 내용", "예상일정", "특이 사항", "3. 차기", "3.차기", "nan", "None"]
        
        def final_filter(target_df):
            if target_df.empty: return target_df
            # '화주명' 열에 stop_words가 포함되지 않은 행만 남김
            mask = target_df['화주명'].apply(lambda x: not any(word in str(x) for word in stop_words))
            return target_df[mask].reset_index(drop=True)

        return final_filter(work_df), final_filter(plan_df)

    except Exception as e:
        st.error(f"오류: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 결과 출력
if heavy_file:
    w, p = process_data(heavy_file)
    t1, t2 = st.tabs(["📊 금일 작업", "📅 예정 작업"])
    with t1: st.dataframe(w, use_container_width=True)
    with t2: st.dataframe(p, use_container_width=True)
