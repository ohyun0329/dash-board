import streamlit as st
import pandas as pd

st.set_page_config(page_title="세방(주) 통합 작업 관리", layout="wide")
st.title("🏗️ 전사 작업 현황 통합 관리 시스템")

heavy_file = st.sidebar.file_uploader("🚚 경남중량팀 일보", type=['xlsx'])
dock_file = st.sidebar.file_uploader("⚓ 경남하역팀 일보", type=['xlsx'])

def extract_team_data_final(file, team_name):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        df = pd.read_excel(file, header=None)
        
        # --- 키워드 찾기 (엄격한 일치 방식) ---
        def find_row_strict(keyword):
            # 텍스트 앞뒤 공백 제거 후 '정확히' 일치하는지 확인
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

        # 공통 정제 함수 (데이터가 아닌 줄 삭제)
        def clean(d, col_name):
            if d.empty: return d
            # 제목이나 대괄호 문구가 섞여 들어오면 즉시 파쇄
            kill_list = ["[금일", "[근태", "[예정", "화주", "본선", "구분", "작업", "관리자", "nan", "None"]
            mask = d[col_name].astype(str).apply(
                lambda x: not any(k in x.replace(" ", "") for k in kill_list) and x.strip() != ""
            )
            return d[mask].reset_index(drop=True)

        # 1. 금일 작업
        if idx_w is not None:
            end = get_next_idx(idx_w)
            raw = df.iloc[idx_w+2:end, :] # 제목줄 건너뛰고 +2부터
            if "중량" in team_name:
                w_df = pd.DataFrame({
                    '팀명': team_name, '화주명': raw.iloc[:, 0], '작업내용': raw.iloc[:, 1], '관리자': raw.iloc[:, 2]
                })
            else: # 하역팀 (화주6, 내용7, 인원8, 비고9)
                w_df = pd.DataFrame({
                    '팀명': team_name, '화주/본선': raw.iloc[:, 6].fillna(raw.iloc[:, 0]),
                    '작업내용': raw.iloc[:, 7], '투입인원': raw_w.iloc[:, 8], '비고': raw.iloc[:, 9]
                })
            w_final = clean(w_df, '화주명' if "중량" in team_name else '화주/본선')
        else: w_final = pd.DataFrame()

        # 2. 근태 현황
        if idx_a is not None:
            end = get_next_idx(idx_a)
            # 근태는 제목줄이 1줄이므로 +1부터 읽어도 됨
            raw_a = df.iloc[idx_a+1:end, [0, 1]].dropna(subset=[0])
            a_df = pd.DataFrame(raw_a.values, columns=['구분', '인원 현황'])
            a_df.insert(0, '팀명', team_name)
            # '구분'이라는 글자가 들어간 제목행 삭제
            a_final = a_df[~a_df['구분'].astype(str).str.contains("구분|근태", na=False)].reset_index(drop=True)
        else: a_final = pd.DataFrame()

        # 3. 예정 작업
        if idx_p is not None:
            end = get_next_idx(idx_p)
            raw_p = df.iloc[idx_p+2:end, :]
            if "중량" in team_name:
                p_df = pd.DataFrame({
                    '팀명': team_name, '화주명': raw_p.iloc[:, 0], '예정내용': raw_p.iloc[:, 1], '일정': raw_p.iloc[:, 2]
                })
            else: # 하역팀 (일정1, 화주6, 내용7, 비고9)
                p_df = pd.DataFrame({
                    '팀명': team_name, '화주/본선': raw_p.iloc[:, 6].fillna(raw_p.iloc[:, 0]),
                    '예정내용': raw_p.iloc[:, 7], '일정': raw_p.iloc[:, 1], '비고': raw_p.iloc[:, 9]
                })
            p_final = clean(p_df, '화주명' if "중량" in team_name else '화주/본선')
        else: p_final = pd.DataFrame()

        return w_final, a_final, p_final

    except Exception:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 로드 및 탭 출력
h_w, h_a, h_p = extract_team_data_final(heavy_file, "중량팀")
d_w, d_a, d_p = extract_team_data_final(dock_file, "하역팀")

t = st.tabs(["📊 종합 현황", "🚚 중량팀 상세", "⚓ 하역팀 상세"])

with t[0]:
    if heavy_file or dock_file:
        st.subheader("🗓️ 1. 금일 작업")
        st.dataframe(pd.concat([h_w, d_w], ignore_index=True), use_container_width=True)
        st.subheader("👥 2. 근태 현황")
        st.dataframe(pd.concat([h_a, d_a], ignore_index=True), use_container_width=True)
        st.subheader("📅 3. 예정 작업")
        st.dataframe(pd.concat([h_p, d_p], ignore_index=True), use_container_width=True)

with t[1]: st.write("중량팀 상세 결과", h_w, h_a, h_p)
with t[2]: st.write("하역팀 상세 결과", d_w, d_a, d_p)
