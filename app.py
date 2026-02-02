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
def extract_sections_auto(file):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        # header=None으로 읽어 전체 판을 먼저 봅니다.
        df = pd.read_excel(file, header=None)
        
        # 장비 정보 변환 보조 함수
        def get_eq(row, a_idx, p_idx, label):
            try:
                a = pd.to_numeric(row.iloc[a_idx], errors='coerce')
                p = pd.to_numeric(row.iloc[p_idx], errors='coerce')
                if a > 0: return f"{label}({int(a)}축, {int(p)}P.P)"
            except: pass
            return ""

        # --- 키워드 위치 추적 (핵심!) ---
        # '화주'라는 글자가 들어있는 모든 행 번호를 찾습니다.
        indices = df[df.iloc[:, 0].astype(str).str.contains("화주", na=False)].index.tolist()
        # '구분'이라는 글자가 들어있는 행 번호를 찾습니다.
        att_idx = df[df.iloc[:, 0].astype(str).str.contains("구 분|구분", na=False)].index.tolist()
        # '근태 현황' 제목 위치
        att_title = df[df.iloc[:, 0].astype(str).str.contains("2. 근태 현황", na=False)].index.tolist()

        # --- 1. 금일 작업 현황 ---
        # 첫 번째 '화주' 단어 다음 줄부터 근태 현황 제목 전까지
        w_start = indices[0] + 1
        w_end = att_title[0] if att_title else w_start + 6
        w_raw = df.iloc[w_start:w_end, :].dropna(subset=[0])
        # "화주" 제목행이나 "대기 장비" 행이 섞여있으면 삭제
        w_raw = w_raw[~w_raw.iloc[:, 0].astype(str).str.contains("화주|대기 장비", na=False)]
        
        work_df = pd.DataFrame({
            '팀명': '경남중량팀',
            '화주명': w_raw.iloc[:, 0].astype(str),
            '작업내용': w_raw.iloc[:, 1].astype(str),
            '관리자': w_raw.iloc[:, 2].astype(str),
            '비고': w_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
        })

        # --- 2. 근태 현황 ---
        # '구분' 단어 다음 줄부터 7줄 정도
        if att_idx:
            a_start = att_idx[0] + 1
            a_raw = df.iloc[a_start:a_start+7, [0, 1, 4]].dropna(subset=[0])
            a_raw = a_raw[~a_raw.iloc[:, 0].astype(str).str.contains("구분|관리자", na=False)]
            att_df = pd.DataFrame({
                '팀명': '경남중량팀',
                '구분': a_raw.iloc[:, 0].astype(str),
                '관리자': a_raw.iloc[:, 1].astype(str),
                '인원 현황': a_raw.iloc[:, 2].astype(str)
            })
        else: att_df = pd.DataFrame()

        # --- 3. 향후 예정 작업 ---
        # 두 번째 '화주' 단어 다음 줄부터 끝까지
        if len(indices) >= 2:
            p_start = indices[1] + 1
            p_raw = df.iloc[p_start:, :].dropna(subset=[0])
            p_raw = p_raw[~p_raw.iloc[:, 0].astype(str).str.contains("화주|차기", na=False)]
            plan_df = pd.DataFrame({
                '팀명': '경남중량팀',
                '화주명': p_raw.iloc[:, 0].astype(str),
                '예정내용': p_raw.iloc[:, 1].astype(str),
                '예정일정': p_raw.iloc[:, 2].astype(str),
                '비고': p_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
            })
        else: plan_df = pd.DataFrame()

        return work_df.reset_index(drop=True), att_df.reset_index(drop=True), plan_df.reset_index(drop=True)

    except Exception as e:
        st.error(f"데이터 처리 중 오류 발생: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 실행
w, a, p = extract_sections_auto(heavy_file)

# 화면 출력
tab1, tab2 = st.tabs(["📊 통합 리포트", "🚚 상세 데이터"])

with tab1:
    if heavy_file:
        st.subheader("🗓️ 1. 금일 작업 현황")
        st.dataframe(w, use_container_width=True)
        st.divider()
        st.subheader("👥 2. 근태 현황")
        st.dataframe(a, use_container_width=True)
        st.divider()
        st.subheader("📅 3. 향후 예정 작업")
        st.dataframe(p, use_container_width=True)
    else:
        st.info("파일을 업로드해 주세요.")

with tab2:
    st.write("금일 작업 원본", w)
    st.write("근태 현황 원본", a)
