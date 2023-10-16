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
    # st.write([r["Unique Dataset Identifier"] for r in data_summary if "License Attribution (DataProvenance)" not in r])
    # st.write(data_summary[0].keys())
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
    # st.write(INFO["constants"].keys())
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

                # format_multiselect = st.multiselect(
                #     'Select the format types to cover in your datasets',
                #     ["All"] + INFO["constants"]["FORMATS"],
                #     ["All"])

                domain_multiselect = st.multiselect(
                    'Select the domain types to cover in your datasets',
                    ["All"] + list(INFO["constants"]["DOMAIN_GROUPS"].keys()),
                    # ["All", "Books", "Code", "Wiki", "News", "Biomedical", "Legal", "Web", "Math+Science"],
                    ["All"])

                time_range_selection = st.slider(
                    "Select data release time constraints",
                    value=(datetime(2000, 1, 1), datetime(2023, 12, 1)))

            # Every form must have a submit button.
            submitted = st.form_submit_button("Submit Selection")


    # st.write(len(INFO["data"]))
    if submitted:
        start_time = time_range_selection[0].strftime('%Y-%m-%d')
        end_time = time_range_selection[1].strftime('%Y-%m-%d') 
        # We do this check to make sure we include No-Time datasets.
        if start_time == "2000-01-01":
            start_time = None
        if end_time == "2023-12-01": 
            end_time = None
        filtered_df = filter_util.apply_filters(
            INFO["data"], 
            INFO["constants"],
            None, 
            None, # Select all licenses.
            license_multiselect,
            str(1 - int(license_attribution)),
            str(1 - int(license_sharealike)),
            language_multiselect, 
            taskcats_multiselect,
            # format_multiselect,
            domain_multiselect,
            start_time,
            end_time,
        )
        def format_datetime(value):
            if isinstance(value, pd.Timestamp):
                return value.strftime('%Y-%m-%d')
            return value
        formatted_df = filtered_df.applymap(format_datetime)
        filtered_data_summary = {row["Unique Dataset Identifier"]: row for row in formatted_df.to_dict(orient='records')}


    st.title("Data Provenance Explorer")

    st.write("The Data Provenance Initiative gives researchers the opportunity to explore thousands of the most popular Datasets for training large language models.")
    st.write("NB: This data is compiled voluntarily by the best efforts of academic & independent researchers, and is :red[**NOT** to be taken as legal advice].")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Data Summary", 
        ":rainbow[Global Representation] :earth_africa:", 
        "Data Licenses :vertical_traffic_light:", 
        "Text Characteristics :test_tube:",
        "Inspect Individual Datasets :mag:"])

    with tab1:
        # insert_main_viz()

        if not submitted:
            st.write("When you're ready, fill out your data filtering criteria on the left, and click Submit!\n\n")

            st.subheader("Instructions")
            form_instructions = """
            1. **Select from the licensed data use cases**. The options range from least to most strict:
            `Commercial`, `Unspecified`, `Non-Commercial`, `Academic-Only`.
            
            * `Commercial` will select only the data with licenses explicitly permitting commercial use. 
            * `Unspecified` includes Commercial plus datasets with no license found attached, which may suggest the curator does not prohibit commercial use.
            * `Non-Commercial` includes Commercial and Unspecified datasets plus those licensed for non-commercial use.
            * `Academic-Only` will select all available datasets, including those that restrict to only academic uses.

            Note that these categories reflect the *self-reported* licenses attached to datasets, and assume fair use of any data they are derived from (e.g. scraped from the web).

            2. Select whether to exclude datasets with **Attribution requirements in their licenses**.

            3. Select whether to exclude datasets with **`Share-Alike` requirements in their licenses**. 
            Share-Alike means a copyright left license, that allows other to re-use, re-mix, and modify works, but requires that derivative work is distributed under the same terms and conditions.

            4. **Select Language Families** to include.

            5. **Select Task Categories** to include.

            6. More advanced selection criteria are also available in the drop down box.

            Finally, Submit Selection when ready!
            """
            st.write(form_instructions)
        elif submitted:
            metrics = util.compute_metrics(filtered_df)

            st.subheader('General Properties of your collection')
            # st.text("See what data fits your criteria.")

            st.markdown('#')
            st.markdown('#')
            
            display_metrics(metrics, df_metadata)

            # st.divider()
            st.markdown('#')
            # st.markdown('#')

            # insert_metric_container("Language Distribution", "languages", metrics)
            # insert_metric_container("Task Category Distribution", "task_categories", metrics)

            with st.container(): 
                st.header('Collections Data')
                table = util.prep_collection_table(filtered_df, INFO["data"], metrics)
                html_util.setup_table(table)

    with tab2:
        st.header(":rainbow[Global Representation] :earth_africa:")

        tab2_intro = """This section explores the representation of text datasets internationally.
        These datasets contain a wide distribution of languages, and are created by many organizations and insitutions.
        We measure both the representation across countries in which these languages are spoken, as well as "who creates these datasets"?
        """
        st.write(tab2_intro)

        if submitted:

            st.subheader("Language Representation by Country")
            # st.write("First we visualize the language representation across countries by measuring **how well a country's population is covered by languages in these datasets**.")
            st.write("""First we visualize the language coverage per country, according to the spoken languages and their representation in the Data Provenance Collection. 
            We compute a score $S_k$ for each country $k$, parametrized by $p_{kl}$, the percentage of people in country $k$ that speak language $l$, and $w_{li}$ which is a binary indicator that is 1 if dataset $i \in D$ contains language $l$ and 0 otherwise."""
            )

            st.latex(r'''
            S_k = \sum_{l \in L} \left( p_{kl} \times \sum_{i \in D} w_{li} \right)
            ''')

            html_util.compose_html_component(
                filtered_data_summary,
                "language-map.js", {
                    "world": "html/countries-50m.json",
                    "countryCodes": "html/country-codes.json",
                    "langCodes": "html/language-codes.json",
                    "countryCodeToLangCodes": "html/country-code-to-language-codes.json",
                })
            st.write("NB: While many global south countries have large English speaking populations, it may still not mean they are well represented by English text from Western/European origins.")
            

            st.subheader("Dataset Creator Representation by Country")
            st.write("Here we visualize the density of organizations that package/create these datasets for machine learning, in contrast to the above.")
            st.write("This may help answer 'who owns the data?'")
            html_util.compose_html_component(
                filtered_data_summary,
                "creator-map.js", {
                    "world": "html/countries-50m.json",
                    "countryToCreator": "html/constants/creator_groups_by_country.json",
                })

            st.subheader("Dataset Creator Proportions")
            st.write("Here we count the contributions of organizations to dataset creation.")
            html_util.compose_html_component(
                filtered_data_summary,
                "creator-sunburst.js", {
                    "CREATOR_GROUPS": "html/constants/creator_groups.json",
                }, 1200)

    with tab3:
        st.header("Data Licenses :vertical_traffic_light:")
        tab3_intro = """This section explores the *self-reported* data licenses by the creators of each dataset.
        Note a few important limitations:
        * The legal status of data licenses is not always clear and may be different by jurisdiction.
        * Despite our best efforts, omissions or mistakes are possible.
        * This transparency initative is **not** intended as legal advice, and bears no responsibility on how the *self-reported* licenses are used.
        """
        st.write(tab3_intro)

        if submitted:
            st.subheader("License Distribution")
            st.write("Here we see the license distribution of those collected by the Data Provenance Initiative.")
            insert_metric_container("License Distribution", "licenses", metrics)

    with tab4:
        st.header("Text Characteristics :test_tube:")
        st.write("This section covers various characteristics of the text in the datasets.")

        if submitted:
            st.subheader("Text Length Metrics x License Category")
            st.write("Text-to-text datasets are formatted as an input-target pair.")
            st.write("Here each point is a dataset, showing its input text length (in characters), target text length (in characters), and license category.")
            html_util.compose_html_component(
                filtered_data_summary, "text-metrics-licenses.js", {})

            st.subheader("Text Length Metrics x Regular/Synthetic Text")
            st.write("New text-to-text datasets are often synthetically generated by large models like GPT-4.")
            st.write("Here each point is a dataset, showing its input text length (in characters), target text length (in characters), and whether it is synthetically generated, or manually/human created.")
            html_util.compose_html_component(
                filtered_data_summary, "text-metrics-synthetic.js", {})

            st.subheader("Task Category Distribution")
            st.write("Here we measure the variety and distribution of tasks that the datasets represent -- i.e. what they're teaching a model to do.")
            html_util.compose_html_component(
                filtered_data_summary,
                "tasks-sunburst.js", {
                    "TASK_GROUPS": "html/constants/task_groups.json",
                },1200)
                

    with tab5:
        st.header("Inspect Individual Datasets :mag:")

        with st.form("data_explorer"):
            # collection_select = st.selectbox(
            #     'Select the collection to inspect',
            #     ["All"] + list(set(INFO["data"]["Collection"])))

            # if collection_select == ["All"]:
            dataset_select = st.selectbox(
                'Select the dataset in this collection to inspect',
                list(set(INFO["data"]["Unique Dataset Identifier"])))
                # ["All"] + list(set(INFO["data"]["Unique Dataset Identifier"])))
            # else:
            #     collection_subset = INFO["data"][INFO["data"]["Collection"] == collection_select]
            #     dataset_select = st.selectbox(
            #         'Select the dataset in this collection to inspect',
            #         ["All"] + list(set(collection_subset["Unique Dataset Identifier"])))

            submitted2 = st.form_submit_button("Submit Selection")

        if submitted2:
        
            # if dataset_select == "All":
            #     tab2_selected_df = INFO["data"][INFO["data"]["Collection"] == collection_select]
            # else:
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
                    "Format", "Languages", "Task Categories", 
                    # "Text Topics", 
                    # "Text Domains", "Number of Examples", "Text Length Metrics",
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

                def format_markdown_entry(df, info_key):
                    dset_info = extract_infos(df, info_key)
                    if dset_info:
                        markdown_txt = dset_info
                        if isinstance(dset_info, list) or isinstance(dset_info, set):
                            markdown_txt = "\n* " + '\n* '.join(dset_info)
                        st.markdown(f"{info_key}: {markdown_txt}")

                if dataset_select != "All":
                    st.caption("Dataset Information")
                    for info_key in dataset_info_keys:
                        format_markdown_entry(tab2_selected_df, info_key)

                st.caption("Data Characteristics")
                for info_key in data_characteristics_info_keys:
                    format_markdown_entry(tab2_selected_df, info_key)

                st.caption("Data Provenance")
                for info_key in data_provenance_info_keys:
                    format_markdown_entry(tab2_selected_df, info_key)

        

            



if __name__ == "__main__":
    streamlit_app()
