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
def process_data(file, team_type):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # 팀 이름 한글 매핑
    team_names = {
        'heavy': '경남중량팀',
        'logis': '경남물류운영팀',
        'dock': '경남하역팀'
    }
    t_name = team_names[team_type]
    
    try:
        # 중량팀은 2행 건너뛰기, 나머지는 기본
        skip = 2 if team_type == 'heavy' else 0
        df = pd.read_excel(file, skiprows=skip)
        
        # --- [1. 작업 현황] 데이터 추출 ---
        work_df = pd.DataFrame()
        work_df['팀명'] = [t_name] * len(df)
        if team_type == 'heavy':
            work_df['화주명'] = df.iloc[:, 0].fillna('-')
            work_df['작업내용'] = df.iloc[:, 1].fillna('-')
            work_df['비고'] = df.apply(lambda r: f"SCHEUERLE({int(r.iloc[5])}축)" if pd.notnull(r.iloc[5]) and r.iloc[5] > 0 else "-", axis=1)
        else:
            work_df['화주명'] = df.get('화주명', '-')
            work_df['작업내용'] = df.get('작업내용', df.get('작업형태', '-'))
            work_df['비고'] = df.get('비고', '-')

        # --- [2. 근태 현황] 데이터 추출 ---
        # 엑셀 시트 구조에 따라 각 팀별 인원 정보를 가져옵니다
        att_df = pd.DataFrame({
            '팀명': [t_name],
            '투입인원': [len(df)], # 예시로 행 개수 활용, 실제 엑셀 숫자로 변경 가능
            '상세': ["정상 근무"]
        })

        # --- [3. 예정 작업] 데이터 추출 ---
        plan_df = work_df.copy() # 예정 데이터가 있는 열을 지정하여 추출 가능

        return work_df, att_df, plan_df
        
    except Exception as e:
        st.error(f"{t_name} 처리 중 오류: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 4. 데이터 로드 및 병합
h_work, h_att, h_plan = process_data(heavy_file, 'heavy')
l_work, l_att, l_plan = process_data(logis_file, 'logis')
d_work, d_att, d_plan = process_data(dock_file, 'dock')

all_work = pd.concat([h_work, l_work, d_work], ignore_index=True)
all_att = pd.concat([h_att, l_att, d_att], ignore_index=True)
all_plan = pd.concat([h_plan, l_plan, d_plan], ignore_index=True)

# 5. 화면 출력 (종합 현황 탭)
tab1, tab2, tab3, tab4 = st.tabs(["📊 종합 현황", "🚚 경남중량팀", "📦 경남물류운영팀", "⚓ 경남하역팀"])

with tab1:
    if not all_work.empty:
        # 섹션 1: 작업 현황
        st.subheader("1️⃣ 금일 작업 현황")
        st.dataframe(all_work, use_container_width=True)
        
        st.divider()
        
        # 섹션 2: 근태 현황
        st.subheader("2️⃣ 팀별 근태 현황")
        st.table(all_att)
        
        st.divider()
        
        # 섹션 3: 예정 작업
        st.subheader("3️⃣ 향후 예정 작업")
        st.dataframe(all_plan, use_container_width=True)
    else:
        st.info("사이드바에서 파일을 업로드해 주세요.")

# 팀별 상세 탭 (생략 가능 또는 데이터 프레임 출력)
with tab2: st.dataframe(h_work)
with tab3: st.dataframe(l_work)
with tab4: st.dataframe(d_work)
