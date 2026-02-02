import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 작업 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바 파일 업로드
st.sidebar.header("📁 팀별 작업일보 업로드")
heavy_file = st.sidebar.file_uploader("경남중량팀 일보 (.xlsx)", type=['xlsx'])

# 3. 데이터 추출 및 청소 함수
def extract_and_clean(file):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        # 헤더 없이 생으로 읽기
        df = pd.read_excel(file, header=None)
        
        # 장비 정보 변환 함수
        def get_eq(row, a_idx, p_idx, label):
            try:
                a = pd.to_numeric(row.iloc[a_idx], errors='coerce')
                p = pd.to_numeric(row.iloc[p_idx], errors='coerce')
                if a > 0: return f"{label}({int(a)}축, {int(p)}P.P)"
            except: pass
            return ""

        # --- [삭제 대상 키워드] ---
        # 이 단어들이 포함된 행은 데이터가 아니므로 무조건 삭제합니다.
        kill_list = ["화주", "작업 내용", "예정내용", "예상일정", "관리자", "구분", "3. 차기", "3.차기", "특이 사항", "nan", "None", "2. 근태", "기사", "다기능", "축수", "PPU"]

        def filter_junk(target_df):
            if target_df.empty: return target_df
            # 첫 번째 열이나 두 번째 열에 kill_list 단어가 포함된 행 삭제
            def is_junk(row):
                line = " ".join(row.astype(str))
                return any(k.replace(" ", "") in line.replace(" ", "") for k in kill_list)
            
            mask = target_df.apply(is_junk, axis=1)
            return target_df[~mask].dropna(how='all').reset_index(drop=True)

        # --- 위치 추적 ---
        indices = df[df.iloc[:, 0].astype(str).str.contains("화주", na=False)].index.tolist()
        att_start_search = df[df.iloc[:, 0].astype(str).str.contains("구 분|구분", na=False)].index

        # --- [1. 금일 작업] ---
        w_start = indices[0] + 1
        w_raw = df.iloc[w_start:w_start+10, :]
        w_df = pd.DataFrame({
            '팀명': '경남중량팀',
            '화주명': w_raw.iloc[:, 0],
            '작업내용': w_raw.iloc[:, 1],
            '관리자': w_raw.iloc[:, 2],
            '비고': w_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
        })
        w_final = filter_junk(w_df)

        # --- [2. 근태 현황] ---
        if not att_start_search.empty:
            a_start = att_start_search[0] + 1
            a_raw = df.iloc[a_start:a_start+10, [0, 1, 4]]
            a_df = pd.DataFrame(a_raw.values, columns=['구분', '관리자', '인원 현황'])
            a_df.insert(0, '팀명', '경남중량팀')
            a_final = filter_junk(a_df)
        else: a_final = pd.DataFrame()

        # --- [3. 예정 작업] ---
        if len(indices) >= 2:
            p_start = indices[1] + 1
            p_raw = df.iloc[p_start:, :]
            p_df = pd.DataFrame({
                '팀명': '경남중량팀',
                '화주명': p_raw.iloc[:, 0],
                '예정내용': p_raw.iloc[:, 1],
                '예정일정': p_raw.iloc[:, 2],
                '비고': p_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
            })
            p_final = filter_junk(p_df)
        else: p_final = pd.DataFrame()

        return w_final, a_final, p_final

    except Exception as e:
        st.error(f"데이터 처리 오류: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로드 및 출력
work, att, plan = extract_and_clean(heavy_file)

t1, t2, t3 = st.tabs(["📊 금일 작업", "👥 근태 현황", "📅 예정 작업"])

with t1:
    st.subheader("🗓️ 1. 금일 작업 현황")
    st.dataframe(work, use_container_width=True)

with t2:
    st.subheader("👥 2. 근태 현황")
    st.dataframe(att, use_container_width=True)

with t3:
    st.subheader("📅 3. 향후 예정 작업")
    st.dataframe(plan, use_container_width=True)
