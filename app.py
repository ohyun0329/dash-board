import streamlit as st
import pandas as pd

# 1. 페이지 설정 및 디자인 (경남지사 명칭 적용)
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

# 3. 데이터 추출 엔진
def extract_data_final(file, team_name):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    try:
        df = pd.read_excel(file, header=None)
        
        # 키워드 위치 찾기 함수
        def find_anchor(kw):
            clean_kw = kw.replace(" ", "")
            for col in range(min(df.shape[1], 2)): # A, B열 검색
                mask = df.iloc[:, col].astype(str).str.replace(" ", "").str.contains(clean_kw, na=False)
                if mask.any(): return df[mask].index[0]
            return None

        # 정확한 인덱스 찾기
        idx_w = find_anchor("[금일작업]")
        idx_p = find_anchor("[예정작업]")
        idx_a = find_anchor("[근태현황]")
        
        all_idxs = sorted([i for i in [idx_w, idx_p, idx_a, len(df)] if i is not None])
        def get_end(s):
            for i in all_idxs:
                if i > s: return i
            return len(df)

        # 공통 정제 함수
        def clean_df(target_df, check_col):
            if target_df.empty: return target_df
            # 제목이나 구분자 줄은 과감히 삭제
            stops = ["[금일", "[예정", "[근태", "화주", "본선", "구분", "내용", "입항", "인원", "nan", "None"]
            mask = target_df[check_col].astype(str).apply(
                lambda x: not any(s in x.replace(" ", "") for s in stops) and x.strip() != ""
            )
            return target_df[mask].reset_index(drop=True)

        # --- 1. 금일 작업 ---
        if idx_w is not None:
            raw_w = df.iloc[idx_w+1:get_end(idx_w), :] # 제목줄 포함해서 일단 읽음
            if "중량" in team_name:
                # 중량팀: 0:화주, 1:작업내용, 2:관리자
                w_df = pd.DataFrame({
                    '팀명': team_name, '화주명': raw_w.iloc[:, 0], '작업내용': raw_w.iloc[:, 1], '관리자': raw_w.iloc[:, 2]
                })
                w_final = clean_df(w_df, '화주명')
            else: # 하역팀: 6:화주명(없으면 0번), 7:작업내용, 9:비고
                w_df = pd.DataFrame({
                    '팀명': team_name, '화주/본선': raw_w.iloc[:, 6].fillna(raw_w.iloc[:, 0]),
                    '작업내용': raw_w.iloc[:, 7], '비고': raw_w.iloc[:, 9]
                })
                w_final = clean_df(w_df, '화주/본선')
        else: w_final = pd.DataFrame()

        # --- 2. 근태 현황 (구분 / 팀명 / 관리자 / 다기능) ---
        if idx_a is not None:
            # 제목줄 다음(+1)부터 읽음
            raw_a = df.iloc[idx_a+1:get_end(idx_a), [0, 1, 2]].dropna(subset=[0])
            a_df = pd.DataFrame({
                '구분': raw_a.iloc[:, 0].astype(str).str.strip().replace({'작업':'작업','본선작업':'작업','육상작업':'작업','연차':'휴가'}),
                '팀명': team_name,
                '관리자 현황': raw_a.iloc[:, 1].fillna("-").astype(str),
                '다기능 현황': raw_a.iloc[:, 2].fillna("-").astype(str)
            })
            a_final = a_df[a_df['구분'].isin(['작업', '내무', '출장', '휴가'])].reset_index(drop=True)
        else: a_final = pd.DataFrame()

        # --- 3. 예정 작업 ---
        if idx_p is not None:
            raw_p = df.iloc[idx_p+1:get_end(idx_p), :]
            if "중량" in team_name:
                p_df = pd.DataFrame({
                    '팀명': team_name, '화주명': raw_p.iloc[:, 0], '예정내용': raw_p.iloc[:, 1], '일정': raw_p.iloc[:, 2]
                })
                p_final = clean_df(p_df, '화주명')
            else:
                p_df = pd.DataFrame({
                    '팀명': team_name, '화주/본선': raw_p.iloc[:, 6].fillna(raw_p.iloc[:, 0]),
                    '예정내용': raw_p.iloc[:, 7], '일정': raw_p.iloc[:, 1]
                })
                p_final = clean_df(p_df, '화주/본선')
        else: p_final = pd.DataFrame()

        return w_final, a_final, p_final
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 실행
h_w, h_a, h_p = extract_data_final(heavy_file, "경남중량팀")
d_w, d_a, d_p = extract_data_final(dock_file, "경남하역팀")

# 인원 집계용 함수
def count_names(val):
    if not val or val == "-" or "nan" in str(val).lower(): return 0
    return len([n for n in str(val).replace("/", ",").split(",") if n.strip()])

# 탭 구성 및 출력
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
        # 중량팀과 하역팀 컬럼명 통일해서 합치기
        all_w = pd.concat([h_w.rename(columns={'화주명':'화주/본선'}), d_w], ignore_index=True)
        st.dataframe(all_w, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("👥 2. 경남지사 근태 현황")
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
        all_p = pd.concat([h_p.rename(columns={'화주명':'화주/본선'}), d_p], ignore_index=True)
        st.dataframe(all_p, use_container_width=True, hide_index=True)
    else: st.info("사이드바에서 파일을 업로드해 주세요.")

with t2: st.write("### 🚚 중량팀 상세", h_w, h_a, h_p)
with t3: st.write("### ⚓ 하역팀 상세", d_w, d_a, d_p)
