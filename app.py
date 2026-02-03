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
    .first-col { background-color: #f0f2f6; font-weight: bold; width: 150px !important; }
    .status-cell { width: 35%; }
    </style>
""", unsafe_allow_html=True)

st.title("🏗️ 세방(주) 경남지사 통합 작업 관리 시스템")

# 2. 구글 시트 연결 주소
SHEET_URLS = {
    "경남중량팀": "https://docs.google.com/spreadsheets/d/1yyfSsY7MEeOQkli8NL1Hd_A_ufpCU9_5EQufv4eLzD8/export?format=xlsx",
    "경남하역팀": "https://docs.google.com/spreadsheets/d/11mNUhbw3h_YUSUX_VugWiiNF4cQLMCFOVtQhJ6arkBU/export?format=xlsx",
    "경남물류운영팀": "https://docs.google.com/spreadsheets/d/1RY1Eevut6CTLR3r8g9OFXz4ZePkGRjE0LaclSjYMb_s/export?format=xlsx"
}

def count_names(val):
    val_str = str(val)
    if not val or val_str in ["-", "nan", "None", ""]: return 0
    return len([n for n in val_str.replace("/", ",").split(",") if n.strip()])

# 3. 데이터 추출 엔진 (제목 기반 매핑)
def load_data(url, team_name):
    try:
        xl = pd.ExcelFile(url)
        last_sheet = xl.sheet_names[-1]
        df = xl.parse(last_sheet, header=None)
        
        def find_row_idx(kw):
            series = df.iloc[:, 0].astype(str).str.replace(" ", "")
            target = kw.replace(" ", "")
            match = df[series == target].index
            return match[0] if not match.empty else None

        idx_w = find_row_idx("[금일 작업]")
        idx_p = find_row_idx("[예정 작업]")
        idx_a = find_row_idx("[근태 현황]")

        all_indices = sorted([i for i in [idx_w, idx_p, idx_a, len(df)] if i is not None])
        def get_end(start):
            for i in all_indices:
                if i > start: return i
            return len(df)

        def get_mapped_df(start_idx, end_idx, mapping_dict):
            if start_idx is None: return pd.DataFrame()
            # 데이터 영역 추출 (제목행 포함)
            section_df = df.iloc[start_idx+1:end_idx, :].copy()
            # 실제 데이터가 시작되는 첫 행에서 제목 찾기
            header_row = section_df.iloc[0].astype(str).str.replace(" ", "").tolist()
            section_df = section_df.iloc[1:].reset_index(drop=True)
            
            result_data = {'팀명': team_name}
            for final_col, possible_names in mapping_dict.items():
                col_idx = -1
                for idx, h_name in enumerate(header_row):
                    if any(p in h_name for p in possible_names):
                        col_idx = idx
                        break
                
                if col_idx != -1:
                    result_data[final_col] = section_df.iloc[:, col_idx]
                else:
                    result_data[final_col] = "-"
            
            res = pd.DataFrame(result_data)
            # 필터링 및 병합 처리
            res = res[res.iloc[:, 1].astype(str).str.strip() != "nan"].copy()
            res.iloc[:, 1] = res.iloc[:, 1].ffill()
            return res.reset_index(drop=True)

        # 1. 금일 작업 매핑
        w_map = {'화주':['화주','본선','고객'], '작업내용':['내용','작업'], '투입인원':['인원','성명','이름']}
        w_final = get_mapped_df(idx_w, get_end(idx_w), w_map)
        
        # 중량팀 특수 비고란(D~G열) 처리
        if "경남중량팀" in team_name and idx_w is not None:
            raw_w_data = df.iloc[idx_w+2:get_end(idx_w), :].reset_index(drop=True)
            processed_notes = []
            for _, r in raw_w_data.iterrows():
                note_parts = []
                def get_v(v): return str(v).strip() if pd.notna(v) and str(v).lower() not in ["nan", "none", "0", "0.0", ""] else ""
                
                # 중량팀 고정 위치: D(3), E(4), F(5), G(6)
                s_axle, s_ppu = get_v(r[3]), get_v(r[4])
                if s_axle or s_ppu: note_parts.append(f"쇼일레({s_axle or '0'}축, {s_ppu or '0'}PPU)")
                
                k_axle, k_ppu = get_v(r[5]), get_v(r[6])
                if k_axle or k_ppu: note_parts.append(f"까막({k_axle or '0'}축, {k_ppu or '0'}PPU)")
                
                # 비고란(H열:7) 데이터 추가
                h_note = get_v(r[7]) if len(r) > 7 else ""
                if h_note: note_parts.append(h_note)
                
                processed_notes.append(" / ".join(note_parts) if note_parts else "-")
            w_final['비고'] = processed_notes[:len(w_final)]
        else:
            w_final['비고'] = "-"

        # 2. 근태 현황 매핑
        a_map = {'구분':['구분','항목'], '관리자 현황':['관리자'], '기사/다기능/선원 현황':['다기능','기사','선원','인원']}
        a_final = get_mapped_df(idx_a, get_end(idx_a), a_map)

        # 3. 예정 작업 매핑
        p_map = {'화주':['화주','본선'], '예정내용':['내용','예정'], '일정':['일정','날짜']}
        p_final = get_mapped_df(idx_p, get_end(idx_p), p_map)

        return w_final, a_final, p_final
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 4. 데이터 로드
with st.spinner('구글 시트 로드 중...'):
    h_w, h_a, h_p = load_data(SHEET_URLS["경남중량팀"], "경남중량팀")
    d_w, d_a, d_p = load_data(SHEET_URLS["경남하역팀"], "경남하역팀")
    m_w, m_a, m_p = load_data(SHEET_URLS["경남물류운영팀"], "경남물류운영팀")

t1, t2, t3, t4 = st.tabs(["📊 종합 현황", "🚚 중량팀", "⚓ 하역팀", "📦 물류운영팀"])

with t1:
    all_att = pd.concat([h_a, d_a, m_a], ignore_index=True)
    all_w = pd.concat([h_w, d_w, m_w], ignore_index=True)
    all_p = pd.concat([h_p, d_p, m_p], ignore_index=True)

    if not all_att.empty:
        m_total_val = all_att['관리자 현황'].apply(count_names).sum()
        f_total_val = all_att['기사/다기능/선원 현황'].apply(count_names).sum()
        st.markdown(f"""<div class="total-card"><h3>📢 경남지사 금일 투입 총원: {m_total_val + f_total_val}명</h3>
                    <p>관리자: {m_total_val}명 | 기사/다기능/선원: {f_total_val}명</p></div>""", unsafe_allow_html=True)

    st.subheader("1. 금일 작업")
    if not all_w.empty:
        summary_w = all_w.groupby('팀명').agg(list).reset_index()
        html_w = "<table class='merged-table'><tr><th class='first-col'>팀명</th><th>화주</th><th>작업내용</th><th>투입인원</th><th>비고</th></tr>"
        for _, row in summary_w.iterrows():
            row_span = len(row['화주'])
            for i in range(row_span):
                html_w += f"<tr>"
                if i == 0: html_w += f"<td class='first-col' rowspan='{row_span}'>{row['팀명']}</td>"
                html_w += f"<td>{row['화주'][i]}</td><td>{row['작업내용'][i]}</td><td>{row['투입인원'][i]}</td><td>{row['비고'][i]}</td></tr>"
        st.write(html_w + "</table>", unsafe_allow_html=True)

    st.divider()
    st.subheader("2. 근태 현황")
    if not all_att.empty:
        order = {'작업':0, '내무':1, '출장':2, '휴가':3}
        all_att['ord'] = all_att['구분'].map(order).fillna(4)
        summary_a = all_att.sort_values(['ord', '팀명']).groupby('구분').agg(list).reset_index()
        summary_a = summary_a.sort_values('구분', key=lambda x: x.map(order))
        html_a = "<table class='merged-table'><tr><th class='first-col'>구분</th><th style='width:150px;'>팀명</th><th class='status-cell'>관리자 현황</th><th class='status-cell'>기사, 다기능, 선원 현황</th></tr>"
        for _, row in summary_a.iterrows():
            row_span = len(row['팀명'])
            for i in range(row_span):
                html_a += f"<tr>"
                if i == 0: html_a += f"<td class='first-col' rowspan='{row_span}'>{row['구분']}</td>"
                html_a += f"<td>{row['팀명'][i]}</td><td>{row['관리자 현황'][i]}</td><td>{row['기사/다기능/선원 현황'][i]}</td></tr>"
        st.write(html_a + "</table>", unsafe_allow_html=True)

    st.divider()
    st.subheader("3. 예정 작업")
    if not all_p.empty:
        summary_p = all_p.groupby('팀명').agg(list).reset_index()
        html_p = "<table class='merged-table'><tr><th class='first-col'>팀명</th><th>화주</th><th>예정내용</th><th>일정</th></tr>"
        for _, row in summary_p.iterrows():
            row_span = len(row['화주'])
            for i in range(row_span):
                html_p += f"<tr>"
                if i == 0: html_p += f"<td class='first-col' rowspan='{row_span}'>{row['팀명']}</td>"
                html_p += f"<td>{row['화주'][i]}</td><td>{row['예정내용'][i]}</td><td>{row['일정'][i]}</td></tr>"
        st.write(html_p + "</table>", unsafe_allow_html=True)
