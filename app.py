import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. 페이지 기본 설정 (한글 폰트 및 레이아웃)
st.set_page_config(page_title="세방(주) 작업일보 통합 대시보드", layout="wide")

st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바: 엑셀 파일 업로드
st.sidebar.header("📁 팀별 작업일보 업로드")
heavy_file = st.sidebar.file_uploader("중량팀 일보 (.xlsx)", type=['xlsx'])
logis_file = st.sidebar.file_uploader("물류운영팀 일보 (.xlsx)", type=['xlsx'])
dock_file = st.sidebar.file_uploader("하역팀 일보 (.xlsx)", type=['xlsx'])

# --- 데이터 처리 함수 정의 ---

def process_heavy(file):
    if file is None: return pd.DataFrame()
    # 이미지 분석 결과: 2행부터 헤더가 시작되는 구조로 가정
    df = pd.read_excel(file, skiprows=2) 
    
    def get_remarks(row):
        items = []
        # 장비 투입 컬럼 확인 (이미지 내 Scheuerle, Kamag, 선박 등)
        if row.get('축수') > 0: items.append(f"SCHEUERLE({int(row['축수'])}축)")
        if row.get('축수.1') > 0: items.append(f"KAMAG({int(row['축수.1'])}축)")
        # 20001호 등 특정 키워드가 포함된 경우 추가
        if "20001" in str(row.get('작업 내용', '')): items.append("세방20001호")
        return ", ".join(items) if items else "-"

    res = pd.DataFrame({
        '팀명': '중량팀',
        '화주명': df.get('화주', '-'),
        '작업내용 및 진행상황': df.get('작업 내용', '-'),
        '담당자': df.get('관리자', '-'),
        '비고': df.apply(get_remarks, axis=1)
    })
    return res

def process_logis(file):
    if file is None: return pd.DataFrame()
    df = pd.read_excel(file, skiprows=3) # 물류팀 양식에 맞춤
    res = pd.DataFrame({
        '팀명': '물류운영팀',
        '화주명': df.get('화주명', '-'),
        '작업내용 및 진행상황': df.get('진행사항', '-'),
        '담당자': df.get('담당자', '-'),
        '비고': df.get('예정사항', '-')
    })
    return res

def process_dock(file):
    if file is None: return pd.DataFrame()
    df = pd.read_excel(file, skiprows=2)
    res = pd.DataFrame({
        '팀명': '하역팀',
        '화주명': df.get('화주명', '-'),
        '작업내용 및 진행상황': df.get('작업형태', '-'),
        '담당자': df.get('대리점', '-'),
        '비고': df.get('비고', '-')
    })
    return res

# --- 화면 구성 (탭) ---
tab_total, tab_heavy, tab_logis, tab_dock = st.tabs(["📊 종합 현황", "🚚 중량팀", "📦 물류운영팀", "⚓ 하역팀"])

# 데이터 로드
df_h = process_heavy(heavy_file)
df_l = process_logis(logis_file)
df_d = process_dock(dock_file)

# 1. 종합 현황 탭
with tab_total:
    if heavy_file or logis_file or dock_file:
        col1, col2, col3 = st.columns(3)
        combined_all = pd.concat([df_h, df_l, df_d], ignore_index=True)
        
        col1.metric("오늘의 총 작업", f"{len(combined_all)}건")
        col2.metric("참여 팀", f"{sum([1 for f in [heavy_file, logis_file, dock_file] if f])}개 팀")
        col3.metric("상태", "정상 운영")

        st.subheader("🛠️ 중량팀 장비 가동 현황")
        c_heavy1, c_heavy2 = st.columns(2)
        
        # 게이지 차트 (예시 수치, 실제 엑셀 합계값으로 연동 가능)
        with c_heavy1:
            st.write("**SCHEUERLE 축(Axle) 가동률**")
            st.progress(0.72) # 가상 수치
            st.caption("가동: 180축 / 전체: 248축 (72%)")
        with c_heavy2:
            st.write("**KAMAG 축(Axle) 가동률**")
            st.progress(0.52) # 가상 수치
            st.caption("가동: 70축 / 전체: 134축 (52%)")

        st.divider()
        st.subheader("📋 통합 상세 내역")
        st.dataframe(combined_all, use_container_width=True)
    else:
        st.info("사이드바에서 엑셀 파일을 업로드하면 대시보드가 생성됩니다.")

# 2~4. 팀별 상세 탭
with tab_heavy:
    st.subheader("🚚 중량팀 상세 데이터")
    st.dataframe(df_h, use_container_width=True)

with tab_logis:
    st.subheader("📦 물류운영팀 상세 데이터")
    st.dataframe(df_l, use_container_width=True)

with tab_dock:
    st.subheader("⚓ 하역팀 상세 데이터")
    st.dataframe(df_d, use_container_width=True)
