import streamlit as st
import pandas as pd

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="세방(주) 경남지사 통합 관리", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    h1 { color: #003366; border-bottom: 2px solid #003366; padding-bottom: 10px; }
    .total-card { 
        background-color: #ffffff; padding: 20px; border-radius: 10px; 
        border-left: 5px solid #003366; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .merged-table { width: 100%; border-collapse: collapse; background: white; margin-bottom: 20px; table-layout: fixed; }
    .merged-table th { 
        background-color: #003366; color: white; padding: 12px; border: 1px solid #ddd; 
        text-align: center !important; vertical-align: middle !important;
    }
    .merged-table td { padding: 10px; border: 1px solid #ddd; text-align: center; vertical-align: middle; word-break: break-all; }
    .cat-cell { background-color: #f0f2f6; font-weight: bold; width: 100px; }
    .status-cell { width: 35%; }
    </style>
""", unsafe_allow_html=True)

st.title("🏗️ 세방(주) 경남지사 통합 작업 관리 시스템")

# 2. 구글 시트 연결 정보
SHEET_LINKS = {
    "경남중량팀": "https://docs.google.com/spreadsheets/d/1yyfSsY7MEeOQkli8NL1Hd_A_ufpCU9_5EQufv4eLzD8/export?format=xlsx",
    "경남하역팀": "https://docs.google.com/spreadsheets/d/11mNUhbw3h_YUSUX_VugWiiNF4cQLMCFOVtQhJ6arkBU/export?format=xlsx",
    "경남물류운영팀": "https://docs.google.com/spreadsheets/d/1RY1Eevut6CTLR3r8g9OFXz4ZePkGRjE0LaclSjYMb_s/export?format=xlsx"
}

# 인원 카운트 함수
def count_names(val):
    val_str = str(val)
    if not val or val_str in ["-", "nan", "None", ""]: return 0
    return len([n for n in val_str.replace("/", ",").split(",") if n.strip()])

# 3. 데이터 추출 엔진 (구글 시트 전용)
def load_sheet_data(url, team_name):
    try:
        # 구글 시트 로드 (가장 마지막 탭 자동 선택)
        xl = pd.ExcelFile(url)
        last_sheet = xl.sheet_names[-1]
        df = xl.parse(last_sheet, header=None)
        
        def find_anchor(keyword):
            series = df.iloc[:, 0].astype(str).str.replace(" ", "")
            target = keyword.replace(" ", "")
            match = df[series == target].index
            return match[0] if not match.empty else None

        idx_w = find_anchor("[금일 작업]")
        idx_p = find_anchor("[예정 작업]")
        idx_a = find_anchor("[근태 현황]")

        all_indices = sorted([i for i in [idx_w, idx_p, idx_a, len(df)] if i is not None])
        def get_end(start):
            for i in all_indices:
                if i > start: return i
            return len(df)

        def clean_section(d, col_name):
            if d.empty: return d
            # 제목행 필터링 및 데이터 정제
            stops = ["화주", "본선", "구분", "내용", "입항", "인원", "nan", "None"]
            mask = d[col_name].astype(str).apply(lambda x: not any(s in x for s in stops))
            d = d[mask].copy()
            d[col_name] = d[col_name].ffill()
            return d.dropna(subset=d.columns.difference(['팀명']), how='all').reset_index(drop=True)

        # 1. 금일 작업 추출
        if idx_w is not None:
            raw_w = df.iloc[idx_w+2:get_end(idx_w), :]
            # 열 위치가 바뀌어도 제목으로 찾기 (데이터 프레임 재구성)
            # 중량/물류는 유사 구조, 하역은 특수 구조 유지
            if "하역" in team_name:
                w_df = pd.DataFrame({'팀명': team_name, '화주': raw_w.iloc[:, 6].fillna(raw_w.iloc[:, 0]), '작업내용': raw_w.iloc[:, 7], '투입인원': raw_w.iloc[:, 8], '비고': raw_w.iloc[:, 9]})
            else:
                w_df = pd.DataFrame({'팀명': team_name, '화주': raw_w.iloc[:, 0], '작업내용': raw_w.iloc[:, 1], '투입인원': raw_w.iloc[:, 2], '비고': raw_w.iloc[:, 3] if len(raw_w.columns) > 3 else "-"})
            w_final = clean_section(w_df, '화주')
        else: w_final = pd.DataFrame()

        # 2. 예정 작업 추출
        if idx_p is not None:
            raw_p = df.iloc[idx_p+2:get_end(idx_p), :]
            if "하역" in team_name:
                p_df = pd.DataFrame({'팀명': team_name, '화주': raw_p.iloc[:, 6].fillna(raw_p.iloc[:, 0]), '예정내용': raw_p.iloc[:, 7], '일정': raw_p.iloc[:, 1]})
            else:
                p_df = pd.DataFrame({'팀명': team_name, '화주': raw_p.iloc[:, 0], '예정내용': raw_p.iloc[:, 1], '일정': raw_p.iloc[:, 2]})
            p_final = clean_section(p_df, '화주')
        else: p_final = pd.DataFrame()

        # 3. 근태 현황 추출
        if idx_a is not None:
            raw_a = df.iloc[idx_a+2:get_end(idx_a), [0, 1, 2]].dropna(subset=[0])
            a_df = pd.DataFrame({
                '구분': raw_a.iloc[:, 0].astype(str).str.strip().replace({'본선 작업':'작업','육상 작업':'작업','연차':'휴가'}),
                '팀명': team_name,
                '관리자 현황': raw_a.iloc[:, 1].fillna("-").astype(str),
                '기사/다기능/선원 현황': raw_a.iloc[:, 2].fillna("-").astype(str)
            })
            a_final = a_df[a_df['구분'].isin(['작업', '내무', '출장', '휴가'])].reset_index(drop=True)
        else: a_final = pd.DataFrame()

        return w_final, a_final, p_final
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 통합 로드
with st.spinner('구글 시트에서 최신 데이터를 불러오는 중...'):
    h_w, h_a, h_p = load_sheet_data(SHEET_LINKS["경남중량팀"], "경남중량팀")
    d_w, d_a, d_p = load_sheet_data(SHEET_LINKS["경남하역팀"], "경남하역팀")
    m_w, m_a, m_p = load_sheet_data(SHEET_LINKS["경남물류운영팀"], "경남물류운영팀")

tabs = st.tabs(["📊 종합 현황", "🚚 중량팀", "⚓ 하역팀", "📦 물류운영팀"])

with tabs[0]:
    # 3개 팀 데이터 병합
    all_att = pd.concat([h_a, d_a, m_a], ignore_index=True)
    all_w = pd.concat([h_w, d_w, m_w], ignore_index=True)
    all_p = pd.concat([h_p, d_p, m_p], ignore_index=True)

    if not all_att.empty:
        m_total = all_att['관리자 현황'].apply(count_names).sum()
        f_total = all_att['기사/다기능/선원 현황'].apply(count_names).sum()
        st.markdown(f"""<div class="total-card"><h3>📢 경남지사 금일 투입 총원: {m_total + f_total}명</h3>
                    <p>관리자: {m_total}명 | 기사/다기능/선원: {f_total}명</p></div>""", unsafe_allow_html=True)

    # 1. 금일 작업
    st.subheader("1. 금일 작업")
    if not all_w.empty:
        summary_w = all_w.groupby('팀명').agg(list).reset_index()
        html_w = "<table class='merged-table'><tr><th style='width:120px;'>팀명</th><th>화주</th><th>작업내용</th><th style='width:150px;'>투입인원</th><th>비고</th></tr>"
        for _, row in summary_w.iterrows():
            row_span = len(row['화주'])
            for i in range(row_span):
                html_w += f"<tr>"
                if i == 0: html_w += f"<td class='cat-cell' rowspan='{row_span}'>{row['팀명']}</td>"
                html_w += f"<td>{row['화주'][i]}</td><td>{row['작업내용'][i]}</td><td>{row['투입인원'][i]}</td><td>{row['비고'][i]}</td></tr>"
        st.write(html_w + "</table>", unsafe_allow_html=True)

    st.divider()

    # 2. 근태 현황
    st.subheader("2. 근태 현황")
    if not all_att.empty:
        order = {'작업':0, '내무':1, '출장':2, '휴가':3}
        all_att['ord'] = all_att['구분'].map(order).fillna(4)
        summary_a = all_att.sort_values(['ord', '팀명']).groupby('구분').agg(list).reset_index()
        summary_a = summary_a.sort_values('구분', key=lambda x: x.map(order))
        html_a = "<table class='merged-table'><tr><th class='cat-cell'>구분</th><th class='team-cell'>팀명</th><th class='status-cell'>관리자 현황</th><th class='status-cell'>기사, 다기능, 선원 현황</th></tr>"
        for _, row in summary_a.iterrows():
            row_span = len(row['팀명'])
            for i in range(row_span):
                html_a += "<tr>"
                if i == 0: html_a += f"<td class='cat-cell' rowspan='{row_span}'>{row['구분']}</td>"
                html_a += f"<td>{row['팀명'][i]}</td><td>{row['관리자 현황'][i]}</td><td>{row['기사/다기능/선원 현황'][i]}</td></tr>"
        st.write(html_a + "</table>", unsafe_allow_html=True)

    st.divider()

    # 3. 예정 작업
    st.subheader("3. 예정 작업")
    if not all_p.empty:
        summary_p = all_p.groupby('팀명').agg(list).reset_index()
        html_p = "<table class='merged-table'><tr><th style='width:120px;'>팀명</th><th>화주</th><th>예정내용</th><th>일정</th></tr>"
        for _, row in summary_p.iterrows():
            row_span = len(row['화주'])
            for i in range(row_span):
                html_p += f"<tr>"
                if i == 0: html_p += f"<td class='cat-cell' rowspan='{row_span}'>{row['팀명']}</td>"
                html_p += f"<td>{row['화주'][i]}</td><td>{row['예정내용'][i]}</td><td>{row['일정'][i]}</td></tr>"
        st.write(html_p + "</table>", unsafe_allow_html=True)

# 개별 팀 탭 생략 (종합 뷰와 동일 로직)
st.sidebar.info("💡 구글 시트에서 데이터를 실시간으로 가져옵니다. 담당자가 시트를 수정하면 새로고침 시 반영됩니다.")
