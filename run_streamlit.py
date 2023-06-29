#!/usr/bin/env python3

"""
To run:

streamlit run ./run_streamlit.py
"""

from datetime import datetime
import json
import numpy as np
import pandas as pd
import math

import util
from src.helpers import io
from src import constants

import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode
import streamlit.components.v1 as components
import requests

INFO = {}




@st.cache_data
def load_data():
    data = io.read_data_summary_json("data_summaries/")
    # data["all"] = ...
    return data


# def render_tweet(tweet_url):
#     api = "https://publish.twitter.com/oembed?url={}".format(tweet_url)
#     response = requests.get(api)
#     html_result = response.json()["html"] 
#     components.html(html_result, height= 360, scrolling=True)


def setup_table(selected_data):

    # selected_data = data[_PRESENT_COLS]

    custom_css = {".ag-header-cell-text": {"font-size": "12px", 'text-overflow': 'revert;', 'font-weight': 700},
                ".ag-theme-streamlit": {'transform': "scale(0.8)", "transform-origin": '0 0'}}
    gb = GridOptionsBuilder.from_dataframe(selected_data, axis=1)
    gb.configure_default_column(cellStyle={'color': 'black', 'font-size': '12px'}, suppressMenu=True, wrapHeaderText=True, autoHeaderHeight=True)
    gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
    gb.configure_side_bar() #Add a sidebar
    # gb.configure_selection('single', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
    gridOptions = gb.build()

    # https://streamlit-aggrid.readthedocs.io/en/docs/AgGrid.html
    # Highlight Rows: https://discuss.streamlit.io/t/aggrid-is-there-a-way-to-color-a-row-based-on-a-column-value/20750/2
    grid_response = AgGrid(
        selected_data,
        gridOptions=gridOptions,
        custom_css=custom_css, allow_unsafe_jscode=True,
        data_return_mode='AS_INPUT', 
        # update_mode='MODEL_CHANGED', 
        update_mode='NO_UPDATE', 
        # update_mode='SELECTION_CHANGED',
        fit_columns_on_grid_load=False,
        theme='material', # streamlit, material
        height=2000, 
        width='100%',
        # reload_data=True
    )

    # resp_data = grid_response['data']
    # selected_rows = grid_response['selected_rows']

    # if selected_rows:

    #     row_index = selected_rows[0]["rowIndex"]
    #     selected_info = resp_data.iloc[row_index]



# @st.cache_data
# def run_query(date_range, ranking_fn_select, filter_fn_select, platform_select):
#     ranking_fn = _RANKING_FUNCTIONS[ranking_fn_select]
#     filter_fn = _FILTER_FUNCTIONS[filter_fn_select]
#     actor_lb_info, primary_lb_info, secondary_lb_info = INFO["data"].get(platform_select.lower())


#     NUM_INFLUENCERS = 50

#     leaderboard = util.generate_leaderboard(
#         lb_stats, rank_fn=ranking_fn, filter_fn=filter_fn
#     )
#     presentable_lb = util.present_leaderboard(
#         leaderboard, actor_lb_info, n=NUM_INFLUENCERS
#     )
#     return leaderboard, presentable_lb


def streamlit_app():
    st.set_page_config(page_title="Data Provenance Explorer", layout="wide")#, initial_sidebar_state='collapsed')
    INFO["data"] = load_data()
    df_metadata = util.compute_metrics(INFO["data"])

    tab1, tab2 = st.tabs(["Data Selection", "Project Details"])

    with tab1:
        st.title("Data Provenance Explorer")

        with st.sidebar:
            st.markdown("""Select the preferred criteria for your datasets.""")

            with st.form("data_selection"):

                # data_select_cols = st.columns(3)

                # with data_select_cols[0]:
                # st.write("Select the acceptable license values for constituent datasets")
                license_multiselect = st.multiselect(
                    'Select the acceptable license values for constituent datasets',
                    ["All"] + list(constants.LICENSE_GROUPS.keys()),
                    ["All"])

                # with data_select_cols[1]:
                language_multiselect = st.multiselect(
                    'Select the languages to cover in your datasets',
                    ["All"] + list(constants.LANGUAGE_GROUPS.keys()),
                    ["All"])

                # with data_select_cols[2]:
                taskcats_multiselect = st.multiselect(
                    'Select the task categories to cover in your datasets',
                    ["All"] + list(constants.TASK_CATEGORY_GROUPS.keys()),
                    ["All"])

                # Every form must have a submit button.
                submitted = st.form_submit_button("Submit Selection")

        if submitted:
            filtered_df = util.apply_filters(
                INFO["data"], license_multiselect, language_multiselect, taskcats_multiselect)
            metrics = util.compute_metrics(filtered_df)

            st.subheader('Properties of your collection')
            # st.text("See what data fits your criteria.")

            st.markdown('#')
            st.markdown('#')
            
            metric_columns1 = st.columns(4)
            metric_columns1[0].metric("Collections", len(metrics["collections"]), delta=f"/ {len(df_metadata['collections'])}")#, delta_color="off")
            metric_columns1[1].metric("Datasets", len(metrics["datasets"]), delta=f"/ {len(df_metadata['datasets'])}")
            # metric_columns2 = st.columns(2)
            metric_columns1[2].metric("Languages", len(metrics["languages"]), delta=f"/ {len(df_metadata['languages'])}")
            metric_columns1[3].metric("Task Categories", len(metrics["task_categories"]), delta=f"/ {len(df_metadata['task_categories'])}")

            # st.divider()
            st.markdown('#')
            # st.markdown('#')

            def insert_metric_container(title, key):
                with st.container():
                    st.caption(title)
                    # stats = f"{len(metrics['collections'])} / {len(df_metadata['collections'])}"
                    # st.caption(stats)
                    fig = util.plot_altair_piechart(metrics[key], title)
                    st.altair_chart(fig, use_container_width=False, theme="streamlit")
                    
            insert_metric_container("License Distribution", "licenses")
            insert_metric_container("Language Distribution", "languages")
            insert_metric_container("Task Category Distribution", "task_categories")

            # st.header('Properties for your collection')
            with st.container(): 
            #     piechart_columns = st.columns(3)
            #     # licensing dist
            #     # st.write("License Distribution")
            #     # fig0 = util.plot_piechart(metrics["licenses"], "License Distribution")
            #     # piechart_columns[0].pyplot(fig0)
            #     fig0 = util.plot_altair_piechart(metrics["licenses"], "License Distribution")
            #     piechart_columns[0].caption("License Distribution")
            #     piechart_columns[0].altair_chart(fig0, use_container_width=False, theme="streamlit")

            #     # language dist
            #     # st.write("Language Distribution")
            #     # fig1 = util.plot_piechart(metrics["languages"], "Language Distribution")
            #     # piechart_columns[1].pyplot(fig1)
            #     fig1 = util.plot_altair_piechart(metrics["languages"], "Language Distribution")
            #     piechart_columns[1].caption("Language Distribution")
            #     piechart_columns[1].altair_chart(fig1, use_container_width=False, theme="streamlit")

            #     # task category dist
            #     # st.write("Task Categories Distribution")
            #     # fig2 = util.plot_piechart(metrics["task_categories"], "Task Categories Distribution")
            #     # piechart_columns[2].pyplot(fig2)
            #     fig2 = util.plot_altair_piechart(metrics["task_categories"], "Task Category Distribution")
            #     piechart_columns[2].caption("Task Category Distribution")
            #     piechart_columns[2].altair_chart(fig2, use_container_width=False, theme="streamlit")

            #     st.markdown('#')
                st.header('Collections Data')
                table = util.prep_collection_table(filtered_df, INFO["data"], metrics)
                setup_table(table)

    with tab2:
        st.header("Project Details")

        st.markdown("""
            Intro
            main tab: set of options:
                license constraints
                language constraints
                task category constraints

            # 0. Metrics:
                num datasets, num languages, num tasks,
                pie chart of languages, pie chart of licenses, pie chart of collections + tasks

            # 1. render table of collections that are left after selection:
                name, num datasets, num languages, num tasks, % in use.
            # 2. render table of datasets.

        """)



if __name__ == "__main__":
    streamlit_app()
