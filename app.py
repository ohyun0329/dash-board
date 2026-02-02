import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 작업 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바 파일 업로드
st.sidebar.header("📁 팀별 작업일보 업로드")
heavy_file = st.sidebar.file_uploader("경남중량팀 일보 (.xlsx)", type=['xlsx'])

# 3. 데이터 정제용 '블랙리스트' (이 단어가 보이면 그 행은 무조건 삭제)
STOP_WORDS = ["화주", "작업 내용", "예정내용", "예상일정", "관리자", "구분", "3. 차기", "3.차기", "특이 사항", "nan", "None", "2. 근태", "기사", "다기능"]

def extract_clean_data(file):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        # 헤더 없이 원본 그대로 로드
        df = pd.read_excel(file, header=None)
        
        # 장비 정보 파싱 함수
        def get_eq(row, a_idx, p_idx, label):
            try:
                a = pd.to_numeric(row.iloc[a_idx], errors='coerce')
                p = pd.to_numeric(row.iloc[p_idx], errors='coerce')
                if a > 0: return f"{label}({int(a)}축, {int(p)}P.P)"
            except: pass
            return ""

        # --- [1. 금일 작업] ---
        # 첫 번째 '화주' 단어 다음부터 10줄 추출
        w_idx = df[df.iloc[:, 0].astype(str).str.contains("화주", na=False)].index[0]
        w_raw = df.iloc[w_idx+1 : w_idx+10, :]
        w_df = pd.DataFrame({
            '팀명': '경남중량팀',
            '화주명': w_raw.iloc[:, 0].astype(str).str.strip(),
            '작업내용': w_raw.iloc[:, 1].astype(str).str.strip(),
            '관리자': w_raw.iloc[:, 2].astype(str).str.strip(),
            '비고': w_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
        })

        # --- [2. 근태 현황] ---
        a_idx_search = df[df.iloc[:, 0].astype(str).str.contains("구 분|구분", na=False)].index
        if not a_idx_search.empty:
            a_start = a_idx_search[0] + 1
            a_raw = df.iloc[a_start:a_start+8, [0, 1, 4]]
            a_df = pd.DataFrame(a_raw.values, columns=['구분', '관리자', '인원 현황'])
            a_df.insert(0, '팀명', '경남중량팀')
        else: a_df = pd.DataFrame()

        # --- [3. 예정 작업] ---
        # '화주' 단어가 두 번째로 나오는 곳부터 추출
        indices = df[df.iloc[:, 0].astype(str).str.contains("화주", na=False)].index.tolist()
        if len(indices) >= 2:
            p_start = indices[1] + 1
            p_raw = df.iloc[p_start:, :]
            p_df = pd.DataFrame({
                '팀명': '경남중량팀',
                '화주명': p_raw.iloc[:, 0].astype(str).str.strip(),
                '예정내용': p_raw.iloc[:, 1].astype(str).str.strip(),
                '예정일정': p_raw.iloc[:, 2].astype(str).str.strip(),
                '비고': p_raw.apply(lambda r: ", ".join(filter(None, [get_eq(r, 5, 6, "SCH"), get_eq(r, 7, 8, "KAM")])), axis=1)
            })
        else: p_df = pd.DataFrame()

        # --- 🔥 최종 필터링: 제목/빈칸 행 모조리 삭제 🔥 ---
        def final_clean(target_df, col_to_check):
            if target_df.empty: return target_df
            # 제목 단어가 포함되어 있거나 빈 값(nan)인 행 제거
            mask = target_df[col_to_check].apply(lambda x: not any(k in str(x).replace(" ", "") for k in STOP_WORDS) and str(x) != "nan")
            return target_df[mask].reset_index(drop=True)

        return final_clean(w_df, '화주명'), final_clean(a_df, '구분'), final_clean(p_df, '화주명')

    except Exception as e:
        st.error(f"데이터 처리 오류: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로드
work, att, plan = extract_clean_data(heavy_file)

# 탭 구성 및 출력
t1, t2, t3 = st.tabs(["📊 금일 작업", "👥 근태 현황", "📅 예정 작업"])

with t1:
    if heavy_file: st.dataframe(work, use_container_width=True)
    else: st.info("파일을 업로드해 주세요.")

with t2: st.dataframe(att, use_container_width=True)
with t3: st.dataframe(plan, use_container_width=True)
