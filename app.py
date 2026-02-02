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

# 3. 데이터 처리 함수 (오류 방지 및 세분화)
def process_all_sections(file, team_type):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # 팀 이름 매핑
    team_names = {'heavy': '경남중량팀', 'logis': '경남물류운영팀', 'dock': '경남하역팀'}
    t_name = team_names[team_type]
    
    try:
        # 엑셀 읽기 (중량팀은 제목 위치 고려)
        skip = 2 if team_type == 'heavy' else 0
        raw_df = pd.read_excel(file, skiprows=skip)
        
        # --- [1. 작업 현황] 추출 ---
        work_data = pd.DataFrame()
        if team_type == 'heavy':
            # 중량팀: 1. 금일 작업 현황 섹션만 추출 (근태 현황 전까지)
            df_work = raw_df.iloc[:6, :] # 상단 6줄 정도가 작업 현황
            work_data['팀명'] = [t_name] * len(df_work)
            work_data['화주명'] = df_work.iloc[:, 0].fillna('-')
            work_data['작업내용'] = df_work.iloc[:, 1].fillna('-')
            
            # 장비 비고 (오류 방지를 위해 숫자 변환 추가)
            def check_equip(row):
                items = []
                try:
                    s_axle = pd.to_numeric(row.iloc[5], errors='coerce')
                    k_axle = pd.to_numeric(row.iloc[7], errors='coerce')
                    if s_axle > 0: items.append(f"SCH({int(s_axle)}축)")
                    if k_axle > 0: items.append(f"KAM({int(k_axle)}축)")
                except: pass
                return ", ".join(items) if items else "-"
            work_data['비고'] = df_work.apply(check_equip, axis=1)
        else:
            # 물류/하역팀 기본 추출
            work_data['팀명'] = [t_name] * len(raw_df)
            work_data['화주명'] = raw_df.get('화주명', raw_df.get('화주', '-'))
            work_data['작업내용'] = raw_df.get('작업내용', raw_df.get('작업형태', '-'))
            work_data['비고'] = raw_df.get('비고', '-')

        # --- [2. 근태 현황] 추출 ---
        att_data = pd.DataFrame()
        if team_type == 'heavy':
            # 중량팀 엑셀 하단 '2. 근태 현황' 부분 타겟팅
            df_att = raw_df.iloc[10:17, 0:5] # 위치 기반 추출
            att_data['팀명'] = [t_name] * len(df_att)
            att_data['구분'] = df_att.iloc[:, 0].fillna('-')
            att_data['인원/내용'] = df_att.iloc[:, 1].fillna('-')
        else:
            att_data = pd.DataFrame({'팀명':[t_name], '구분':['일보 참조'], '인원/내용':['파일 확인 요망']})

        # --- [3. 예정 작업] 추출 ---
        plan_data = pd.DataFrame()
        if team_type == 'heavy':
            df_plan = raw_df.iloc[20:, 0:4] # 하단 예정 작업 섹션
            plan_data['팀명'] = [t_name] * len(df_plan)
            plan_data['화주명'] = df_plan.iloc[:, 0].fillna('-')
            plan_data['예정내용'] = df_plan.iloc[:, 1].fillna('-')
        else:
            plan_data = pd.DataFrame({'팀명':[t_name], '예정내용':['일보 하단 참조']})

        return work_data, att_data, plan_data

    except Exception as e:
        st.error(f"{t_name} 처리 중 오류 발생: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로드
h_w, h_a, h_p = process_all_sections(heavy_file, 'heavy')
l_w, l_a, l_p = process_all_sections(logis_file, 'logis')
d_w, d_a, d_p = process_all_sections(dock_file, 'dock')

# 통합 데이터 생성 (팀명 한글 적용됨)
total_work = pd.concat([h_w, l_w, d_w], ignore_index=True).dropna(subset=['화주명'])
total_att = pd.concat([h_a, l_a, d_a], ignore_index=True)
total_plan = pd.concat([h_p, l_p, d_p], ignore_index=True).dropna(subset=['팀명'])

# 탭 구성
t_total, t_heavy, t_logis, t_dock = st.tabs(["📊 종합 현황", "🚚 경남중량팀", "📦 경남물류운영팀", "⚓ 경남하역팀"])

with t_total:
    if not total_work.empty:
        st.subheader("🗓️ 1. 금일 작업 현황")
        st.dataframe(total_work, use_container_width=True)
        
        st.markdown("---")
        st.subheader("👥 2. 팀별 근태 현황")
        st.dataframe(total_att, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📝 3. 향후 예정 작업")
        st.dataframe(total_plan, use_container_width=True)
    else:
        st.info("파일을 업로드하면 통합 리포트가 생성됩니다.")

# 각 팀별 상세 탭
with t_heavy: st.dataframe(h_w)
with t_logis: st.dataframe(l_w)
with t_dock: st.dataframe(d_w)
