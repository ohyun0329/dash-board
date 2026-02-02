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

# 3. 데이터 추출 함수
def extract_sections(file, team_type):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    team_names = {'heavy': '경남중량팀', 'logis': '경남물류운영팀', 'dock': '경남하역팀'}
    t_name = team_names[team_type]
    
    try:
        # 엑셀 데이터 로드 (중량팀 양식 특성 반영)
        df = pd.read_excel(file)
        
        # --- 공통 장비 파싱 함수 (중량팀용) ---
        def get_equip_desc(row, axle_idx, ppu_idx, label):
            try:
                axle = pd.to_numeric(row.iloc[axle_idx], errors='coerce')
                ppu = pd.to_numeric(row.iloc[ppu_idx], errors='coerce')
                if axle > 0:
                    return f"{label}({int(axle)}축, {int(ppu)}P.P)"
            except: pass
            return ""

        # --- 1. 금일 작업 현황 ---
        if team_type == 'heavy':
            # '1. 금일 작업 현황' 제목 아래 데이터 (보통 3행부터)
            # 마지막 행(대기 장비) 제외를 위해 데이터가 있는 행만 필터링
            work_raw = df.iloc[2:8, :].dropna(subset=[df.columns[0]]) 
            work_raw = work_raw[~work_raw.iloc[:, 0].str.contains("대기 장비", na=False)]
            
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
            att_raw = df.iloc[10:17, [0, 1, 4]] # 구분, 관리자, 기사+다기능
            att_df = pd.DataFrame({
                '팀명': t_name,
                '구분': att_raw.iloc[:, 0].astype(str),
                '관리자': att_raw.iloc[:, 1].astype(str),
                '인원 현황': att_raw.iloc[:, 2].astype(str)
            })
            
            # --- 3. 차기 예정 작업 ---
            plan_raw = df.iloc[20:25, :].dropna(subset=[df.columns[0]])
            plan_df = pd.DataFrame({
                '팀명': t_name,
                '화주명': plan_raw.iloc[:, 0].astype(str),
                '예정내용': plan_raw.iloc[:, 1].astype(str),
                '예정일정': plan_raw.iloc[:, 2].astype(str),
                '비고': plan_raw.apply(lambda r: ", ".join(filter(None, [
                    get_equip_desc(r, 5, 6, "SCH"), get_equip_desc(r, 7, 8, "KAM")
                ])), axis=1)
            })
        else:
            # 물류/하역팀 처리 (기본 양식)
            work_df = pd.DataFrame({'팀명': [t_name], '화주명': ['일보 참조'], '작업내용': ['데이터 로드 완료'], '관리자': ['-'], '비고(장비)': ['-']})
            att_df = pd.DataFrame({'팀명': [t_name], '구분': ['-'], '관리자': ['-'], '인원 현황': ['상세 탭 참조']})
            plan_df = pd.DataFrame({'팀명': [t_name], '화주명': ['-'], '예정내용': ['-'], '예정일정': ['-'], '비고': ['-']})

        return work_df, att_df, plan_df

    except Exception as e:
        st.error(f"{t_name} 데이터 추출 중 오류: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로드 및 탭 구성
h_w, h_a, h_p = extract_sections(heavy_file, 'heavy')
l_w, l_a, l_p = extract_sections(logis_file, 'logis')
d_w, d_a, d_p = extract_sections(dock_file, 'dock')

tab1, tab2, tab3, tab4 = st.tabs(["📊 종합 현황", "🚚 경남중량팀", "📦 경남물류운영팀", "⚓ 경남하역팀"])

with tab1:
    if heavy_file or logis_file or dock_file:
        st.subheader("🗓️ 1. 금일 작업 현황")
        total_work = pd.concat([h_w, l_w, d_w], ignore_index=True)
        st.dataframe(total_work, use_container_width=True)
        
        st.divider()
        st.subheader("👥 2. 근태 현황")
        total_att = pd.concat([h_a, l_a, d_a], ignore_index=True)
        st.dataframe(total_att, use_container_width=True)
        
        st.divider()
        st.subheader("📅 3. 향후 예정 작업")
        total_plan = pd.concat([h_p, l_p, d_p], ignore_index=True)
        st.dataframe(total_plan, use_container_width=True)
    else:
        st.info("파일을 업로드하면 통합 대시보드가 생성됩니다.")

# 상세 탭 (디버깅용 원본 데이터)
with tab2: st.write(h_w)
with tab3: st.write(l_w)
with tab4: st.write(d_w)
