import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 작업 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바 파일 업로드
st.sidebar.header("📁 팀별 작업일보 업로드")
heavy_file = st.sidebar.file_uploader("경남중량팀 일보 (.xlsx)", type=['xlsx'])
logis_file = st.sidebar.file_uploader("경남물류운영팀 일보 (.xlsx)", type=['xlsx'])
dock_file = st.sidebar.file_uploader("경남하역팀 일보 (.xlsx)", type=['xlsx'])

# 3. 데이터 추출 함수 (정밀 위치 추적형)
def extract_sections(file, team_type):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    team_names = {'heavy': '경남중량팀', 'logis': '경남물류운영팀', 'dock': '경남하역팀'}
    t_name = team_names[team_type]
    
    try:
        # header=None으로 읽어야 제목 줄 위치를 정확히 계산할 수 있습니다.
        df = pd.read_excel(file, header=None)
        
        def get_equip_desc(row, axle_idx, ppu_idx, label):
            try:
                axle = pd.to_numeric(row.iloc[axle_idx], errors='coerce')
                ppu = pd.to_numeric(row.iloc[ppu_idx], errors='coerce')
                if axle > 0: return f"{label}({int(axle)}축, {int(ppu)}P.P)"
            except: pass
            return ""

        if team_type == 'heavy':
            # --- 위치 탐색: '화주'나 '구분'이라는 단어가 있는 행 번호를 찾습니다 ---
            header_indices = df[df.iloc[:, 0].astype(str).str.contains("화주", na=False)].index.tolist()
            att_title_idx = df[df.iloc[:, 0].astype(str).str.contains("2. 근태 현황", na=False)].index
            att_row_idx = df[df.iloc[:, 0].astype(str).str.contains("구 분|구분", na=False)].index

            # --- 1. 금일 작업 현황 ---
            # 첫 번째 '화주' 제목의 다음 행(+1)부터 근태 현황 전까지
            w_start = header_indices[0] + 1
            w_end = att_title_idx[0] if not att_title_idx.empty else w_start + 6
            work_raw = df.iloc[w_start:w_end, :].dropna(subset=[0])
            
            # 제목 행이 섞여 들어왔을 경우(0번행 화주) 강제 필터링
            work_raw = work_raw[~work_raw.iloc[:, 0].astype(str).str.contains("화주|대기 장비", na=False)]
            
            work_df = pd.DataFrame({
                '팀명': t_name,
                '화주명': work_raw.iloc[:, 0].astype(str),
                '작업내용': work_raw.iloc[:, 1].astype(str),
                '관리자': work_raw.iloc[:, 2].astype(str),
                '비고(장비)': work_raw.apply(lambda r: ", ".join(filter(None, [
                    get_equip_desc(r, 5, 6, "SCH"), get_equip_desc(r, 7, 8, "KAM")
                ])), axis=1)
            })

            # --- 2. 근태 현황 ---
            # '구분' 제목의 다음 행(+1)부터 7줄 정도 가져옴
            if not att_row_idx.empty:
                a_start = att_row_idx[0] + 1
                att_raw = df.iloc[a_start:a_start+7, [0, 1, 4]].dropna(subset=[0])
                att_raw = att_raw[~att_raw.iloc[:, 0].astype(str).str.contains("구분|관리자", na=False)]
                att_df = pd.DataFrame({
                    '팀명': t_name,
