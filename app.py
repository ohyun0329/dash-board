import streamlit as st
import pandas as pd

# ... (상단 설정 및 데이터 추출 로직은 동일) ...

with tabs[0]:
    if heavy_file or dock_file:
        # 1, 3번 섹션은 기존 dataframe 유지
        st.subheader("🗓️ 1. 전사 금일 작업")
        st.dataframe(pd.concat([h_w, d_w], ignore_index=True), use_container_width=True)
        
        st.divider()
        st.subheader("👥 2. 전사 근태 현황")
        total_att = pd.concat([h_a, d_a], ignore_index=True)
        
        if not total_att.empty:
            # 정렬 순서 적용
            sort_order = {'작업': 0, '내무': 1, '출장': 2, '휴가': 3}
            total_att['order'] = total_att['구분'].map(sort_order).fillna(4)
            total_att = total_att.sort_values(['order', '팀명']).drop('order', axis=1)

            # --- ✨ HTML을 이용한 완전 병합 테이블 생성 ---
            # 같은 구분별로 그룹화하여 행 개수를 계산합니다.
            summary = total_att.groupby('구분').agg({'팀명': list, '인원 현황': list}).reset_index()
            summary['priority'] = summary['구분'].map(sort_order).fillna(4)
            summary = summary.sort_values('priority')

            # HTML 표 시작 (세방 스타일 블루 테마 적용)
            html_code = """
            <style>
                .merged-table { width: 100%; border-collapse: collapse; font-family: sans-serif; }
                .merged-table th { background-color: #003366; color: white; padding: 10px; border: 1px solid #ddd; }
                .merged-table td { padding: 8px; border: 1px solid #ddd; text-align: center; }
                .category-cell { background-color: #f8f9fa; font-weight: bold; width: 15%; }
            </style>
            <table class="merged-table">
                <thead>
                    <tr>
                        <th>구분</th>
                        <th>팀명</th>
                        <th>인원 현황</th>
                    </tr>
                </thead>
                <tbody>
            """

            for _, row in summary.iterrows():
                row_span = len(row['팀명'])
                for i in range(row_span):
                    html_code += "<tr>"
                    # 첫 번째 행일 때만 '구분' 칸을 만들고 rowspan 적용
                    if i == 0:
                        html_code += f"<td class='category-cell' rowspan='{row_span}'>{row['구분']}</td>"
                    html_code += f"<td>{row['팀명'][i]}</td>"
                    html_code += f"<td>{row['인원 현황'][i]}</td>"
                    html_code += "</tr>"
            
            html_code += "</tbody></table>"
            
            # 마크다운을 통해 HTML 렌더링
            st.write(html_code, unsafe_allow_html=True)
        
        st.divider()
        st.subheader("📅 3. 전사 예정 작업")
        st.dataframe(pd.concat([h_p, d_p], ignore_index=True), use_container_width=True)
