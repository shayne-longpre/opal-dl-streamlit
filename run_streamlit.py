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
import webbrowser

from PIL import Image


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

def custom_metric(caption, score, delta=None):
    st.markdown("## :green[" + str(score) + "]")
    # st.subheader("     :green[" + str(score) + "]")
    if delta:
        st.markdown("     " + str(delta))
    st.markdown(f":gray[{caption}]")
    # st.caption(caption)

    # :red[**NOT** to be taken as legal advice]


def display_metrics(metrics, df_metadata):
    # metric_columns = st.columns(4)
    # metric_columns[0].metric("Collections", len(metrics["collections"]), delta=f"/ {len(df_metadata['collections'])}")#, delta_color="off")
    # metric_columns[1].metric("Datasets", len(metrics["datasets"]), delta=f"/ {len(df_metadata['datasets'])}")
    # metric_columns[2].metric("Languages", len(metrics["languages"]), delta=f"/ {len(df_metadata['languages'])}")
    # metric_columns[3].metric("Task Categories", len(metrics["task_categories"]), delta=f"/ {len(df_metadata['task_categories'])}")
    metric_columns = st.columns(3)
    # with metric_columns[0]:
    #     st.metric("Collections", len(metrics["collections"]), delta=f"/ {len(df_metadata['collections'])}")#, delta_color="off")
    #     st.metric("Datasets", len(metrics["datasets"]), delta=f"/ {len(df_metadata['datasets'])}")
    #     st.metric("Dialogs", metrics["dialogs"], delta=f"/ {df_metadata['dialogs']}")
    # with metric_columns[1]:
    #     st.metric("Languages", len(metrics["languages"]), delta=f"/ {len(df_metadata['languages'])}")
    #     st.metric("Task Categories", len(metrics["task_categories"]), delta=f"/ {len(df_metadata['task_categories'])}")
    #     st.metric("Topics", len(metrics["topics"]), delta=f"/ {len(df_metadata['topics'])}")
    # with metric_columns[2]:
    #     st.metric("Text Domains", len(metrics["domains"]), delta=f"/ {len(df_metadata['domains'])}")
    #     st.metric("Text Sources", len(metrics["sources"]), delta=f"/ {len(df_metadata['sources'])}")
    #     st.metric("% Synthetic Text", metrics["synthetic_pct"])
    with metric_columns[0]:
        custom_metric("Collections", len(metrics["collections"]), delta=f"/ {len(df_metadata['collections'])}")#, delta_color="off")
        custom_metric("Datasets", len(metrics["datasets"]), delta=f"/ {len(df_metadata['datasets'])}")
        custom_metric("Dialogs", metrics["dialogs"], delta=f"/ {df_metadata['dialogs']}")
    with metric_columns[1]:
        custom_metric("Languages", len(metrics["languages"]), delta=f"/ {len(df_metadata['languages'])}")
        custom_metric("Task Categories", len(metrics["task_categories"]), delta=f"/ {len(df_metadata['task_categories'])}")
        custom_metric("Topics", len(metrics["topics"]), delta=f"/ {len(df_metadata['topics'])}")
    with metric_columns[2]:
        custom_metric("Text Domains", len(metrics["domains"]), delta=f"/ {len(df_metadata['domains'])}")
        custom_metric("Text Sources", len(metrics["sources"]), delta=f"/ {len(df_metadata['sources'])}")
        custom_metric("% Synthetic Text", metrics["synthetic_pct"])


def insert_metric_container(title, key, metrics):
    with st.container():
        st.caption(title)
        fig = util.plot_altair_barchart(metrics[key])
        # fig = util.plot_altair_piechart(metrics[key], title)
        st.altair_chart(fig, use_container_width=True, theme="streamlit")

def add_instructions():
    st.title("Data Provenance Explorer")

    col1, col2 = st.columns([0.75, 0.25], gap="medium")

    with col1:
        intro_sents = "The Data Provenance Initiative is a large-scale audit of AI datasets used to train large language models. As a first step, we've traced 1800+ popular, text-to-text finetuning datasets from origin to creation, cataloging their data sources, licenses, creators, and other metadata, for researchers to explore using this tool."
        follow_sents = "The purpose of this work is to improve transparency, documentation, and informed use of datasets in AI. "
        st.write(" ".join([intro_sents, follow_sents]))
        st.write("You can download this data (with filters) directly from the [Data Provenance Collection](https://github.com/Data-Provenance-Initiative/Data-Provenance-Collection).")
        st.write("If you wish to contribute or discuss, please feel free to contact the organizers at [data.provenance.init@gmail.com](mailto:data.provenance.init@gmail.com).")
        # st.write("NB: This data is compiled voluntarily by the best efforts of academic & independent researchers, and is :red[**NOT** to be taken as legal advice].")

        st.write("NB: It is important to note we collect *self-reported licenses*, from the papers and repositories that released these datasets, and categorize them according to our best efforts, as a volunteer research and transparency initiative. The information provided by any of our works and any outputs of the Data Provenance Initiative :red[do **NOT**, and are **NOT** intended to, constitute legal advice]; instead, all information, content, and materials are for general informational purposes only.")

        col1a, col1b, col1c = st.columns([0.16, 0.16, 0.68], gap="small")
        with col1a:
            st.link_button("Data Repository", 'https://github.com/Data-Provenance-Initiative/Data-Provenance-Collection', type="primary")
        with col1b:
            st.link_button("Paper", 'https://www.dataprovenance.org/paper.pdf', type="primary")

        # col1a, col1b = st.columns(2, gap="large")
        # with col1a:
            # st.link_button("Paper", 'https://www.dataprovenance.org/paper.pdf', type="primary")
        # with col1b:
            # st.link_button("Data Repository", 'https://github.com/Data-Provenance-Initiative/Data-Provenance-Collection', type="primary")
        # st.link_button('Paper', 'https://www.dataprovenance.org/paper.pdf', type="primary")
        # st.link_button('Download Repository', 'https://github.com/Data-Provenance-Initiative/Data-Provenance-Collection', type="primary")
        # if st.button('Paper', type="primary"):
        #     webbrowser.open_new_tab('https://www.dataprovenance.org/paper.pdf')
        # if st.button('Download Repository', type="primary"):
        #     webbrowser.open_new_tab('https://github.com/Data-Provenance-Initiative/Data-Provenance-Collection')

        # URL_STRING = "https://streamlit.io/"

        # st.markdown(
        #     f'<a href="{URL_STRING}" style="display: inline-block; padding: 12px 20px; background-color: #4CAF50; color: white; text-align: center; text-decoration: none; font-size: 16px; border-radius: 4px;">Action Text on Button</a>',
        #     unsafe_allow_html=True
        # )
    with col2:
        image = Image.open('dpi.png')
        st.image(image)#, caption='Sunrise by the mountains')

    st.subheader("Instructions")
    form_instructions = """
    1. **Select from the licensed data use cases**. The options range from least to most strict:
    `Commercial`, `Unspecified`, `Non-Commercial`, `Academic-Only`.
    
    * `Commercial` will select only the data with licenses explicitly permitting commercial use. 
    * `Unspecified` includes Commercial plus datasets with no license found attached, which may suggest the curator does not prohibit commercial use.
    * `Non-Commercial` includes Commercial and Unspecified datasets plus those licensed for non-commercial use.
    * `Academic-Only` will select all available datasets, including those that restrict to only academic uses.

    Note that these categories reflect the *self-reported* licenses attached to datasets, and assume fair use of any data they are derived from (e.g. scraped from the web).

    2. Select whether to include datasets with **Attribution requirements in their licenses**.

    3. Select whether to include datasets with **`Share-Alike` requirements in their licenses**. 
    Share-Alike means a copyright left license, that allows other to re-use, re-mix, and modify works, but requires that derivative work is distributed under the same terms and conditions.

    4. Select whether to ignore the [OpenAI Terms of Use](https://openai.com/policies/terms-of-use) as a Non-Commercial restriction, and include datasets that are at least partially **generated by OpenAI** (inputs, outputs, or both).
    While the OpenAI terms state you cannot ``use output from the Services to develop models that compete with OpenAI'', there is debate as to their enforceability and applicability to third parties who did not generate this data themselves. See our Legal Discussion section in the paper for more discussion on these terms.
    
    5. **Select Language Families** to include.

    6. **Select Task Categories** to include.

    7. **Select Time of Collection**. By default it includes all datasets.

    8. **Select the Text Domains** to include.

    Finally, Submit Selection when ready!
    """
    with st.expander("Expand for Instructions!"):
        st.write(form_instructions)

def streamlit_app():
    st.set_page_config(page_title="Data Provenance Explorer", layout="wide")#, initial_sidebar_state='collapsed')
    INFO["constants"] = load_constants()
    # st.write(INFO["constants"].keys())
    INFO["data"] = load_data()

    df_metadata = util.compute_metrics(INFO["data"], INFO["constants"])

    add_instructions()

    #### ALTERNATIVE STARTS HERE
    st.markdown("""Select the preferred criteria for your datasets.""")

    with st.form("data_selection"):

        col1, col2, col3 = st.columns([1,1,1], gap="medium")

        with col1:
            # st.write("Select the acceptable license values for constituent datasets")
            license_multiselect = st.select_slider(
                'Select the datasets licensed for these use cases',
                options=constants.LICENSE_USE_CLASSES,
                value="Academic-Only")

            license_attribution = st.toggle('Include Datasets w/ Attribution Requirements', value=True)
            license_sharealike = st.toggle('Include Datasets w/ Share Alike Requirements', value=True)
            openai_license_override = st.toggle('Always include datasets w/ OpenAI-generated data. (I.e. See `instructions` above for details.)', value=False)

        with col3:
            
            taskcats_multiselect = st.multiselect(
                'Select the task categories to cover in your datasets',
                ["All"] + list(INFO["constants"]["TASK_GROUPS"].keys()),
                ["All"])

        # with st.expander("More advanced criteria"):

            # format_multiselect = st.multiselect(
            #     'Select the format types to cover in your datasets',
            #     ["All"] + INFO["constants"]["FORMATS"],
            #     ["All"])

            domain_multiselect = st.multiselect(
                'Select the domain types to cover in your datasets',
                ["All"] + list(INFO["constants"]["DOMAIN_GROUPS"].keys()),
                # ["All", "Books", "Code", "Wiki", "News", "Biomedical", "Legal", "Web", "Math+Science"],
                ["All"])


        with col2:
            language_multiselect = st.multiselect(
                'Select the languages to cover in your datasets',
                ["All"] + list(INFO["constants"]["LANGUAGE_GROUPS"].keys()),
                ["All"])

            time_range_selection = st.slider(
                "Select data release time constraints",
                value=(datetime(2000, 1, 1), datetime(2023, 12, 1)))

            # st.write("")
        # st.write("")
        st.divider()

        # Every form must have a submit button.
        submitted = st.form_submit_button("Submit Selection")




    #### ALTERNATIVE ENDS HERE

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
            openai_license_override,
            str(int(license_attribution)),
            str(int(license_sharealike)),
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

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Data Summary",
        ":rainbow[Global Representation] :earth_africa:", 
        "Text Characteristics :test_tube:",
        "Data Licenses :vertical_traffic_light:", 
        "Inspect Individual Datasets :mag:"])

    with tab1:
        # insert_main_viz()

        if not submitted:
            st.write("When you're ready, fill out your data filtering criteria on the left, and click Submit!\n\n")

        elif submitted:
            metrics = util.compute_metrics(filtered_df, INFO["constants"])

            st.subheader('General Properties of your collection')
            st.write("Given your selection, see the quantity of data (collections, datasets, dialogs), the characteristics of the data (languages, tasks, topics), and the sources of data covered (sources, domains, \% synthetically generated by models).")

            st.markdown('#')
            # st.markdown('#')
            
            display_metrics(metrics, df_metadata)

            # st.divider()
            # st.markdown('#')
            # st.markdown('#')

            # insert_metric_container("Language Distribution", "languages", metrics)
            # insert_metric_container("Task Category Distribution", "task_categories", metrics)

            with st.container(): 
                st.header('Summary of Data Collections')
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
                }, 1600)

    with tab3:
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

            # tree    
            st.subheader("Text Source Domains")
            st.write("Many datasets are originally scraped from the web or other sources. For the data you've selected, we cluster the original sources by Domain, quantify them and show the top sources 5 per domain.")
            html_util.compose_html_component(
                filtered_data_summary,
                "source-tree.js", {
                    "DOMAIN_GROUPS": "html/constants/domain_groups.json",
                },2400)

    with tab4:

        st.header("Data Licenses :vertical_traffic_light:")
        st.write("This section explores the *self-reported* data licenses by the creators of each dataset.")

        tab4_intro = """
        Note a few important limitations:

        * The legal status of data licenses is not always clear and may be different by jurisdiction.
        * Despite our best efforts, omissions or mistakes are possible.
        * This transparency initative is **not** intended as legal advice, and bears no responsibility on how the *self-reported* licenses are used.
        """
        st.markdown(tab4_intro)

        if submitted:
            st.subheader("License Distribution")
            st.write("Here we see the license distribution of those collected by the Data Provenance Initiative.")
            insert_metric_container("License Distribution", "licenses", metrics)

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

            tab2_metrics = util.compute_metrics(tab2_selected_df, INFO["constants"])
            display_metrics(tab2_metrics, df_metadata)

            with st.container():
                collection_info_keys = [
                    "Collection Name",
                    "Collection URL",
                    "Collection Hugging Face URL",
                    "Collection Paper Title",
                ]
                dataset_info_keys = [
                    "Unique Dataset Identifier",
                    "Paper Title",
                    "Dataset URL",
                    "Hugging Face URL",
                ]
                data_characteristics_info_keys = [
                    "Format", "Languages", "Task Categories",
                    ("Inferred Metadata", "Text Topics"),
                    # "Text Domains", 
                ]
                data_provenance_info_keys = ["Creators", "Text Sources", "Licenses"]

                def extract_infos(df, key, numerical=False):
                    if isinstance(key, tuple):
                        dds = df[key[0]].tolist()
                        # st.write(dds)
                        entries = [dd.get(key[1], []) for dd in dds]
                        # st.write(entries)
                    else:
                        entries = df[key].tolist()
                    if not entries:
                        return []
                    elif numerical:
                        return np.mean([x for x in entries if x])
                    elif key == "Licenses":
                            return set([x["License"] for xs in entries for x in xs if x and x["License"]])
                    elif isinstance(entries[0], list):
                        return list(set([x for xs in entries if xs for x in xs if x]))
                    else:
                        return list(set([x for x in entries if x]))

                # st.caption("Collection Information")
                # for info_key in collection_info_keys:
                #     st.text(f"{item}: {extract_infos(tab2_selected_df, info_key)}")

                def format_markdown_entry(dset_info, info_key):
                    if dset_info:
                        info_key = info_key if isinstance(info_key, str) else info_key[1]
                        markdown_txt = dset_info
                        if isinstance(dset_info, list) or isinstance(dset_info, set):
                            # if len(dset_info) == 1:
                            #     markdown_txt = list(dset_info)[0]
                            # else:
                            markdown_txt = "\n* " + "\n* ".join([str(x) for x in dset_info])
                        st.markdown(f"{info_key}: {markdown_txt}")

                # st.write(tab2_selected_df)
                if dataset_select != "All":
                    st.subheader("Dataset Information")
                    for info_key in dataset_info_keys:
                        # st.write(info_key)
                        dset_info = extract_infos(tab2_selected_df, info_key)
                        if len(dset_info):
                            format_markdown_entry(dset_info[0], info_key)

                st.subheader("Data Characteristics")
                for info_key in data_characteristics_info_keys:
                    dset_info = extract_infos(tab2_selected_df, info_key)
                    # st.write(dset_info)
                    format_markdown_entry(dset_info, info_key)

                st.subheader("Data Statistics")
                # for info_key in data_characteristics_info_keys:
                dset_info = extract_infos(tab2_selected_df, ("Text Metrics", "Num Dialogs"), numerical=True)
                format_markdown_entry(round(dset_info, 0), "Num Exs")
                dset_infos = [extract_infos(tab2_selected_df, info_key, numerical=True) for info_key in [
                    ("Text Metrics", "Min Inputs Length"),
                    ("Text Metrics", "Mean Inputs Length"),
                    ("Text Metrics", "Max Inputs Length")]]
                format_markdown_entry("   |   ".join([str(round(x, 1)) for x in dset_infos]), "Input Length (characters) [Minimum | Mean | Maximum]")
                dset_infos = [extract_infos(tab2_selected_df, info_key, numerical=True) for info_key in [
                    ("Text Metrics", "Min Targets Length"),
                    ("Text Metrics", "Mean Targets Length"),
                    ("Text Metrics", "Max Targets Length")]]
                format_markdown_entry("   |   ".join([str(round(x, 1)) for x in dset_infos]), "Target Length (characters) [Minimum | Mean | Maximum]")

                st.subheader("Data Provenance")
                for info_key in data_provenance_info_keys:
                    dset_info = extract_infos(tab2_selected_df, info_key)
                    format_markdown_entry(dset_info, info_key)

        
    ### SIDEBAR STARTS HERE

    # with st.sidebar:
        
    #     st.markdown("""Select the preferred criteria for your datasets.""")

    #     with st.form("data_selection"):

    #         # st.write("Select the acceptable license values for constituent datasets")
    #         license_multiselect = st.select_slider(
    #             'Select the datasets licensed for these use cases',
    #             options=constants.LICENSE_USE_CLASSES,
    #             value="Academic-Only")

    #         license_attribution = st.toggle('Exclude Datasets w/ Attribution Requirements', value=False)
    #         license_sharealike = st.toggle('Exclude Datasets w/ Share Alike Requirements', value=False)
    #         openai_license_override = st.toggle('Include Datasets w/ OpenAI-generated data', value=False)

    #         # with data_select_cols[1]:
    #         language_multiselect = st.multiselect(
    #             'Select the languages to cover in your datasets',
    #             ["All"] + list(INFO["constants"]["LANGUAGE_GROUPS"].keys()),
    #             ["All"])

    #         # with data_select_cols[2]:
    #         taskcats_multiselect = st.multiselect(
    #             'Select the task categories to cover in your datasets',
    #             ["All"] + list(INFO["constants"]["TASK_GROUPS"].keys()),
    #             ["All"])

    #         with st.expander("More advanced criteria"):

    #             # format_multiselect = st.multiselect(
    #             #     'Select the format types to cover in your datasets',
    #             #     ["All"] + INFO["constants"]["FORMATS"],
    #             #     ["All"])

    #             domain_multiselect = st.multiselect(
    #                 'Select the domain types to cover in your datasets',
    #                 ["All"] + list(INFO["constants"]["DOMAIN_GROUPS"].keys()),
    #                 # ["All", "Books", "Code", "Wiki", "News", "Biomedical", "Legal", "Web", "Math+Science"],
    #                 ["All"])

    #             time_range_selection = st.slider(
    #                 "Select data release time constraints",
    #                 value=(datetime(2000, 1, 1), datetime(2023, 12, 1)))

    #         # Every form must have a submit button.
    #         submitted = st.form_submit_button("Submit Selection")

    #### SIDEBAR ENDS HERE

            



if __name__ == "__main__":
    streamlit_app()
