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


def compute_metrics(df):
    # Datasets with the same Dataset Name may have different languages
    # but not different tasks, topics, or licenses. Let's not double count these.
    # Drop duplicate rows based on 'Dataset Name' column
    df_unique = df.drop_duplicates(subset='Dataset Name')

    datasets_count = dict(Counter(df["Unique Dataset Identifier"]))
    collections_count = dict(Counter(df["Collection"]))
    language_counts = dict(Counter([lang for row in df["Languages"] for lang in row]))
    taskcat_counts = dict(Counter([tc for row in df_unique["Task Categories"] for tc in row]))
    format_counts = dict(Counter([fmt for row in df_unique["Format"] for fmt in row]))
    license_counts = dict(Counter([license_info["License"] for licenses in df_unique["Licenses"] for license_info in licenses if license_info["License"]]))

    return {
        "collections": collections_count,
        "datasets": datasets_count,
        "languages": language_counts,
        "task_categories": taskcat_counts,
        "licenses": license_counts,
        "formats": format_counts,
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
        subset_topics = set([tc for row in subset_df["Inferred Metadata"] for tc in row.get("Text Topics", [])])
        subset_sources = set([tc for row in subset_df["Text Sources"] for tc in row])
        subset_model_gen = Counter([tc for row in subset_df["Model Generated"] for tc in row]).most_common(1)
        subset_mean_inp_len = np.mean([row["Mean Inputs Length"] for row in subset_df["Text Metrics"]])
        subset_mean_tar_len = np.mean([row["Mean Targets Length"] for row in subset_df["Text Metrics"]])
        total_dialogs = subset_df['Text Metrics'].apply(lambda x: x.get('Num Dialogs') if isinstance(x, dict) else 0).fillna(0).sum()
        table["# Datasets"].append(len(subset_datasets))
        table["# Exs"].append(total_dialogs)
        table["# Languages"].append(len(subset_langs)) 
        table["# Tasks"].append(len(subset_taskcats))
        table["# Topics"].append(len(subset_topics))
        table["# Sources"].append(len(subset_sources))
        table["Generated By"].append(subset_model_gen[0][0] if subset_model_gen else "")
        table["Mean Input Words"].append(round(subset_mean_inp_len, 1))
        table["Mean Target Words"].append(round(subset_mean_tar_len, 1))
        table["% Datasets Used"].append(f"{round(100* len(subset_datasets) / len(original_datasets), 1)} %")
    return pd.DataFrame(table)


def plot_altair_piechart(counts, title, threshold_cutoff=16):
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


def plot_altair_barchart(counts):

    df = pd.DataFrame({
        "category": list(counts.keys()),
        "count": list(counts.values()),
    })

    total = df['count'].sum()

    # create a new column for percentage
    df['percentage'] = 100 * df['count'] / total

    # sort the DataFrame and only select the top 20 categories
    df = df.sort_values('count', ascending=False)[:30]

    # for having a different color for each bar
    palette = alt.Scale(scheme='category20')

    # create the chart
    chart = alt.Chart(df).mark_bar().encode(
        x='count:Q',
        # y=alt.Y('category:N', sort='-x'),
        y=alt.Y('category:N', sort=alt.EncodingSortField(field="count", op="sum", order='descending')),
        color=alt.Color('category:N', scale=palette, legend=None),
        tooltip=['category', 'count', 'percentage']
    )

    # text label for percentage
    text = chart.mark_text(
        align='left',
        baseline='middle',
        dx=3  # Nudges text to right so it doesn't appear on top of the bar
    ).encode(
        text=alt.Text('text:N')
    )

    # Concatenate count and percentage fields for the text label
    df['text'] = df['count'].astype(str) + ' (' + df['percentage'].round(1).astype(str) + '%)'

    return (chart + text).properties(height=700, width=800)