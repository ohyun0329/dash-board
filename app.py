import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 작업 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바 파일 업로드
st.sidebar.header("📁 팀별 작업일보 업로드")
heavy_file = st.sidebar.file_uploader("경남중량팀 일보 (.xlsx)", type=['xlsx'])

# 3. 데이터 추출 및 필터링 핵심 함수
def extract_final_version(file):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        # 헤더 없이 생으로 읽기
        df = pd.read_excel(file, header=None)

        # 장비 정보 변환 보조 함수
        def get_eq(row, a_idx, p_idx, label):
            try:
                a = pd.to_numeric(row.iloc[a_idx], errors='coerce')
                p = pd.to_numeric(row.iloc[p_idx], errors='coerce')
                if a > 0: return f"{label}({int(a)}축, {int(p)}P.P)"
            except: pass
            return ""

        # --- [삭제 대상 블랙리스트] ---
        # 이 단어 중 하나라도 행에 포함되어 있으면 '제목'으로 간주하고 삭제합니다.
        kill_list = ["화주", "작업 내용", "작업내용", "예상일정", "특이 사항", "3. 차기", "3.차기", "구분", "관리자", "2. 근태", "nan", "None"]

        def filter_junk_rows(target_df, col_idx):
            if target_df.empty: return target_df
            # 첫 번째 열(화주명 등)에 블랙리스트 단어가 있는지 전수 검사
            mask = target_df.iloc[:, col_idx].astype(str).apply(
                lambda x: not any(k.replace(" ", "") in x.replace(" ", "") for k in kill_list)
            )
            return target_df[mask].dropna(subset=[target_df.columns[col_idx]]).reset_index(drop=True)

        # --- 위치 추적 ---
        # '화주' 단어가 들어있는 모든 인덱스 찾기
        header_indices = df[df.iloc[:, 0].astype(str).str.contains("화주", na=False)].index.tolist()
        att_title_idx = df[df.iloc[:, 0].astype(str).str.contains("2. 근태 현황", na=False)].index
        att_row_idx = df[df.iloc[:, 0].astype(str).str.contains("구 분|구분", na=False)].index

        # --- [1. 금일 작업] ---
        w_start = header_indices[0] + 1
        w_end = att_title_idx[0] if not att_title_idx.empty else w_start + 8
        w_raw = df.iloc[w_start:w_end, :]
        w_df = pd.DataFrame({
            '화주명': w_raw.iloc[:, 0],
            '작업내용': w_raw.iloc[:, 1],
            '관리자': w_raw.iloc[:, 2],
            '비고': w_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
        })
        w_final = filter_junk_rows(w_df, 0)

        # --- [2. 근태 현황] ---
        if not att_row_idx.empty:
            a_start = att_row_idx[0] + 1
            a_raw = df.iloc[a_start:a_start+8, [0, 1, 4]]
            a_df = pd.DataFrame(a_raw.values, columns=['구분', '관리자', '인원현황'])
            a_final = filter_junk_rows(a_df, 0)
        else: a_final = pd.DataFrame()

        # --- [3. 예정 작업] ---
        # 두 번째 '화주' 키워드가 나오는 행(26행) 다음부터 추출
        if len(header_indices) >= 2:
            p_start = header_indices[1] + 1
            p_raw = df.iloc[p_start:, :]
            p_df = pd.DataFrame({
                '화주명': p_raw.iloc[:, 0],
                '예정내용': p_raw.iloc[:, 1],
                '예정일정': p_raw.iloc[:, 2],
                '비고': p_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
            })
            p_final = filter_junk_rows(p_df, 0)
        else: p_final = pd.DataFrame()

        return w_final, a_final, p_final

    except Exception as e:
        st.error(f"데이터 처리 오류: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 실행 및 탭 출력
work, att, plan = extract_final_version(heavy_file)

if heavy_file:
    t1, t2, t3 = st.tabs(["📊 금일 작업 현황", "👥 근태 현황", "📅 향후 예정 작업"])
    with t1: st.dataframe(work, use_container_width=True)
    with t2: st.table(att) # 근태는 정적인 테이블이 더 깔끔함
    with t3: st.dataframe(plan, use_container_width=True)
else:
    st.info("사이드바에서 파일을 업로드해 주세요.")
