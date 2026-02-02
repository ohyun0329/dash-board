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

# 3. 데이터 추출 및 정제 함수
def extract_refined_sections(file, team_type):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    team_names = {'heavy': '경남중량팀', 'logis': '경남물류운영팀', 'dock': '경남하역팀'}
    t_name = team_names[team_type]
    
    try:
        # 전체 시트 읽기 (헤더 없이 읽어서 위치를 정확히 제어)
        df = pd.read_excel(file, header=None)
        
        # 장비 상세 텍스트 생성 함수
        def get_equip_text(row, axle_idx, ppu_idx, label):
            try:
                axle = pd.to_numeric(row.iloc[axle_idx], errors='coerce')
                ppu = pd.to_numeric(row.iloc[ppu_idx], errors='coerce')
                if axle > 0:
                    return f"{label}({int(axle)}축, {int(ppu)}P.P)"
            except: pass
            return ""

        if team_type == 'heavy':
            # --- 1. 금일 작업 현황 (0번행 제목 제외) ---
            # 3행부터 8행까지 작업 데이터 (마지막 대기 장비 행 제외를 위해 7행까지 슬라이싱 가능)
            work_raw = df.iloc[3:8, :].dropna(how='all')
            # "마산항 4부두 대기 장비" 포함 행 필터링
            work_raw = work_raw[~work_raw.iloc[:, 0].astype(str).str.contains("대기 장비", na=False)]
            
            work_df = pd.DataFrame({
                '팀명': t_name,
                '화주명': work_raw.iloc[:, 0].astype(str),
                '작업내용': work_raw.iloc[:, 1].astype(str),
                '관리자': work_raw.iloc[:, 2].astype(str),
                '비고(장비)': work_raw.apply(lambda r: ", ".join(filter(None, [
                    get_equip_text(r, 5, 6, "SCH"), get_equip_text(r, 7, 8, "KAM")
                ])), axis=1)
            })

            # --- 2. 근태 현황 (0번행 제목 제외) ---
            att_raw = df.iloc[11:18, [0, 1, 4]].dropna(how='all')
            att_df = pd.DataFrame({
                '팀명': t_name,
                '구분': att_raw.iloc[:, 0].astype(str),
                '관리자': att_raw.iloc[:, 1].astype(str),
                '인원 현황': att_raw.iloc[:, 2].astype(str)
            })

            # --- 3. 차기 예정 작업 (0번행 제목 제외) ---
            plan_raw = df.iloc[21:26, :].dropna(subset=[df.columns[0]])
            plan_df = pd.DataFrame({
                '팀명': t_name,
                '화주명': plan_raw.iloc[:, 0].astype(str),
                '예정내용': plan_raw.iloc[:, 1].astype(str),
                '예정일정': plan_raw.iloc[:, 2].astype(str),
                '비고': plan_raw.apply(lambda r: ", ".join(filter(None, [
                    get_equip_text(r, 5, 6, "SCH"), get_equip_text(r, 7, 8, "KAM")
                ])), axis=1)
            })
        else:
            # 물류/하역팀 기본 구성
            work_df = pd.DataFrame({'팀명':[t_name], '화주명':['일보 참조'], '작업내용':['-'], '관리자':['-'], '비고(장비)':['-']})
            att_df = pd.DataFrame({'팀명':[t_name], '구분':['상세 확인'], '관리자':['-'], '인원 현황':['-']})
            plan_df = pd.DataFrame({'팀명':[t_name], '화주명':['-'], '예정내용':['-'], '예정일정':['-'], '비고':['-']})

        # "화주", "작업 내용" 등 제목이 들어간 행 최종 필터링
        work_df = work_df[work_df['화주명'] != '화주']
        plan_df = plan_df[plan_df['화주명'] != '화주']
        
        return work_df, att_df, plan_df

    except Exception as e:
        st.error(f"{t_name} 처리 중 오류: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 병합 및 탭 출력
h_w, h_a, h_p = extract_refined_sections(heavy_file, 'heavy')
l_w, l_a, l_p = extract_refined_sections(logis_file, 'logis')
d_w, d_a, d_p = extract_refined_sections(dock_file, 'dock')

tab1, tab2, tab3, tab4 = st.tabs(["📊 종합 현황", "🚚 경남중량팀", "📦 경남물류운영팀", "⚓ 경남하역팀"])

with tab1:
    if any([heavy_file, logis_file, dock_file]):
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
        st.info("파일을 업로드하면 통합 데이터가 표시됩니다.")

# 상세 탭
with tab2: st.write(h_w)
with tab3: st.write(l_w)
with tab4: st.write(d_w)
