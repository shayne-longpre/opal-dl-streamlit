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

from src import util
from src import filter_util
from src.helpers import io
from src import constants
from src import html_util

import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode
import streamlit.components.v1 as components
import requests

INFO = {}


@st.cache_data
def load_constants():
    return io.read_all_constants()

@st.cache_data
def load_data():
    data_summary = io.read_data_summary_json("data_summaries/")
    data_summary = filter_util.map_license_criteria(data_summary, INFO["constants"])
    return pd.DataFrame(data_summary).fillna("")


# def render_tweet(tweet_url):
#     api = "https://publish.twitter.com/oembed?url={}".format(tweet_url)
#     response = requests.get(api)
#     html_result = response.json()["html"] 
#     st.text(html_result)
#     components.html(html_result, height= 360, scrolling=True)

def insert_main_viz():

    # p5.js embed
    sketch = '<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.6.0/p5.js"></script>'
    sketch += '<script src="https://cdnjs.cloudflare.com/ajax/libs/p5.js/1.6.0/addons/p5.sound.min.js"></script>'
    sketch += '<script>'
    sketch += "const JSONDATA = " + open("static/ds_viz1.json", 'r', encoding='utf-8').read() + "\n"
    sketch += open("static/sketch.js", 'r', encoding='utf-8').read()
    sketch += '</script>'
    components.html(sketch, height=800, scrolling=True)




def display_metrics(metrics, df_metadata):
    metric_columns = st.columns(4)
    metric_columns[0].metric("Collections", len(metrics["collections"]), delta=f"/ {len(df_metadata['collections'])}")#, delta_color="off")
    metric_columns[1].metric("Datasets", len(metrics["datasets"]), delta=f"/ {len(df_metadata['datasets'])}")
    metric_columns[2].metric("Languages", len(metrics["languages"]), delta=f"/ {len(df_metadata['languages'])}")
    metric_columns[3].metric("Task Categories", len(metrics["task_categories"]), delta=f"/ {len(df_metadata['task_categories'])}")


def insert_metric_container(title, key, metrics):
    with st.container():
        st.caption(title)
        fig = util.plot_altair_barchart(metrics[key])
        # fig = util.plot_altair_piechart(metrics[key], title)
        st.altair_chart(fig, use_container_width=True, theme="streamlit")


def streamlit_app():
    st.set_page_config(page_title="Data Provenance Explorer", layout="wide")#, initial_sidebar_state='collapsed')
    INFO["constants"] = load_constants()
    INFO["data"] = load_data()

    df_metadata = util.compute_metrics(INFO["data"])

    with st.sidebar:
        st.markdown("""Select the preferred criteria for your datasets.""")

        with st.form("data_selection"):

            # st.write("Select the acceptable license values for constituent datasets")
            license_multiselect = st.select_slider(
                'Select the datasets licensed for these use cases',
                options=constants.LICENSE_USE_CLASSES,
                value="Commercial")

            license_attribution = st.toggle('Exclude Datasets w/ Attribution Requirements', value=False)
            license_sharealike = st.toggle('Exclude Datasets w/ Share Alike Requirements', value=False)

            # with data_select_cols[1]:
            language_multiselect = st.multiselect(
                'Select the languages to cover in your datasets',
                ["All"] + list(INFO["constants"]["LANGUAGE_GROUPS"].keys()),
                ["All"])

            # with data_select_cols[2]:
            taskcats_multiselect = st.multiselect(
                'Select the task categories to cover in your datasets',
                ["All"] + list(INFO["constants"]["TASK_GROUPS"].keys()),
                ["All"])

            with st.expander("More advanced criteria"):

                format_multiselect = st.multiselect(
                    'Select the format types to cover in your datasets',
                    ["All"] + INFO["constants"]["FORMATS"],
                    ["All"])

                domain_multiselect = st.multiselect(
                    'Select the domain types to cover in your datasets',
                    ["All", "Books", "Code", "Wiki", "News", "Biomedical", "Legal", "Web", "Math+Science"],
                    ["All"])

                time_range_selection = st.slider(
                    "Select data release time constraints",
                    value=(datetime(2000, 1, 1), datetime(2023, 7, 1)))

            # Every form must have a submit button.
            submitted = st.form_submit_button("Submit Selection")

    # st.write(len(INFO["data"]))
    if submitted:
        filtered_df = filter_util.apply_filters(
            INFO["data"], 
            INFO["constants"],
            "All", 
            license_multiselect,
            str(1 - int(license_attribution)),
            str(1 - int(license_sharealike)),
            language_multiselect, 
            taskcats_multiselect,
            # format_multiselect,
            # ["All"], #domain_multiselect,
            # time_range_selection,
        )
        filtered_data_summary = {row["Unique Dataset Identifier"]: row for row in filtered_df.to_dict(orient='records')}


    st.title("Data Provenance Explorer")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Data Summary", ":rainbow[Global Representation] :globe2:", "Licenses :vertical_traffic_light:", "Text Characteristics 📈"])

    with tab1:
        

        # insert_main_viz()

        if submitted:
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

            html_util.compose_html_component(
                filtered_data_summary, "text-metrics-licenses.js", {})

            html_util.compose_html_component(
                filtered_data_summary,
                "tasks-sunburst.js", {
                    "TASK_GROUPS": "html/constants/task_groups.json",
                })
            html_util.compose_html_component(
                filtered_data_summary,
                "creator-sunburst.js", {
                    "CREATOR_GROUPS": "html/constants/creator_groups.json",
                })

            with st.container(): 
                st.header('Collections Data')
                table = util.prep_collection_table(filtered_df, INFO["data"], metrics)
                html_util.setup_table(table)

    with tab2:
        st.header("Collection Explorer")
        st.write("Hello World")

        if submitted:
            html_util.compose_html_component(
                filtered_data_summary,
                "language-map.js", {
                    "world": "html/countries-50m.json",
                    "countryCodes": "html/country-codes.json",
                    "langCodes": "html/language-codes.json",
                    "countryCodeToLangCodes": "html/country-code-to-language-codes.json",
                })

            html_util.compose_html_component(
                filtered_data_summary,
                "creator-map.js", {
                    "world": "html/countries-50m.json",
                    "countryToCreator": "html/constants/creator_groups_by_country.json",
                })

    with tab3:
        st.header("Test")

    with tab4:
        st.header("Test")
                

    #     with st.form("data_explorer"):
    #         collection_select = st.selectbox(
    #             'Select the collection to inspect',
    #             ["All"] + list(set(INFO["data"]["Collection"])))

    #         if collection_select == ["All"]:
    #             dataset_select = st.selectbox(
    #                 'Select the dataset in this collection to inspect',
    #                 ["All"] + list(set(INFO["data"]["Unique Dataset Identifier"])))
    #         else:
    #             collection_subset = INFO["data"][INFO["data"]["Collection"] == collection_select]
    #             dataset_select = st.selectbox(
    #                 'Select the dataset in this collection to inspect',
    #                 ["All"] + list(set(collection_subset["Unique Dataset Identifier"])))

    #         submitted2 = st.form_submit_button("Submit Selection")

    #     if submitted2:
        
    #         if dataset_select == "All":
    #             tab2_selected_df = INFO["data"][INFO["data"]["Collection"] == collection_select]
    #         else:
    #             tab2_selected_df = INFO["data"][INFO["data"]["Unique Dataset Identifier"] == dataset_select]

    #         tab2_metrics = util.compute_metrics(tab2_selected_df)
    #         display_metrics(tab2_metrics, df_metadata)

    #         with st.container():
    #             collection_info_keys = [
    #                 "Collection Name",
    #                 "Collection URL",
    #                 "Collection Hugging Face URL",
    #                 "Collection Paper Title",
    #                 "Collection Creators",
    #             ]
    #             dataset_info_keys = [
    #                 "Unique Dataset Identifier",
    #                 "Paper Title",
    #                 "Dataset URL",
    #                 "Hugging Face URL",
    #             ]
    #             data_characteristics_info_keys = [
    #                 "Format", "Languages", "Task Categories", "Text Topics", 
    #                 "Text Domains", "Number of Examples", "Text Length Metrics",
    #             ]
    #             data_provenance_info_keys = ["Creators", "Text Sources", "Licenses"]

    #             def extract_infos(df, key):
    #                 entries = df[key].tolist()
    #                 if not entries:
    #                     return []
    #                 elif key == "Licenses":
    #                         return set([x["License"] for xs in entries for x in xs if x and x["License"]])
    #                 elif isinstance(entries[0], list):
    #                     return set([x for xs in entries if xs for x in xs if x])
    #                 else:
    #                     return set([x for x in entries if x])

    #             # st.caption("Collection Information")
    #             # for info_key in collection_info_keys:
    #             #     st.text(f"{item}: {extract_infos(tab2_selected_df, info_key)}")

    #             def format_markdown_entry(df, info_key):
    #                 dset_info = extract_infos(df, info_key)
    #                 if dset_info:
    #                     markdown_txt = dset_info
    #                     if isinstance(dset_info, list) or isinstance(dset_info, set):
    #                         markdown_txt = "\n* " + '\n* '.join(dset_info)
    #                     st.markdown(f"{info_key}: {markdown_txt}")

    #             if dataset_select != "All":
    #                 st.caption("Dataset Information")
    #                 for info_key in dataset_info_keys:
    #                     format_markdown_entry(tab2_selected_df, info_key)

    #             st.caption("Data Characteristics")
    #             for info_key in data_characteristics_info_keys:
    #                 format_markdown_entry(tab2_selected_df, info_key)

    #             st.caption("Data Provenance")
    #             for info_key in data_provenance_info_keys:
    #                 format_markdown_entry(tab2_selected_df, info_key)

        

            



if __name__ == "__main__":
    streamlit_app()
