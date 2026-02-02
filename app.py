import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 작업 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바 파일 업로드
st.sidebar.header("📁 팀별 작업일보 업로드")
heavy_file = st.sidebar.file_uploader("경남중량팀 일보 (.xlsx)", type=['xlsx'])

# 3. 데이터 정밀 추출 함수
def extract_final_clean_data(file):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        # 헤더 없이 원본 그대로 읽기
        df = pd.read_excel(file, header=None)
        
        # 장비 정보 파싱 (축/P.P 상세)
        def get_eq_detail(row, a_idx, p_idx, label):
            try:
                a = pd.to_numeric(row.iloc[a_idx], errors='coerce')
                p = pd.to_numeric(row.iloc[p_idx], errors='coerce')
                if a > 0: return f"{label}({int(a)}축, {int(p)}P.P)"
            except: pass
            return ""

        # 제목 행 키워드 목록 (이 단어들이 포함된 행은 무조건 삭제)
        stop_keywords = ["화주", "작업 내용", "예정내용", "예상일정", "관리자", "구분", "3. 차기", "3.차기", "특이 사항", "nan", "None", "2. 근태"]

        def clean_section(raw_data, col_names):
            if raw_data.empty: return pd.DataFrame()
            clean_df = pd.DataFrame(raw_data.values, columns=col_names)
            # 첫 번째 열(화주명/구분)을 기준으로 제목 단어가 포함된 행 전체 제거
            mask = clean_df.iloc[:, 0].astype(str).apply(lambda x: not any(k in x.replace(" ", "") for k in stop_keywords))
            return clean_df[mask].dropna(subset=[clean_df.columns[0]]).reset_index(drop=True)

        # --- 위치 추적 ---
        header_indices = df[df.iloc[:, 0].astype(str).str.contains("화주", na=False)].index.tolist()
        att_title_search = df[df.iloc[:, 0].astype(str).str.contains("2. 근태 현황", na=False)].index
        att_start_search = df[df.iloc[:, 0].astype(str).str.contains("구 분|구분", na=False)].index

        # --- [1. 금일 작업] ---
        w_start = header_indices[0] + 1
        w_end = att_title_search[0] if not att_title_search.empty else w_start + 6
        w_raw = df.iloc[w_start:w_end, :]
        w_df = pd.DataFrame({
            '팀명': '경남중량팀',
            '화주명': w_raw.iloc[:, 0],
            '작업내용': w_raw.iloc[:, 1],
            '관리자': w_raw.iloc[:, 2],
            '비고': w_raw.apply(lambda r: ", ".join(filter(None, [get_eq_detail(r, 5, 6, "SCH"), get_eq_detail(r, 7, 8, "KAM")])), axis=1)
        })
        w_final = clean_section(w_df, ['팀명', '화주명', '작업내용', '관리자', '비고'])
        # '마산항 대기 장비' 행 추가 필터링
        w_final = w_final[~w_final['화주명'].str.contains("대기 장비|마산항", na=False)]

        # --- [2. 근태 현황] ---
        if not att_start_search.empty:
            a_start = att_start_search[0] + 1
            a_raw = df.iloc[a_start:a_start+8, [0, 1, 4]]
            a_final = clean_section(a_raw, ['구분', '관리자', '인원 현황'])
            a_final.insert(0, '팀명', '경남중량팀')
        else: a_final = pd.DataFrame()

        # --- [3. 예정 작업] ---
        if len(header_indices) > 1:
            p_start = header_indices[1] + 1
            p_raw = df.iloc[p_start:, :]
            p_df = pd.DataFrame({
                '팀명': '경남중량팀',
                '화주명': p_raw.iloc[:, 0],
                '예정내용': p_raw.iloc[:, 1],
                '예정일정': p_raw.iloc[:, 2],
                '비고': p_raw.apply(lambda r: ", ".join(filter(None, [get_eq_detail(r, 5, 6, "SCH"), get_eq_detail(r, 7, 8, "KAM")])), axis=1)
            })
            p_final = clean_section(p_df, ['팀명', '화주명', '예정내용', '예정일정', '비고'])
        else: p_final = pd.DataFrame()

        return w_final, a_final, p_final

    except Exception as e:
        st.error(f"데이터 처리 중 오류 발생: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로드 및 탭 구성
work, att, plan = extract_final_clean_data(heavy_file)

t1, t2, t3 = st.tabs(["📊 금일 작업 현황", "👥 근태 현황", "📅 향후 예정 작업"])

with t1:
    if heavy_file:
        st.subheader("🗓️ 1. 금일 작업 현황")
        st.dataframe(work, use_container_width=True)
    else: st.info("사이드바에서 파일을 업로드해 주세요.")

with t2:
    st.subheader("👥 2. 팀별 근태 현황")
    st.dataframe(att, use_container_width=True)

with t3:
    st.subheader("📅 3. 향후 예정 작업")
    st.dataframe(plan, use_container_width=True)
