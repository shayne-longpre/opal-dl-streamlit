from ast import literal_eval
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import json
import os
import gzip
import numpy as np
import pandas as pd
import copy
import altair as alt

import streamlit as st

import constants


def read_dataset_table(fp):
    list_cols = {k: literal_eval for k in ["Collection URL", "Languages", "Task Domains", "Task Categories", "Task Reasoning"]}
    df = pd.read_csv(fp, converters=list_cols).fillna("")

    # Annotate license categories (TODO: do this offline)
    # for license_name, license_strs in constant._LICENSE_GROUPINGS.items():
    #     if license_strs is None:
    #         other_strs = set([lic for license_s in constant._LICENSE_GROUPINGS.values() for lic in licenses])
    #         df[f"License Category: {license_name}"] = ~df['License'].isin(other_strs)
    #     else:
    #         df[f"License Category: {license_name}"] = df['License'].isin(license_strs)

    # Annotate language categories (TODO: do this offline)
    # for language_group, language_strs in constant._LANGUAGE_GROUPS.items():
    #     df[f"Language: {language_group}"] = df['Languages'].apply(lambda x: len(x.intersection(language_strs)) > 0)

    # # Annotate language categories (TODO: do this offline)
    # for language_group, language_strs in constant._LANGUAGE_GROUPS.items():
    #     df[f"Language: {language_group}"] = df['Languages'].apply(lambda x: len(x.intersection(language_strs)) > 0)

    return df

def apply_filters(
    df,
    selected_licenses,
    selected_languages,
    selected_task_categories,
):
    filtered_df = copy.deepcopy(df)
    if "All" not in selected_licenses:
        # st.write(selected_licenses)
        license_strs = [license_str for k in selected_licenses for license_str in constants._LICENSE_GROUPINGS[k]]
        filtered_df = filtered_df[filtered_df["License"].isin(license_strs)]
    if "All" not in selected_languages:
        # st.write("Lang Filter")
        lang_strs = set([lang_str for k in selected_languages for lang_str in constants._LANGUAGE_GROUPS[k]])
        filtered_df = filtered_df[filtered_df["Languages"].apply(lambda x: len(set(x).intersection(lang_strs)) > 0)]
    if "All" not in selected_task_categories:
        taskcat_strs = set([taskcat_str for k in selected_task_categories for taskcat_str in constants._TASK_CATEGORY_GROUPS[k]])
        filtered_df = filtered_df[filtered_df["Task Categories"].apply(lambda x: len(set(x).intersection(taskcat_strs)) > 0)]

    return filtered_df

def compute_metrics(df):
    datasets_count = dict(Counter(df["Dataset Name"]))
    collections_count = dict(Counter(df["Collection"].tolist()).most_common())
    language_counts = dict(Counter([lang for row in df["Languages"] for lang in row]).most_common())
    taskcat_counts = dict(Counter([tc for row in df["Task Categories"] for tc in row]).most_common())
    license_counts = dict(Counter(df["License"].tolist()).most_common())
    
    return {
        "collections": collections_count,
        "datasets": datasets_count,
        "languages": language_counts,
        "task_categories": taskcat_counts,
        "licenses": license_counts,
    }


def prep_collection_table(df, original_df, metrics):
    table = defaultdict(list)
    for collection in metrics["collections"]:
        table["Collection"].append(collection)
        subset_df = df[df["Collection"] == collection]
        original_subset_df = original_df[original_df["Collection"] == collection]
        original_datasets = set(original_subset_df["Dataset Name"])
        subset_datasets = set(subset_df["Dataset Name"])
        subset_langs = set([lang for row in subset_df["Languages"] for lang in row])
        subset_taskcats = set([tc for row in subset_df["Task Categories"] for tc in row])
        table["Num Datasets"].append(len(subset_datasets))
        table["Num Languages"].append(len(subset_langs)) 
        table["Num Tasks"].append(len(subset_taskcats))
        table["Num Exs"].append("Coming soon.")
        table["% Dataset Used"].append(f"{round(100* len(subset_datasets) / len(original_datasets), 1)} %")
    return pd.DataFrame(table)


def plot_altair_piechart(counts, title, threshold_cutoff=8):
    top_keys = sorted(counts.keys(), reverse=True, key=lambda x: counts[x])[:threshold_cutoff]
    thresholded_counts = {}
    other_count = 0

    for k in counts.keys():
        if k in top_keys:
            thresholded_counts[k] = counts[k]
        else:
            other_count += counts[k]
    thresholded_counts["Other"] = other_count

    vals = list(thresholded_counts.values())
    labels = [k[:15] + "..." if len(k) > 15 else k for k in thresholded_counts.keys()]
    labels = [f"{k} ({c})" for k, c in zip(labels, vals)]
    sorted_labels = [k for (k, c) in sorted(zip(labels, vals), key=lambda x: x[1], reverse=True)]
    val_strs = [str(v) for v in vals]

    source = pd.DataFrame(
        {"category": labels, "value": vals, "counts": val_strs}
    )

    base = alt.Chart(source).encode( # , title=title
        theta=alt.Theta("value:Q", stack=True), color=alt.Color("category:N", sort=sorted_labels) #, legend=None)
    )

    # base = alt.Chart(source, title=title).encode(
    #     theta=alt.Theta("value:Q", stack=True), color=alt.Color(
    #         "category:N", 
    #         legend=alt.Legend(
    #             orient='bottom',
    #             # legendX=130, legendY=-40,
    #             # legendX=0, legendY=-40,
    #             # direction='horizontal',
    #             # titleAnchor='middle'),
    #         )
    #     ))

    pie = base.mark_arc(outerRadius=90)
    text = base.mark_text(radius=120, size=12, color='black').encode(text="counts")

    return pie + text

# def plot_piechart(counts, title, threshold_cutoff=8):
#     top10_threshold = sorted(counts.values(), reverse=True)[threshold_cutoff]
#     thresholded_counts = {}
#     other_count = 0
#     for k, v in counts.items():
#         if v >= top10_threshold:
#             thresholded_counts[k] = v
#         else:
#             other_count += v
#     thresholded_counts["Other"] = other_count

#     # counts = {k: v for k, v in counts.items() if }
#     labels = list(thresholded_counts.keys())
#     vals = list(thresholded_counts.values())
#     fig1, ax1 = plt.subplots()
#     ax1.pie(vals, labels=labels)#, autopct='%1.1f%%')
#             # shadow=True, startangle=90)
#     ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
#     plt.title(title)
#     return fig1