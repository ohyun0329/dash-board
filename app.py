import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 작업 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바 파일 업로드
st.sidebar.header("📁 팀별 작업일보 업로드")
heavy_file = st.sidebar.file_uploader("경남중량팀 일보 (.xlsx)", type=['xlsx'])

# 3. 데이터 추출 핵심 로직
def extract_final_version(file):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        # 헤더 없이 생으로 읽기
        df = pd.read_excel(file, header=None)

        # 장비 텍스트 변환 함수 (축/P.P 상세 기입)
        def get_equip(row, axle_idx, ppu_idx, label):
            try:
                axle = pd.to_numeric(row.iloc[axle_idx], errors='coerce')
                ppu = pd.to_numeric(row.iloc[ppu_idx], errors='coerce')
                if axle > 0: return f"{label}({int(axle)}축, {int(ppu)}P.P)"
            except: pass
            return ""

        # --- [1. 금일 작업 현황 추출] ---
        # "화주" 단어가 처음 나오는 행 찾기
        work_idx = df[df.iloc[:, 0].astype(str).str.contains("화주", na=False)].index[0]
        # 제목 행(+1) 다음부터 '2. 근태 현황' 전까지 데이터만 가져오기
        att_title_idx = df[df.iloc[:, 0].astype(str).str.contains("2. 근태 현황", na=False)].index[0]
        work_raw = df.iloc[work_idx+1 : att_title_idx-1, :].dropna(subset=[0])
        # 대기 장비 행 제외
        work_raw = work_raw[~work_raw.iloc[:, 0].astype(str).str.contains("대기 장비|마산항", na=False)]
        
        work_df = pd.DataFrame({
            '팀명': '경남중량팀',
            '화주명': work_raw.iloc[:, 0].astype(str).str.strip(),
            '작업내용': work_raw.iloc[:, 1].astype(str).str.strip(),
            '관리자': work_raw.iloc[:, 2].astype(str).str.strip(),
            '비고(장비)': work_raw.apply(lambda r: ", ".join(filter(None, [
                get_equip(r, 5, 6, "SCH"), get_equip(r, 7, 8, "KAM")
            ])), axis=1)
        })

        # --- [2. 근태 현황 추출] ---
        att_start = df[df.iloc[:, 0].astype(str).str.contains("구 분|구분", na=False)].index[0] + 1
        att_raw = df.iloc[att_start : att_start+7, [0, 1, 4]].dropna(subset=[0])
        att_df = pd.DataFrame({
            '팀명': '경남중량팀',
            '구분': att_raw.iloc[:, 0].astype(str).str.strip(),
            '관리자': att_raw.iloc[:, 1].astype(str).str.strip(),
            '인원 현황': att_raw.iloc[:, 2].astype(str).str.strip()
        })

        # --- [3. 향후 예정 작업 추출] ---
        # "화주" 단어가 두 번째로 나오는 행 찾기
        plan_header_idx = df[df.iloc[:, 0].astype(str).str.contains("화주", na=False)].index[1]
        # 그 행(+1) 다음부터 끝까지 가져오기
        plan_raw = df.iloc[plan_header_idx+1 :, :].dropna(subset=[0])
        
        plan_df = pd.DataFrame({
            '팀명': '경남중량팀',
            '화주명': plan_raw.iloc[:, 0].astype(str).str.strip(),
            '예정내용': plan_raw.iloc[:, 1].astype(str).str.strip(),
            '예정일정': plan_raw.iloc[:, 2].astype(str).str.strip(),
            '비고(장비)': plan_raw.apply(lambda r: ", ".join(filter(None, [
                get_equip(r, 5, 6, "SCH"), get_equip(r, 7, 8, "KAM")
            ])), axis=1)
        })

        # --- [최종 필터: 제목 텍스트가 데이터에 섞인 경우 강제 삭제] ---
        stop_words = ["화주", "작업 내용", "예정내용", "예상일정", "관리자", "구분", "nan", "None"]
        work_df = work_df[~work_df['화주명'].isin(stop_words)].reset_index(drop=True)
        plan_df = plan_df[~plan_df['화주명'].isin(stop_words)].reset_index(drop=True)

        return work_df, att_df, plan_df

    except Exception as e:
        st.error(f"오류 발생: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로드 및 탭 구성
w, a, p = extract_final_version(heavy_file)

tab1, tab2, tab3 = st.tabs(["📊 종합 현황", "👥 근태 현황", "📅 예정 작업"])

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
        st.info("사이드바에서 파일을 업로드해 주세요.")
