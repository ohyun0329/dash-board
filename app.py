import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 작업 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바 파일 업로드
heavy_file = st.sidebar.file_uploader("수정된 양식([금일 작업] 등 적용) 업로드", type=['xlsx'])

def extract_by_fixed_keywords(file):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        # 엑셀을 헤더 없이 통째로 로드
        df = pd.read_excel(file, header=None)

        # 장비 정보 변환 보조 함수
        def get_eq(row, a_idx, p_idx, label):
            try:
                a = pd.to_numeric(row.iloc[a_idx], errors='coerce')
                p = pd.to_numeric(row.iloc[p_idx], errors='coerce')
                if a > 0: return f"{label}({int(a)}축, {int(p)}P.P)"
            except: pass
            return ""

        # --- 키워드 위치 추적 (핵심) ---
        def find_row(keyword):
            # 대괄호와 띄어쓰기를 그대로 인식하도록 설정
            match = df[df.iloc[:, 0].astype(str).str.contains(keyword, na=False, regex=False)].index
            return match[0] if not match.empty else None

        idx_w = find_row("[금일 작업]")
        idx_a = find_row("[근태 현황]")
        idx_p = find_row("[예정 작업]")

        # --- 1. 금일 작업 추출 ---
        if idx_w is not None:
            start = idx_w + 2 # 키워드(0) -> 제목(1) -> 데이터시작(2)
            end = idx_a if idx_a else start + 10
            raw = df.iloc[start:end, :].dropna(subset=[0])
            w_df = pd.DataFrame({
                '화주명': raw.iloc[:, 0].astype(str).str.strip(),
                '작업내용': raw.iloc[:, 1].astype(str).str.strip(),
                '관리자': raw.iloc[:, 2].astype(str).str.strip(),
                '비고(장비)': raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
            })
        else: w_df = pd.DataFrame()

        # --- 2. 근태 현황 추출 ---
        if idx_a is not None:
            start = idx_a + 2
            end = idx_p if idx_p else start + 8
            raw = df.iloc[start:end, [0, 1, 4]].dropna(subset=[0])
            a_df = pd.DataFrame(raw.values, columns=['구분', '관리자', '인원 현황'])
        else: a_df = pd.DataFrame()

        # --- 3. 예정 작업 추출 ---
        if idx_p is not None:
            start = idx_p + 2
            raw = df.iloc[start:, :].dropna(subset=[0])
            p_df = pd.DataFrame({
                '화주명': raw.iloc[:, 0].astype(str).str.strip(),
                '예정내용': raw.iloc[:, 1].astype(str).str.strip(),
                '예정일정': raw.iloc[:, 2].astype(str).str.strip(),
                '비고': raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
            })
        else: p_df = pd.DataFrame()

        # --- 제목줄 찌꺼기 최종 필터링 ---
        def final_filter(target_df, col_name):
            if target_df.empty: return target_df
            # 제목용 단어가 섞여있으면 삭제
            stop_words = ["화주", "구분", "작업 내용", "예정", "비고", "관리자"]
            mask = target_df[col_name].apply(lambda x: not any(s in str(x) for s in stop_words))
            return target_df[mask].reset_index(drop=True)

        return final_filter(w_df, '화주명'), a_df, final_filter(p_df, '화주명')

    except Exception as e:
        st.error(f"데이터를 읽는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 화면 출력
if heavy_file:
    work, attend, plan = extract_by_fixed_keywords(heavy_file)
    
    t1, t2, t3 = st.tabs(["📊 금일 작업", "👥 근태 현황", "📅 예정 작업"])
    
    with t1:
        st.subheader("🗓️ 1. 금일 작업 현황")
        st.dataframe(work, use_container_width=True)
    with t2:
        st.subheader("👥 2. 근태 현황")
        st.table(attend) # 근태는 table이 훨씬 깔끔합니다
    with t3:
        st.subheader("📅 3. 향후 예정 작업")
        st.dataframe(plan, use_container_width=True)
else:
    st.info("사이드바에서 [금일 작업], [근태 현황], [예정 작업] 키워드가 적용된 엑셀을 업로드해 주세요.")
