import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="전사 작업 현황 통합 관리", layout="wide")

st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 사이드바 파일 업로드
st.sidebar.header("📁 팀별 작업일보 업로드")
heavy_file = st.sidebar.file_uploader("중량팀 일보 (.xlsx)", type=['xlsx'])
logis_file = st.sidebar.file_uploader("물류운영팀 일보 (.xlsx)", type=['xlsx'])
dock_file = st.sidebar.file_uploader("하역팀 일보 (.xlsx)", type=['xlsx'])

# 공통 데이터 처리 함수 (오류 방지용)
def safe_process(file, team_type):
    if file is None: return pd.DataFrame()
    
    try:
        # 중량팀은 2행부터 데이터 시작, 나머지는 기본 읽기
        skip = 2 if team_type == 'heavy' else 0
        df = pd.read_excel(file, skiprows=skip)
        
        # 3팀 공통 형식으로 변환 (열이 없으면 빈칸 처리)
        new_df = pd.DataFrame()
        new_df['팀명'] = [team_type.upper()] * len(df)
        
        if team_type == 'heavy':
            new_df['화주명'] = df.iloc[:, 0] # 첫번째 열(화주)
            new_df['작업내용 및 진행상황'] = df.iloc[:, 1] # 두번째 열(작업내용)
            new_df['담당자'] = df.iloc[:, 2] # 세번째 열(관리자)
            
            # 자가장비 비고 로직 (중량팀 특화)
            def get_heavy_rem(row):
                rem = []
                # 엑셀 위치에 따라 인덱스(숫자)로 접근하여 장비 확인
                try:
                    if row.iloc[5] > 0: rem.append(f"SCHEUERLE({int(row.iloc[5])}축)")
                    if row.iloc[7] > 0: rem.append(f"KAMAG({int(row.iloc[7])}축)")
                except: pass
                return ", ".join(rem) if rem else "-"
            new_df['비고'] = df.apply(get_heavy_rem, axis=1)
            
        elif team_type == 'logis':
            new_df['화주명'] = df.get('화주명', '-')
            new_df['작업내용 및 진행상황'] = df.get('진행사항', '-')
            new_df['담당자'] = df.get('담당자', '-')
            new_df['비고'] = df.get('예정사항', '-')
            
        else: # 하역팀
            new_df['화주명'] = df.get('화주명', '-')
            new_df['작업내용 및 진행상황'] = df.get('작업형태', '-')
            new_df['담당자'] = df.get('대리점', '-')
            new_df['비고'] = df.get('비고', '-')
            
        return new_df.dropna(subset=['화주명']) # 화주가 없는 빈 줄은 삭제
    except Exception as e:
        st.error(f"{team_type} 파일 처리 중 오류 발생: {e}")
        return pd.DataFrame()

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["📊 종합 현황", "🚚 중량팀", "📦 물류운영팀", "⚓ 하역팀"])

df_h = safe_process(heavy_file, 'heavy')
df_l = safe_process(logis_file, 'logis')
df_d = safe_process(dock_file, 'dock')

with tab1:
    if heavy_file or logis_file or dock_file:
        all_df = pd.concat([df_h, df_l, df_d], ignore_index=True)
        st.subheader("📋 통합 상세 내역")
        st.dataframe(all_df, use_container_width=True)
    else:
        st.info("왼쪽에서 엑셀 파일을 업로드해주세요!")

with tab2: st.dataframe(df_h)
with tab3: st.dataframe(df_l)
with tab4: st.dataframe(df_d)
