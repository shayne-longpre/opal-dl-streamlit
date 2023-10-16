import os
import numpy as np
import pandas as pd
from collections import Counter, defaultdict

import streamlit as st

from src import constants

def classify_license(license_name, license_url, all_constants):
    if license_name == "Custom":
        use_case, attribution, share_alike = all_constants["CUSTOM_LICENSE_CLASSES"].get(license_url, ("?", "?", "?"))
    else:
        use_case, attribution, share_alike = all_constants["LICENSE_CLASSES"][license_name]
    return {
        "use": use_case, 
        "attribution": int(attribution) if attribution.isnumeric() else 1, 
        "share_alike": int(share_alike) if share_alike.isnumeric() else 1,
    }

def resolve_multiple_licenses(license_criterias):
    if not license_criterias:
        # Return empty if no licenses from this aggregator
        return ["", "", ""]
    use_cases = [l["use"] for l in license_criterias]
    attributions = [l["attribution"] for l in license_criterias]
    share_alikes = [l["share_alike"] for l in license_criterias]

    if "?" in use_cases:
        resolved_use_case = "academic-only"
    elif "Acad" in use_cases:
        resolved_use_case = "academic-only"
    elif "NC" in use_cases:
        resolved_use_case = "non-commercial"
    elif "Unspecified" in use_cases:
        resolved_use_case = "unspecified"
    elif "All":
        resolved_use_case = "commercial"
    
    resolved_attribution = max(attributions)
    resolved_share_alikes = max(share_alikes)
    return resolved_use_case, resolved_attribution, resolved_share_alikes


def map_license_criteria(data_summary, all_constants, openai_override=False):

    # Unpack licenses for each dataset
    our_uid_to_license_infos = defaultdict(list)
    hf_uid_to_license_infos = defaultdict(list)
    github_uid_to_license_infos = defaultdict(list)
    pwc_uid_to_license_infos = defaultdict(list)

    for row in data_summary:
        uid = row["Unique Dataset Identifier"]
        for license_info in row["Licenses"]:
            # Do not count OpenAI licenses if override is active.
            if openai_override and license_info["License"] == "OpenAI":
                continue
            license_name = license_info["License"]
            license_url = license_info["License URL"]
            our_uid_to_license_infos[uid].append((license_name, license_url))

        gh_license = row.get("Inferred Metadata", {}).get("GitHub License", None)
        hfy_license = row.get("Inferred Metadata", {}).get("HF Yaml License", None)
        hfc_license = row.get("Inferred Metadata", {}).get("HF Config License", None)
        pwc_license = row.get("Inferred Metadata", {}).get("PwC License Name", None)
        if hfy_license:
            hf_uid_to_license_infos[uid].append((hfy_license, None))
        if hfc_license:
            hf_uid_to_license_infos[uid].append((hfc_license, None))
        if gh_license:
            github_uid_to_license_infos[uid].append((gh_license, None))
        if pwc_license:
            pwc_uid_to_license_infos[uid].append((pwc_license, None))

    # valid_licenses = list(all_constants["LICENSE_CLASSES"].keys())
    # print(set([v for vs in pwc_uid_to_license_infos.values() for (v, _) in vs]) - set(valid_licenses))
    # print(set([v for vs in github_uid_to_license_infos.values() for (v, _) in vs]) - set(valid_licenses))

    def classify_and_resolve_licenses(license_infos, all_constants):
        classified_licenses = []
        for (license_name, license_url) in license_infos:
            classifications = classify_license(license_name, license_url, all_constants)
            classified_licenses.append(classifications)
        resolved_criteria = resolve_multiple_licenses(classified_licenses)
        return resolved_criteria

    # classify and resolve licenses for each dataset and each aggregator
    ours_resolved, hf_resolved, gh_resolved, pwc_resolved = {}, {}, {}, {}
    for uid in our_uid_to_license_infos.keys():
        ours_resolved[uid] = classify_and_resolve_licenses(our_uid_to_license_infos[uid], all_constants)
        hf_resolved[uid] = classify_and_resolve_licenses(hf_uid_to_license_infos[uid], all_constants)
        gh_resolved[uid] = classify_and_resolve_licenses(github_uid_to_license_infos[uid], all_constants)
        pwc_resolved[uid] = classify_and_resolve_licenses(pwc_uid_to_license_infos[uid], all_constants)

    def add_license_classes_to_summaries(data_summary, resolved_classes, aggregator):
        # update dataframe with columns for use, attribution, share_alike
        for row in data_summary:
            row[f'License Use ({aggregator})'] = resolved_classes[row['Unique Dataset Identifier']][0]
            row[f'License Attribution ({aggregator})'] = resolved_classes[row['Unique Dataset Identifier']][1]
            row[f'License Share Alike ({aggregator})'] = resolved_classes[row['Unique Dataset Identifier']][2]
        return data_summary

    data_summary = add_license_classes_to_summaries(data_summary, ours_resolved, "DataProvenance")
    data_summary = add_license_classes_to_summaries(data_summary, hf_resolved, "HuggingFace")
    data_summary = add_license_classes_to_summaries(data_summary, gh_resolved, "GitHub")
    data_summary = add_license_classes_to_summaries(data_summary, pwc_resolved, "PapersWithCode")

    return data_summary


def apply_filters(
    df,
    all_constants,
    selected_collection,
    selected_licenses,
    selected_license_use,
    selected_license_attribution,
    selected_license_sharealike,
    selected_languages,
    selected_task_categories,
    selected_domains,
    selected_start_time,
    selected_end_time,
):
    filtered_df = df
    st.write(len(filtered_df))

    # Some sanity checks:
    all_langs = set([v for vs in all_constants["LANGUAGE_GROUPS"].values() for v in vs])
    option_langs = set(
        [lang for langs in filtered_df["Languages"].tolist() for lang in langs]
    )
    assert all_langs >= option_langs, f"Missing Languages: {option_langs - all_langs}"
    all_tcats = set([v for vs in all_constants["TASK_GROUPS"].values() for v in vs])
    option_tcats = set(
        [tc for tcs in filtered_df["Task Categories"].tolist() for tc in tcs]
    )
    assert (
            all_tcats >= option_tcats
    ), f"Missing Task Categories: {option_tcats - all_tcats}"
    all_sources = set([v for vs in all_constants["DOMAIN_GROUPS"].values() for v in vs])
    option_sources = set(
        [src for sources in filtered_df["Text Sources"].tolist() for src in sources]
    )
    assert all_sources >= option_sources, f"Missing Text Sources: {option_sources - all_sources}"

    st.write(len(filtered_df))
    if selected_collection:
        filtered_df = filtered_df[filtered_df["Collection"] == selected_collection]

    st.write(len(filtered_df))
    if selected_licenses:
        license_strs = set(all_constants["LICENSE_CLASSES"].keys())
        filtered_df = filtered_df[
            filtered_df["Licenses"].apply(lambda xs: license_strs >= set([x["License"] for x in xs]))
        ]

    st.write(len(filtered_df))
    if selected_license_use:
        valid_license_use_idx = constants.LICENSE_USE_TYPES.index(selected_license_use)
        st.write(valid_license_use_idx)
        valid_license_uses = constants.LICENSE_USE_TYPES[:valid_license_use_idx+1]
        st.write(valid_license_uses)
        st.write(filtered_df["License Use (DataProvenance)"])
        filtered_df = filtered_df[
            filtered_df["License Use (DataProvenance)"].apply(lambda x: x in valid_license_uses)
        ]

    st.write(len(filtered_df))
    if selected_license_attribution:
        filtered_df = filtered_df[
            filtered_df["License Attribution (DataProvenance)"].apply(lambda x: x <= int(selected_license_attribution))
        ]

    st.write(len(filtered_df))
    if selected_license_sharealike:
        st.write(filtered_df.columns)
        st.write(filtered_df["License Share Alike (DataProvenance)"])
        filtered_df = filtered_df[
            filtered_df["License Share Alike (DataProvenance)"].apply(lambda x: x <= int(selected_license_sharealike))
        ]

    if selected_languages:
        lang_strs = set(
            [
                lang_str
                for k in selected_languages
                for lang_str in all_constants["LANGUAGE_GROUPS"][k]
            ]
        )
        filtered_df = filtered_df[
            filtered_df["Languages"].apply(lambda x: lang_strs >= set(x))
        ]

    if selected_task_categories:
        taskcat_strs = set(
            [
                taskcat_str
                for k in selected_task_categories
                for taskcat_str in all_constants["TASK_GROUPS"][k]
            ]
        )
        filtered_df = filtered_df[
            filtered_df["Task Categories"].apply(lambda x: taskcat_strs >= set(x))
        ]
    if selected_domains:
        text_source_strs = set(
            [
                source_str
                for k in selected_domains
                for source_str in all_constants["DOMAIN_GROUPS"][k]
            ]
        )
        filtered_df = filtered_df[
            filtered_df["Text Sources"].apply(lambda x: text_source_strs >= set(x))
        ]
    if selected_start_time or selected_end_time:

        def get_min_date(metadata):
            date_columns = ["S2 Date", "HF Date", "GitHub Date"]
            dates = [metadata.get(col, "") for col in date_columns]
            valid_dates = [pd.to_datetime(date, format='%Y-%m-%d', errors='coerce') for date in dates if date]
            if valid_dates:
                return min(valid_dates)
            return pd.NaT

        filtered_df['Estimated Creation Date'] = filtered_df['Inferred Metadata'].apply(get_min_date)
        if selected_start_time:
            filtered_df = filtered_df[filtered_df['Estimated Creation Date'] >= pd.to_datetime(selected_start_time)]
        if selected_end_time:
            filtered_df = filtered_df[filtered_df['Estimated Creation Date'] <= pd.to_datetime(selected_end_time)]

    return filtered_df