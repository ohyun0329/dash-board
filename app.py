import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 작업 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바 파일 업로드
st.sidebar.header("📁 팀별 작업일보 업로드")
heavy_file = st.sidebar.file_uploader("경남중량팀 일보 (.xlsx)", type=['xlsx'])

# 3. 데이터 추출 핵심 함수
def extract_smart_sections(file):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        # 헤더 없이 생으로 읽기
        df = pd.read_excel(file, header=None)
        
        # 장비 텍스트 변환 함수
        def get_equip_desc(row, axle_idx, ppu_idx, label):
            try:
                axle = pd.to_numeric(row.iloc[axle_idx], errors='coerce')
                ppu = pd.to_numeric(row.iloc[ppu_idx], errors='coerce')
                if axle > 0: return f"{label}({int(axle)}축, {int(ppu)}P.P)"
            except: pass
            return ""

        # --- [1. 금일 작업 현황] ---
        # '화주' 키워드가 첫 번째로 나타나는 위치를 찾아 그 다음 줄부터 읽음
        w_idx = df[df.iloc[:, 0].astype(str).str.contains("화주", na=False)].index[0]
        w_raw = df.iloc[w_idx+1 : w_idx+7, :].dropna(subset=[0])
        w_df = pd.DataFrame({
            '팀명': '경남중량팀',
            '화주명': w_raw.iloc[:, 0].astype(str).str.strip(),
            '작업내용': w_raw.iloc[:, 1].astype(str).str.strip(),
            '관리자': w_raw.iloc[:, 2].astype(str).str.strip(),
            '비고': w_raw.apply(lambda r: ", ".join(filter(None, [get_equip_desc(r, 5, 6, "SCH"), get_equip_desc(r, 7, 8, "KAM")])), axis=1)
        })

        # --- [3. 향후 예정 작업] ---
        # '화주' 키워드가 두 번째로 나타나는 위치를 정밀 추적
        indices = df[df.iloc[:, 0].astype(str).str.contains("화주", na=False)].index.tolist()
        if len(indices) >= 2:
            p_start = indices[1] + 1
            p_raw = df.iloc[p_start:, :].dropna(subset=[0])
            p_df = pd.DataFrame({
                '팀명': '경남중량팀',
                '화주명': p_raw.iloc[:, 0].astype(str).str.strip(),
                '예정내용': p_raw.iloc[:, 1].astype(str).str.strip(),
                '예정일정': p_raw.iloc[:, 2].astype(str).str.strip(),
                '비고': p_raw.apply(lambda r: ", ".join(filter(None, [get_equip_desc(r, 5, 6, "SCH"), get_equip_desc(r, 7, 8, "KAM")])), axis=1)
            })
        else: p_df = pd.DataFrame()

        # --- [핵심 필터링: 제목 단어가 포함된 행을 무조건 삭제] ---
        # 화주명 칸에 '화주'나 '차기 예정' 같은 단어가 있으면 데이터가 아니므로 삭제합니다.
        stop_words = ["화주", "작업 내용", "예정내용", "예상일정", "3. 차기", "3.차기", "특이 사항", "nan", "None"]
        
        def is_valid(val):
            val = str(val).replace(" ", "") # 공백 제거 후 비교
            return not any(word.replace(" ", "") in val for word in stop_words)

        w_df = w_df[w_df['화주명'].apply(is_valid)].reset_index(drop=True)
        p_df = p_df[p_df['화주명'].apply(is_valid)].reset_index(drop=True)
        
        return w_df, p_df

    except Exception as e:
        st.error(f"오류: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 데이터 로드 및 출력
work, plan = extract_smart_sections(heavy_file)

if heavy_file:
    tab1, tab2 = st.tabs(["📊 금일 작업 현황", "📅 향후 예정 작업"])
    with tab1:
        st.subheader("🗓️ 1. 금일 작업 현황")
        st.dataframe(work, use_container_width=True)
    with tab2:
        st.subheader("📅 3. 향후 예정 작업")
        st.dataframe(plan, use_container_width=True)
else:
    st.info("사이드바에서 파일을 업로드해 주세요.")
