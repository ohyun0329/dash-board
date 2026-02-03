import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="세방(주) 통합 작업 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")
st.markdown("---")

# 2. 사이드바 파일 업로드
st.sidebar.header("📁 팀별 작업일보 업로드")
heavy_file = st.sidebar.file_uploader("🚚 경남중량팀 일보", type=['xlsx'])
dock_file = st.sidebar.file_uploader("⚓ 경남하역팀 일보", type=['xlsx'])

# 3. 데이터 추출 엔진 (하역팀 열 위치 보정)
def extract_team_data_v3(file, team_name):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        df = pd.read_excel(file, header=None)
        
        # 키워드 위치 찾기 (A열 우선 검색)
        def find_row_strict(keyword):
            mask = df.iloc[:, 0].astype(str).str.strip() == keyword
            match = df[mask].index
            return match[0] if not match.empty else None

        idx_w = find_row_strict("[금일 작업]")
        idx_p = find_row_strict("[예정 작업]")
        idx_a = find_row_strict("[근태 현황]")

        # 섹션 간 경계 인덱스 정리
        all_idxs = sorted([i for i in [idx_w, idx_p, idx_a, len(df)] if i is not None])
        def get_next_idx(current):
            for i in all_idxs:
                if i > current: return i
            return len(df)

        # 공통 정제 함수
        def clean(d, col_name):
            if d.empty: return d
            kill_list = ["[금일", "[근태", "[예정", "화주", "본선", "구분", "작업", "관리자", "nan", "None", "일보"]
            mask = d[col_name].astype(str).apply(
                lambda x: not any(k in x.replace(" ", "") for k in kill_list) and x.strip() != "nan" and x.strip() != ""
            )
            return d[mask].reset_index(drop=True)

        # 1. 금일 작업
        if idx_w is not None:
            end = get_next_idx(idx_w)
            raw = df.iloc[idx_w+2:end, :] 
            if "중량" in team_name:
                w_df = pd.DataFrame({
                    '팀명': team_name, '화주/본선': raw.iloc[:, 0], '작업내용': raw.iloc[:, 1], '비고': raw.iloc[:, 2]
                })
            else: # 하역팀 (공유양식 기반: 화주 6번열, 작업내용 7번열)
                # 데이터가 비어있을 경우를 대비해 fillna 처리
                w_df = pd.DataFrame({
                    '팀명': team_name, 
                    '화주/본선': raw.iloc[:, 6].fillna(raw.iloc[:, 0]),
                    '작업내용': raw.iloc[:, 7].fillna(raw.iloc[:, 11]), # 하역팀 특성 반영
                    '투입인원': raw.iloc[:, 8],
                    '비고': raw.iloc[:, 9]
                })
            w_final = clean(w_df, '화주/본선')
        else: w_final = pd.DataFrame()

        # 2. 근태 현황 (하역팀: 구분 0번, 인원 1번)
        if idx_a is not None:
            end = get_next_idx(idx_a)
            raw_a = df.iloc[idx_a+2:end, [0, 1]].dropna(subset=[0])
            a_df = pd.DataFrame(raw_a.values, columns=['구분', '현황'])
            a_df.insert(0, '팀명', team_name)
            a_final = a_df[~a_df['구분'].astype(str).str.contains("구분|근태", na=False)].reset_index(drop=True)
        else: a_final = pd.DataFrame()

        # 3. 예정 작업
        if idx_p is not None:
            end = get_next_idx(idx_p)
            raw_p = df.iloc[idx_p+2:end, :]
            if "중량" in team_name:
                p_df = pd.DataFrame({
                    '팀명': team_name, '화주/본선': raw_p.iloc[:, 0], '예정내용': raw_p.iloc[:, 1], '일정': raw_p.iloc[:, 2]
                })
            else: # 하역팀 (일정 1번열, 화주 6번열, 내용 7번열)
                p_df = pd.DataFrame({
                    '팀명': team_name, 
                    '화주/본선': raw_p.iloc[:, 6].fillna(raw_p.iloc[:, 0]),
                    '예정내용': raw_p.iloc[:, 7], 
                    '일정': raw_p.iloc[:, 1],
                    '비고': raw_p.iloc[:, 9]
                })
            p_final = clean(p_df, '화주/본선')
        else: p_final = pd.DataFrame()

        return w_final, a_final, p_final

    except Exception:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로드 및 출력
h_w, h_a, h_p = extract_team_data_v3(heavy_file, "중량팀")
d_w, d_a, d_p = extract_team_data_v3(dock_file, "하역팀")

t = st.tabs(["📊 종합 현황", "🚚 중량팀 상세", "⚓ 하역팀 상세"])

with t[0]:
    if heavy_file or dock_file:
        st.subheader("🗓️ 1. 전사 금일 작업")
        st.dataframe(pd.concat([h_w, d_w], ignore_index=True), use_container_width=True)
        st.subheader("👥 2. 전사 근태 현황")
        st.dataframe(pd.concat([h_a, d_a], ignore_index=True), use_container_width=True)
        st.subheader("📅 3. 전사 예정 작업")
        st.dataframe(pd.concat([h_p, d_p], ignore_index=True), use_container_width=True)
    else:
        st.info("사이드바에서 파일을 업로드해 주세요.")

with t[1]: st.write("중량팀 상세 결과", h_w, h_a, h_p)
with t[2]: st.write("하역팀 상세 결과", d_w, d_a, d_p)
