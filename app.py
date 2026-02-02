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

# 3. 데이터 추출 및 필터링 핵심 함수
def extract_final_sections(file, team_type):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    team_names = {'heavy': '경남중량팀', 'logis': '경남물류운영팀', 'dock': '경남하역팀'}
    t_name = team_names[team_type]
    
    try:
        # 헤더 없이 원본 그대로 읽기
        df = pd.read_excel(file, header=None)
        
        # 장비 텍스트 변환 보조 함수
        def get_equip_desc(row, axle_idx, ppu_idx, label):
            try:
                axle = pd.to_numeric(row.iloc[axle_idx], errors='coerce')
                ppu = pd.to_numeric(row.iloc[ppu_idx], errors='coerce')
                if axle > 0: return f"{label}({int(axle)}축, {int(ppu)}P.P)"
            except: pass
            return ""

        if team_type == 'heavy':
            # --- [위치 추적] ---
            # '화주' 키워드가 포함된 모든 행의 인덱스를 찾음
            header_indices = df[df.iloc[:, 0].astype(str).str.contains("화주", na=False)].index.tolist()
            att_title_search = df[df.iloc[:, 0].astype(str).str.contains("2. 근태 현황", na=False)].index
            
            # --- [1. 금일 작업 현황] ---
            work_start = header_indices[0] + 1
            work_end = att_title_search[0] if not att_title_search.empty else work_start + 6
            work_raw = df.iloc[work_start:work_end, :].dropna(subset=[0])
            
            work_df = pd.DataFrame({
                '팀명': t_name,
                '화주명': work_raw.iloc[:, 0].astype(str).str.strip(),
                '작업내용': work_raw.iloc[:, 1].astype(str).str.strip(),
                '관리자': work_raw.iloc[:, 2].astype(str).str.strip(),
                '비고(장비)': work_raw.apply(lambda r: ", ".join(filter(None, [
                    get_equip_desc(r, 5, 6, "SCH"), get_equip_desc(r, 7, 8, "KAM")
                ])), axis=1)
            })

            # --- [2. 근태 현황] ---
            att_start_search = df[df.iloc[:, 0].astype(str).str.contains("구 분|구분", na=False)].index
            if not att_start_search.empty:
                att_start = att_start_search[0] + 1
                att_raw = df.iloc[att_start:att_start+7, [0, 1, 4]].dropna(subset=[0])
                att_df = pd.DataFrame({
                    '팀명': t_name,
                    '구분': att_raw.iloc[:, 0].astype(str).str.strip(),
                    '관리자': att_raw.iloc[:, 1].astype(str).str.strip(),
                    '인원 현황': att_raw.iloc[:, 2].astype(str).str.strip()
                })
            else: att_df = pd.DataFrame()

            # --- [3. 향후 예정 작업] ---
            # 두 번째 '화주' 제목 행 다음부터 읽기
            if len(header_indices) > 1:
                plan_start = header_indices[1] + 1
                plan_raw = df.iloc[plan_start:, :].dropna(subset=[0])
                plan_df = pd.DataFrame({
                    '팀명': t_name,
                    '화주명': plan_raw.iloc[:, 0].astype(str).str.strip(),
                    '예정내용': plan_raw.iloc[:, 1].astype(str).str.strip(),
                    '예정일정': plan_raw.iloc[:, 2].astype(str).str.strip(),
                    '비고': plan_raw.apply(lambda r: ", ".join(filter(None, [
                        get_equip_desc(r, 5, 6, "SCH"), get_equip_desc(r, 7, 8, "KAM")
                    ])), axis=1)
                })
            else: plan_df = pd.DataFrame()
            
        else:
            # 물류/하역팀 기본 구성
            work_df = pd.DataFrame({'팀명':[t_name], '화주명':['일보 참조'], '작업내용':['-'], '관리자':['-'], '비고(장비)':['-']})
            att_df = pd.DataFrame({'팀명':[t_name], '구분':['상세 확인'], '관리자':['-'], '인원 현황':['-']})
            plan_df = pd.DataFrame({'팀명':[t_name], '화주명':['-'], '예정내용':['-'], '예정일정':['-'], '비고':['-']})

        # --- [최종 필터링: 제목 단어가 포함된 0번 행을 무조건 제거] ---
        # 화주명 칸에 '화주'라는 단어가 포함된 행은 데이터가 아닌 제목이므로 삭제
        if not work_df.empty:
            work_df = work_df[work_df['화주명'] != '화주'].reset_index(drop=True)
        if not plan_df.empty:
            plan_df = plan_df[plan_df['화주명'] != '화주'].reset_index(drop=True)
            # "대기 장비" 관련 텍스트가 포함된 행도 최종 제거
            plan_df = plan_df[~plan_df['화주명'].str.contains("대기 장비|마산항", na=False)].reset_index(drop=True)
        if not att_df.empty:
            att_df = att_df[~att_df['구분'].str.contains("구분|구 분", na=False)].reset_index(drop=True)
        
        return work_df, att_df, plan_df

    except Exception as e:
        st.error(f"{t_name} 처리 중 예외 발생: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 통합 및 화면 출력
h_w, h_a, h_p = extract_final_sections(heavy_file, 'heavy')
l_w, l_a, l_p = extract_final_sections(logis_file, 'logis')
d_w, d_a, d_p = extract_final_sections(dock_file, 'dock')

tab1, tab2, tab3, tab4 = st.tabs(["📊 종합 현황", "🚚 경남중량팀", "📦 경남물류운영팀", "⚓ 경남하역팀"])

with tab1:
    if any([heavy_file, logis_file, dock_file]):
        st.subheader("🗓️ 1. 금일 작업 현황")
        st.dataframe(pd.concat([h_w, l_w, d_w], ignore_index=True), use_container_width=True)
        st.divider()
        st.subheader("👥 2. 근태 현황")
        st.dataframe(pd.concat([h_a, l_a, d_a], ignore_index=True), use_container_width=True)
        st.divider()
        st.subheader("📅 3. 향후 예정 작업")
        st.dataframe(pd.concat([h_p, l_p, d_p], ignore_index=True), use_container_width=True)
    else:
        st.info("사이드바에서 파일을 업로드해 주세요.")

with tab2: st.write(h_w)
with tab3: st.write(l_w)
with tab4: st.write(d_w)
