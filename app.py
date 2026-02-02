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

# 3. 데이터 처리 함수
def process_all_sections(file, team_type):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    team_names = {'heavy': '경남중량팀', 'logis': '경남물류운영팀', 'dock': '경남하역팀'}
    t_name = team_names[team_type]
    
    try:
        # 중량팀은 2행 건너뛰기
        skip = 2 if team_type == 'heavy' else 0
        raw_df = pd.read_excel(file, skiprows=skip)
        
        # --- [1. 금일 작업 현황] ---
        work_data = pd.DataFrame()
        if team_type == 'heavy':
            # '2. 근태 현황' 직전까지가 작업 현황 (대기 장비 행 제외를 위해 위치 계산)
            # 보통 1번 섹션은 3~8행 사이이므로 유동적으로 슬라이싱
            df_work = raw_df.iloc[:5, :] # 마지막 '대기 장비' 행을 제외하기 위해 인덱스 조정
            
            work_data['팀명'] = [t_name] * len(df_work)
            work_data['화주명'] = df_work.iloc[:, 0].fillna('-')
            work_data['작업내용'] = df_work.iloc[:, 1].fillna('-')
            work_data['관리자'] = df_work.iloc[:, 2].fillna('-') # 관리자 열 추가
            
            def get_equip_detail(row):
                items = []
                try:
                    s_axle = pd.to_numeric(row.iloc[5], errors='coerce')
                    s_ppu = pd.to_numeric(row.iloc[6], errors='coerce')
                    k_axle = pd.to_numeric(row.iloc[7], errors='coerce')
                    k_ppu = pd.to_numeric(row.iloc[8], errors='coerce')
                    
                    if s_axle > 0: items.append(f"SCH({int(s_axle)}축, {int(s_ppu)}P.P)")
                    if k_axle > 0: items.append(f"KAM({int(k_axle)}축, {int(k_ppu)}P.P)")
                except: pass
                return ", ".join(items) if items else "-"
            work_data['비고(장비)'] = df_work.apply(get_equip_detail, axis=1)
        else:
            work_data['팀명'] = [t_name] * len(raw_df)
            work_data['화주명'] = raw_df.get('화주명', raw_df.get('화주', '-'))
            work_data['작업내용'] = raw_df.get('작업내용', raw_df.get('작업형태', '-'))
            work_data['관리자'] = raw_df.get('담당자', raw_df.get('대리점', '-'))
            work_data['비고(장비)'] = raw_df.get('비고', '-')

        # --- [2. 근태 현황] ---
        att_data = pd.DataFrame()
        if team_type == 'heavy':
            # 중량팀 엑셀 중간의 근태 섹션 추출 (위치 기반)
            df_att = raw_df.iloc[10:17, [0, 1, 3]] # 구분, 관리자, 기사+다기능
            att_data['팀명'] = [t_name] * len(df_att)
            att_data['구분'] = df_att.iloc[:, 0].fillna('-')
            att_data['관리자'] = df_att.iloc[:, 1].fillna('-')
            att_data['기사/기타'] = df_att.iloc[:, 2].fillna('-')
        else:
            att_data = pd.DataFrame({'팀명':[t_name], '내용':['팀별 상세 탭 확인']})

        # --- [3. 향후 예정 작업] ---
        plan_data = pd.DataFrame()
        if team_type == 'heavy':
            # 중량팀 하단 차기 예정 작업 (3. 차기 예정 작업 제목 이후)
            df_plan = raw_df.iloc[20:, [0, 1, 2, 3, 4, 5, 6, 7]] 
            plan_data['팀명'] = [t_name] * len(df_plan)
            plan_data['화주명'] = df_plan.iloc[:, 0].fillna('-')
            plan_data['예정내용'] = df_plan.iloc[:, 1].fillna('-')
            plan_data['예정일정'] = df_plan.iloc[:, 2].fillna('-')
            # 예정 작업 비고에도 장비 세부 기입
            plan_data['비고'] = df_plan.apply(get_equip_detail, axis=1)
        else:
            plan_data = pd.DataFrame({
                '팀명':[t_name], '화주명':['-'], '예정내용':['일보 참조'], 
                '예정일정':['-'], '비고':['-']
            })

        return work_data, att_data, plan_data

    except Exception as e:
        st.error(f"{t_name} 처리 중 오류: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로드
h_w, h_a, h_p = process_all_sections(heavy_file, 'heavy')
l_w, l_a, l_p = process_all_sections(logis_file, 'logis')
d_w, d_a, d_p = process_all_sections(dock_file, 'dock')

# 통합 데이터
total_work = pd.concat([h_w, l_w, d_w], ignore_index=True).query("화주명 != '-'")
total_att = pd.concat([h_a, l_a, d_a], ignore_index=True)
total_plan = pd.concat([h_p, l_p, d_p], ignore_index=True).query("화주명 != '-'")

# 화면 출력
t1, t2, t3, t4 = st.tabs(["📊 종합 현황", "🚚 경남중량팀", "📦 경남물류운영팀", "⚓ 경남하역팀"])

with t1:
    if not total_work.empty:
        st.subheader("🗓️ 1. 금일 작업 현황")
        st.dataframe(total_work, use_container_width=True)
        
        st.markdown("---")
        st.subheader("👥 2. 팀별 근태 현황")
        st.dataframe(total_att, use_container_width=True)
        
        st.markdown("---")
        st.subheader("📝 3. 향후 예정 작업")
        # 요청하신 팀명, 화주명, 예정내용, 예정일정, 비고 구성
        st.dataframe(total_plan[['팀명', '화주명', '예정내용', '예정일정', '비고']], use_container_width=True)
    else:
        st.info("파일을 업로드하면 통합 리포트가 생성됩니다.")

# 개별 탭은 원본 데이터 확인용
with t2: st.write(h_w)
with t3: st.write(l_w)
with t4: st.write(d_w)
