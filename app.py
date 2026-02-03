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

# 3. 데이터 추출 엔진
def extract_data(file, team_name):
    if file is None: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    try:
        df = pd.read_excel(file, header=None)
        
        # 키워드 위치 찾기 (A열 기준)
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

        # --- 1. 금일 작업 ---
        if idx_w is not None:
            raw_w = df.iloc[idx_w+2:get_end(idx_w), :]
            if "중량" in team_name:
                w_df = pd.DataFrame({'팀명': team_name, '구분/화주': raw_w.iloc[:, 0], '작업내용': raw_w.iloc[:, 1], '비고': raw_w.iloc[:, 2]})
            else:
                w_df = pd.DataFrame({'팀명': team_name, '구분/화주': raw_w.iloc[:, 6].fillna(raw_w.iloc[:, 0]), '작업내용': raw_w.iloc[:, 7], '비고': raw_w.iloc[:, 9]})
        else: w_df = pd.DataFrame()

        # --- 2. 예정 작업 ---
        if idx_p is not None:
            raw_p = df.iloc[idx_p+2:get_end(idx_p), :]
            if "중량" in team_name:
                p_df = pd.DataFrame({'팀명': team_name, '구분/화주': raw_p.iloc[:, 0], '예정내용': raw_p.iloc[:, 1], '일정': raw_p.iloc[:, 2]})
            else:
                p_df = pd.DataFrame({'팀명': team_name, '구분/화주': raw_p.iloc[:, 6].fillna(raw_p.iloc[:, 0]), '예정내용': raw_p.iloc[:, 7], '일정': raw_p.iloc[:, 1], '비고': raw_p.iloc[:, 9]})
        else: p_df = pd.DataFrame()

        # --- 3. 근태 현황 (구분 - 팀명 - 인원 현황) ---
        if idx_a is not None:
            # 하역팀 양식에 맞춰 인덱스 유연하게 조정
            raw_a = df.iloc[idx_a+2:get_end(idx_a), [0, 1]].dropna(subset=[0])
            a_df = pd.DataFrame({
                '구분': raw_a.iloc[:, 0].astype(str).str.strip(),
                '팀명': team_name,
                '인원 현황': raw_a.iloc[:, 1].astype(str).str.strip()
            })
            # 명칭 표준화
            a_df['구분'] = a_df['구분'].replace({'본선 작업': '작업', '육상 작업': '작업', '연차': '휴가'})
        else: a_df = pd.DataFrame()

        # 최종 정제
        def clean(d, col):
            if d.empty: return d
            stops = ["화주", "본선", "구분", "내용", "입항", "인원", "nan", "None"]
            mask = d[col].astype(str).apply(lambda x: not any(s in x for s in stops) and x != "")
            return d[mask].reset_index(drop=True)

        return clean(w_df, '구분/화주'), a_df, clean(p_df, '구분/화주')

    except Exception:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# 데이터 처리
h_w, h_a, h_p = extract_data(heavy_file, "경남중량팀")
d_w, d_a, d_p = extract_data(dock_file, "경남하역팀")

tabs = st.tabs(["📊 종합 현황", "🚚 중량팀 상세", "⚓ 하역팀 상세"])

with tabs[0]:
    if heavy_file or dock_file:
        st.subheader("🗓️ 1. 전사 금일 작업")
        st.dataframe(pd.concat([h_w, d_w], ignore_index=True), use_container_width=True)
        
        st.divider()
        st.subheader("👥 2. 전사 근태 현황")
        total_att = pd.concat([h_a, d_a], ignore_index=True)
        if not total_att.empty:
            # 정렬 순서 정의
            order = {'작업': 0, '내무': 1, '출장': 2, '휴가': 3}
            total_att['priority'] = total_att['구분'].map(order).fillna(4)
            total_att = total_att.sort_values(['priority', '팀명']).drop('priority', axis=1)
            
            # ✨ 시각적 병합 (중복 텍스트 제거)
            display_att = total_att.copy()
            display_att.loc[display_att['구분'].duplicated(), '구분'] = ""
            
            # 에러 방지를 위해 st.table 대신 st.dataframe 사용 (가독성 위해 index 제거)
            st.dataframe(display_att, use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("📅 3. 전사 예정 작업")
        st.dataframe(pd.concat([h_p, d_p], ignore_index=True), use_container_width=True)
