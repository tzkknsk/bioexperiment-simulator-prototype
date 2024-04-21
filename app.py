import time
from io import BytesIO

import pandas as pd
import streamlit as st

from experiment import (
    generate_experimental_result,
    CONTROL_COLUMN,
)

def to_excel(df1, df2):
    """複数のデータフレームを受け取り、Excelファイルに変換する"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df1.to_excel(writer, sheet_name="design", index=False)
        df2.to_excel(writer, sheet_name="result", index=False)
    output.seek(0)
    return output


tabnames = ["design", "result"]

# Set page config
st.set_page_config(layout="wide")

# Session State
save_state_variables = [
    "design",
    "result"
]
for var in save_state_variables:
    if var not in st.session_state:
        st.session_state[var] = None

ss = st.session_state

# Data Upload
st.markdown("## 生命科学実験シミュレータ(プロトタイプ)")

# st.container(border=True) でなぜか `unexpected keyword argument` となる
with st.container(border=True):

    # Upload data file for analysis
    uploaded_file = st.file_uploader(
        "Upload data file for analysis",
        type="xlsx"
    )
    if uploaded_file is not None:

        tab1, tab2 = st.tabs(tabnames)

        _design = pd.read_excel(uploaded_file, sheet_name="design")
        _design[CONTROL_COLUMN] = _design[CONTROL_COLUMN].apply(
            lambda x: True if x == 1 else None
        )
        ss.design = _design

        _result = pd.read_excel(uploaded_file, sheet_name="result")
        _result[CONTROL_COLUMN] = _result[CONTROL_COLUMN].apply(
            lambda x: True if x == 1 else None
        )
        ss.result = _result

        with tab1:
            ss.design = st.data_editor(ss.design, num_rows="dynamic")

        with tab2:
            st.dataframe(ss.result)

with st.container(border=True):

    button_start_experiment = st.button("実験開始")

    if button_start_experiment:

        if ss.design is None:
            st.warning("データがアップロードされていません。")
            st.stop()

        new_design, new_result = generate_experimental_result(
            df_design=ss.design,
            df_result=ss.result
        )

        expeimeriment_image_folder = st.empty()

        progress_text = "実験中です。少々お待ちください。"
        my_bar = st.progress(0, text=progress_text)

        split_value = 5
        progress_value = int(100 / split_value)

        for i in range(1, split_value + 1):

            if i == split_value:
                progress_text = ""
            else:
                progress_text = "実験中です。少々お待ちください。"

            my_bar.progress(i * progress_value, text=progress_text)
            expeimeriment_image_folder.image(
                f"./images/{i}.png",
                use_column_width=True,
            )

            time.sleep(1)

        st.success("実験が完了しました。実験結果が記載されたファイルをダウンロードしてください。")

        tab1_new, tab2_new = st.tabs(tabnames)

        with tab1_new:
            st.dataframe(new_design)

        with tab2_new:
            st.dataframe(new_result)

        # Excelファイルを生成
        excel_file = to_excel(new_design, new_result)

        # ダウンロードボタン
        st.download_button(
            label="実験結果をダウンロード",
            data=excel_file,
            file_name="optimization_problem_setting_sheet.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
