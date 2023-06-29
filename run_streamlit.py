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
    return io.read_data_summary_json("data_summaries/")


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

def display_metrics(metrics, df_metadata):
    metric_columns = st.columns(4)
    metric_columns[0].metric("Collections", len(metrics["collections"]), delta=f"/ {len(df_metadata['collections'])}")#, delta_color="off")
    metric_columns[1].metric("Datasets", len(metrics["datasets"]), delta=f"/ {len(df_metadata['datasets'])}")
    metric_columns[2].metric("Languages", len(metrics["languages"]), delta=f"/ {len(df_metadata['languages'])}")
    metric_columns[3].metric("Task Categories", len(metrics["task_categories"]), delta=f"/ {len(df_metadata['task_categories'])}")


def insert_metric_container(title, key, metrics):
    with st.container():
        st.caption(title)
        # stats = f"{len(metrics['collections'])} / {len(df_metadata['collections'])}"
        # st.caption(stats)
        fig = util.plot_altair_barchart(metrics[key])
        # fig = util.plot_altair_piechart(metrics[key], title)
        st.altair_chart(fig, use_container_width=True, theme="streamlit")

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

                with st.expander("More advanced criteria"):

                    format_multiselect = st.multiselect(
                        'Select the format types to cover in your datasets',
                        ["All"] + list(constants.FORMAT_GROUPS.keys()),
                        ["All"])

                    domain_multiselect = st.multiselect(
                        'Select the domain types to cover in your datasets',
                        ["All"] + list(constants.DOMAIN_GROUPS.keys()),
                        ["All"])

                    time_range_selection = st.slider(
                        "Select data release time constraints",
                        value=(datetime(2000, 1, 1), datetime(2023, 7, 1)))

                # Every form must have a submit button.
                submitted = st.form_submit_button("Submit Selection")

        if submitted:
            filtered_df = util.apply_filters(
                INFO["data"], 
                license_multiselect, 
                language_multiselect, 
                taskcats_multiselect,
                format_multiselect,
                ["All"], #domain_multiselect,
                time_range_selection,
            )
            metrics = util.compute_metrics(filtered_df)

            st.subheader('Properties of your collection')
            # st.text("See what data fits your criteria.")

            st.markdown('#')
            st.markdown('#')
            
            display_metrics(metrics, df_metadata)

            # st.divider()
            st.markdown('#')
            # st.markdown('#')

            insert_metric_container("License Distribution", "licenses", metrics)
            insert_metric_container("Language Distribution", "languages", metrics)
            insert_metric_container("Task Category Distribution", "task_categories", metrics)

            with st.container(): 
                st.header('Collections Data')
                table = util.prep_collection_table(filtered_df, INFO["data"], metrics)
                setup_table(table)

    with tab2:
        st.header("Collection Explorer")

        with st.form("data_explorer"):
            collection_select = st.selectbox(
                'Select the collection to inspect',
                ["All"] + list(set(INFO["data"]["Collection"])))

            if collection_select == ["All"]:
                dataset_select = st.selectbox(
                    'Select the dataset in this collection to inspect',
                    ["All"] + list(set(INFO["data"]["Unique Dataset Identifier"])))
            else:
                collection_subset = INFO["data"][INFO["data"]["Collection"] == collection_select]
                dataset_select = st.selectbox(
                    'Select the dataset in this collection to inspect',
                    ["All"] + list(set(collection_subset["Unique Dataset Identifier"])))

            submitted2 = st.form_submit_button("Submit Selection")

        if submitted2:
        
            if dataset_select == "All":
                tab2_selected_df = INFO["data"][INFO["data"]["Collection"] == collection_select]
            else:
                tab2_selected_df = INFO["data"][INFO["data"]["Unique Dataset Identifier"] == dataset_select]

            tab2_metrics = util.compute_metrics(tab2_selected_df)
            display_metrics(tab2_metrics, df_metadata)

            with st.container():
                collection_info_keys = [
                    "Collection Name",
                    "Collection URL",
                    "Collection Hugging Face URL",
                    "Collection Paper Title",
                    "Collection Creators",
                ]
                dataset_info_keys = [
                    "Unique Dataset Identifier",
                    "Paper Title",
                    "Dataset URL",
                    "Hugging Face URL",
                ]
                data_characteristics_info_keys = [
                    "Format", "Languages", "Task Categories", "Text Topics", 
                    "Text Domains", "Number of Examples", "Text Length Metrics",
                ]
                data_provenance_info_keys = ["Creators", "Text Sources", "Licenses"]

                def extract_infos(df, key):
                    entries = df[key].tolist()
                    if not entries:
                        return []
                    elif key == "Licenses":
                            return set([x["License"] for xs in entries for x in xs if x and x["License"]])
                    elif isinstance(entries[0], list):
                        return set([x for xs in entries if xs for x in xs if x])
                    else:
                        return set([x for x in entries if x])

                # st.caption("Collection Information")
                # for info_key in collection_info_keys:
                #     st.text(f"{item}: {extract_infos(tab2_selected_df, info_key)}")

                if dataset_select != "All":
                    st.caption("Dataset Information")
                    for info_key in dataset_info_keys:
                        st.text(f"{info_key}: {extract_infos(tab2_selected_df, info_key)}")

                st.caption("Data Characteristics")
                for info_key in data_characteristics_info_keys:
                    st.text(f"{info_key}: {extract_infos(tab2_selected_df, info_key)}")

                st.caption("Data Provenance")
                for info_key in data_provenance_info_keys:
                    st.text(f"{info_key}: {extract_infos(tab2_selected_df, info_key)}")

        

            



if __name__ == "__main__":
    streamlit_app()
