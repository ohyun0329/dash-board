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
    .merged-table { width: 100%; border-collapse: collapse; background: white; }
    .merged-table th { background-color: #003366; color: white; padding: 12px; border: 1px solid #ddd; }
    .merged-table td { padding: 10px; border: 1px solid #ddd; text-align: center; }
    .cat-cell { background-color: #f0f2f6; font-weight: bold; width: 120px; }
    </style>
""", unsafe_allow_html=True)

st.title("🏗️ 세방(주) 경남지사 통합 작업 관리 시스템")

# 2. 사이드바 파일 업로드
st.sidebar.header("📁 팀별 일보 업로드")
heavy_file = st.sidebar.file_uploader("🚚 경남중량팀", type=['xlsx'])
dock_file = st.sidebar.file_uploader("⚓ 경남하역팀", type=['xlsx'])

# 3. 데이터 추출 및 정제 엔진
def extract_data_v5(file, team_name):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    try:
        df = pd.read_excel(file, header=None)
        
        # 키워드 위치 찾기 (공백 제거 후 검색하여 오차 방지)
        def find_row(kw):
            clean_kw = kw.replace(" ", "")
            for col in range(min(df.shape[1], 2)): # A, B열 위주 검색
                mask = df.iloc[:, col].astype(str).str.replace(" ", "").str.contains(clean_kw, na=False)
                if mask.any(): return df[mask].index[0]
            return None

        idx_w = find_row("[금일작업]")
        idx_p = find_row("[예정작업]")
        idx_a = find_row("[근태현황]")
        
        all_idxs = sorted([i for i in [idx_w, idx_p, idx_a, len(df)] if i is not None])
        def get_end(s):
            for i in all_idxs:
                if i > s: return i
            return len(df)

        # 공통 정제 함수
        def clean(d, col):
            if d.empty: return d
            stops = ["[금일", "[예정", "[근태", "화주", "본선", "구분", "내용", "입항", "인원", "nan", "None", "작업구분"]
            mask = d[col].astype(str).apply(lambda x: not any(s in x.replace(" ", "") for s in stops) and x.strip() != "")
            return d[mask].reset_index(drop=True)

        # 1. 금일 작업
        if idx_w is not None:
            raw_w = df.iloc[idx_w+2:get_end(idx_w), :] 
            col_idx = 0 if "중량" in team_name else 6 # 하역팀 공유양식은 화주명이 6번열
            w_df = pd.DataFrame({
                '팀명': team_name, 
                '화주/본선': raw_w.iloc[:, col_idx].fillna(raw_w.iloc[:, 0]),
                '작업내용': raw_w.iloc[:, 1] if "중량" in team_name else raw_w.iloc[:, 7],
                '비고': raw_w.iloc[:, 14] if len(raw_w.columns) > 14 else raw_w.iloc[:, -1]
            })
            w_final = clean(w_df, '화주/본선')
        else: w_final = pd.DataFrame()

        # 2. 근태 현황 (구분 / 팀명 / 관리자 / 다기능)
        if idx_a is not None:
            raw_a = df.iloc[idx_a+2:get_end(idx_a), [0, 1, 2]].dropna(subset=[0])
            a_df = pd.DataFrame({
                '구분': raw_a.iloc[:, 0].astype(str).str.strip().replace({'작업':'관내작업','본선작업':'작업','육상작업':'작업','연차':'휴가'}),
                '팀명': team_name,
                '관리자 현황': raw_a.iloc[:, 1].fillna("-").astype(str),
                '다기능 현황': raw_a.iloc[:, 2].fillna("-").astype(str)
            })
            a_final = a_df[a_df['구분'].isin(['작업', '내무', '출장', '휴가'])].reset_index(drop=True)
        else: a_final = pd.DataFrame()

        # 3. 예정 작업
        if idx_p is not None:
            raw_p = df.iloc[idx_p+2:get_end(idx_p), :]
            col_idx = 0 if "중량" in team_name else 6
            p_df = pd.DataFrame({
                '팀명': team_name, 
                '화주/본선': raw_p.iloc[:, col_idx].fillna(raw_p.iloc[:, 0]),
                '예정내용': raw_p.iloc[:, 1] if "중량" in team_name else raw_p.iloc[:, 7],
                '일정': raw_p.iloc[:, 2] if "중량" in team_name else raw_p.iloc[:, 1]
            })
            p_final = clean(p_df, '화주/본선')
        else: p_final = pd.DataFrame()

        return w_final, a_final, p_final
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로드
h_w, h_a, h_p = extract_data_v5(heavy_file, "경남중량팀")
d_w, d_a, d_p = extract_data_v5(dock_file, "경남하역팀")

# 인원 집계 함수
def count_names(val):
    if not val or val == "-" or "nan" in str(val).lower(): return 0
    return len([n for n in str(val).replace("/", ",").split(",") if n.strip()])

# UI 출력
t1, t2, t3 = st.tabs(["📊 경남지사 종합 현황", "🚚 중량팀 상세", "⚓ 하역팀 상세"])

with t1:
    if heavy_file or dock_file:
        all_att = pd.concat([h_a, d_a], ignore_index=True)
        m_total = all_att['관리자 현황'].apply(count_names).sum()
        f_total = all_att['다기능 현황'].apply(count_names).sum()
        
        st.markdown(f"""
            <div class="total-card">
                <h3 style='margin:0; color:#003366;'>📢 경남지사 금일 투입 총원: {m_total + f_total}명</h3>
                <p style='margin:5px 0 0 0;'>관리자: {m_total}명 | 다기능: {f_total}명</p>
            </div>
        """, unsafe_allow_html=True)

        st.subheader("🗓️ 1. 경남지사 금일 작업")
        st.dataframe(pd.concat([h_w, d_w], ignore_index=True), use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("👥 2. 경남지사 근태 현황 (병합 뷰)")
        if not all_att.empty:
            order = {'작업':0, '내무':1, '출장':2, '휴가':3}
            all_att['ord'] = all_att['구분'].map(order).fillna(4)
            summary = all_att.sort_values(['ord', '팀명']).groupby('구분').agg(list).reset_index()
            summary = summary.sort_values('구분', key=lambda x: x.map(order))

            html = "<table class='merged-table'><tr><th>구분</th><th>팀명</th><th>관리자 현황</th><th>다기능 현황</th></tr>"
            for _, row in summary.iterrows():
                row_span = len(row['팀명'])
                for i in range(row_span):
                    html += "<tr>"
                    if i == 0: html += f"<td class='cat-cell' rowspan='{row_span}'>{row['구분']}</td>"
                    html += f"<td>{row['팀명'][i]}</td><td>{row['관리자 현황'][i]}</td><td>{row['다기능 현황'][i]}</td></tr>"
            st.write(html + "</table>", unsafe_allow_html=True)

        st.divider()
        st.subheader("📅 3. 경남지사 예정 작업")
        st.dataframe(pd.concat([h_p, d_p], ignore_index=True), use_container_width=True, hide_index=True)
