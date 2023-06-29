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

from src import constants


def apply_filters(
    df,
    selected_licenses,
    selected_languages,
    selected_task_categories,
    selected_formats,
    selected_text_domains,
    time_range_selection,
):
    filtered_df = df

    # Some sanity checks:
    all_langs = set([v for vs in constants.LANGUAGE_GROUPS.values() for v in vs])
    option_langs = set(
        [lang for langs in filtered_df["Languages"].tolist() for lang in langs]
    )
    assert all_langs >= option_langs, f"Missing Languages: {option_langs - all_langs}"
    all_tcats = set([v for vs in constants.TASK_CATEGORY_GROUPS.values() for v in vs])
    option_tcats = set(
        [tc for tcs in filtered_df["Task Categories"].tolist() for tc in tcs]
    )
    assert (
        all_tcats >= option_tcats
    ), f"Missing Task Categories: {option_tcats - all_tcats}"

    if selected_licenses and "All" not in selected_licenses:
        license_strs = set(
            [
                license_str
                for k in selected_licenses
                for license_str in constants.LICENSE_GROUPS[k]
            ]
        )
        filtered_df = filtered_df[
            filtered_df["Licenses"].apply(lambda xs: license_strs >= set([x["License"] for x in xs]))
        ]

    def filter_on_key(df, selection_criteria, key, options):
        if selection_criteria and "All" not in selection_criteria:
            selected_strs = set(
                [
                    select_str
                    for k in selection_criteria
                    for select_str in options[k]
                ]
            )
            df = df[
                df[key].apply(lambda x: selected_strs >= set(x))
            ]
        return df

    filtered_df = filter_on_key(filtered_df, selected_languages, "Languages", constants.LANGUAGE_GROUPS)
    filtered_df = filter_on_key(filtered_df, selected_task_categories, "Task Categories", constants.TASK_CATEGORY_GROUPS)
    filtered_df = filter_on_key(filtered_df, selected_formats, "Format", constants.FORMAT_GROUPS)
    filtered_df = filter_on_key(filtered_df, selected_text_domains, "Text Domains", constants.DOMAIN_GROUPS)
    return filtered_df


def compute_metrics(df):
    datasets_count = dict(Counter(df["Unique Dataset Identifier"]))
    collections_count = dict(Counter(df["Collection"].tolist()).most_common())
    language_counts = dict(Counter([lang for row in df["Languages"] for lang in row]).most_common())
    taskcat_counts = dict(Counter([tc for row in df["Task Categories"] for tc in row]).most_common())
    license_counts = dict(Counter([license_info["License"] for licenses in df["Licenses"].tolist() for license_info in licenses if license_info["License"]]).most_common())
    
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
        original_datasets = set(original_subset_df["Unique Dataset Identifier"])
        subset_datasets = set(subset_df["Unique Dataset Identifier"])
        subset_langs = set([lang for row in subset_df["Languages"] for lang in row])
        subset_taskcats = set([tc for row in subset_df["Task Categories"] for tc in row])
        table["Num Datasets"].append(len(subset_datasets))
        table["Num Languages"].append(len(subset_langs)) 
        table["Num Tasks"].append(len(subset_taskcats))
        table["Num Exs"].append("Coming soon.")
        table["% Dataset Used"].append(f"{round(100* len(subset_datasets) / len(original_datasets), 1)} %")
    return pd.DataFrame(table)


def plot_altair_piechart(counts, title, threshold_cutoff=20):
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
