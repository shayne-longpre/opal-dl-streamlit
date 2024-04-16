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
    use_cases = [license_criteria["use"] for license_criteria in license_criterias]
    attributions = [license_criteria["attribution"] for license_criteria in license_criterias]
    share_alikes = [license_criteria["share_alike"] for license_criteria in license_criterias]

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


def map_license_criteria(data_summary, all_constants):

    # Unpack licenses for each dataset. {uid --> (license_name, license_url)}
    our_uid_to_license_infos = defaultdict(list)
    hf_uid_to_license_infos = defaultdict(list)
    github_uid_to_license_infos = defaultdict(list)
    pwc_uid_to_license_infos = defaultdict(list)
    # Same as ours, but excludes OpenAI Terms:
    our_uid_to_license_infos_no_openai = defaultdict(list)

    for row in data_summary:
        uid = row["Unique Dataset Identifier"]
        for license_info in row["Licenses"]:
            license_name = license_info["License"]
            license_url = license_info["License URL"]
            our_uid_to_license_infos[uid].append((license_name, license_url))
            if license_info["License"] != "OpenAI":
                our_uid_to_license_infos_no_openai[uid].append((license_name, license_url))
        # If OpenAI was the only license, we add Unspecified so there isn't nothing there.
        if len(our_uid_to_license_infos_no_openai[uid]) == 0:
            our_uid_to_license_infos_no_openai[uid].append(("Unspecified", None))

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
    ours_resolved, ours_openai_resolved, hf_resolved, gh_resolved, pwc_resolved = {}, {}, {}, {}, {}
    for uid in our_uid_to_license_infos.keys():
        ours_resolved[uid] = classify_and_resolve_licenses(our_uid_to_license_infos[uid], all_constants)
        ours_openai_resolved[uid] = classify_and_resolve_licenses(our_uid_to_license_infos_no_openai[uid], all_constants)
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
    data_summary = add_license_classes_to_summaries(data_summary, ours_openai_resolved, "DataProvenance IgnoreOpenAI")
    data_summary = add_license_classes_to_summaries(data_summary, hf_resolved, "HuggingFace")
    data_summary = add_license_classes_to_summaries(data_summary, gh_resolved, "GitHub")
    data_summary = add_license_classes_to_summaries(data_summary, pwc_resolved, "PapersWithCode")
    # st.write([r for r in data_summary if r["Collection"] == "GPTeacher"])

    return data_summary


def apply_filters(
    df,
    all_constants,
    selected_collection,
    selected_licenses,
    selected_license_use,
    openai_license_override,
    selected_license_attribution,
    selected_license_sharealike,
    selected_languages,
    selected_task_categories,
    selected_domains,
    selected_start_time,
    selected_end_time,
):
    filtered_df = df
    # st.write(filtered_df.columns)

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

    if selected_collection:
        filtered_df = filtered_df[filtered_df["Collection"] == selected_collection]

    if not filtered_df.empty and selected_licenses:
        license_strs = set(all_constants["LICENSE_CLASSES"].keys())
        filtered_df = filtered_df[
            filtered_df["Licenses"].apply(lambda xs: license_strs >= set([x["License"] for x in xs]))
        ]

    if not filtered_df.empty and selected_license_use:
        # use_key = "License Use (DataProvenance IgnoreOpenAI)" if openai_license_override else "License Use (DataProvenance)"
        valid_license_use_idx = constants.LICENSE_USE_TYPES.index(selected_license_use)
        valid_license_uses = [x.lower() for x in constants.LICENSE_USE_TYPES[:valid_license_use_idx + 1]]

        if openai_license_override:
            if "DataProvenance" in selected_licenses:
                selected_licenses.remove("DataProvenance")
            use_keys = ["DataProvenance IgnoreOpenAI"] + selected_licenses
        else:
            use_keys = selected_licenses

        if "DataProvenance-GitHub" in selected_licenses:
            filtered_df["License Use (DataProvenance)"] = filtered_df["License Use (DataProvenance)"].apply(
                lambda x: x if x != "Unspecified" else filtered_df["License Use (GitHub)"]
            )
            filtered_df = filtered_df[
                filtered_df["License Use (DataProvenance)"].apply(lambda x: x in valid_license_uses)
            ]
        else:
            if "DataProvenance-GitHub" in use_keys:
                selected_licenses.remove("DataProvenance-GitHub")
            filtered_df = filtered_df[
                filtered_df.apply(lambda row: any(row[f"License Use ({key})"] in valid_license_uses for key in use_keys), axis=1)
            ]

        # filtered_df = filtered_df[
        #    filtered_df[use_key].apply(lambda x: x in valid_license_uses)
        # ]

    # st.write(len(filtered_df))
    if not filtered_df.empty and selected_license_attribution:
        filtered_df = filtered_df[
            filtered_df["License Attribution (DataProvenance)"].apply(lambda x: x <= int(selected_license_attribution))
        ]

    if not filtered_df.empty and selected_license_sharealike:
        filtered_df = filtered_df[
            filtered_df["License Share Alike (DataProvenance)"].apply(lambda x: x <= int(selected_license_sharealike))
        ]

    if not filtered_df.empty and "All" not in selected_languages:
        lang_strs = set(
            [
                lang_str
                for k in selected_languages
                for lang_str in all_constants["LANGUAGE_GROUPS"].get(k, [])
            ]
        )
        filtered_df = filtered_df[
            filtered_df["Languages"].apply(lambda x: lang_strs >= set(x))
        ]

    if not filtered_df.empty and "All" not in selected_task_categories:
        taskcat_strs = set(
            [
                taskcat_str
                for k in selected_task_categories
                for taskcat_str in all_constants["TASK_GROUPS"].get(k, [])
            ]
        )
        filtered_df = filtered_df[
            filtered_df["Task Categories"].apply(lambda x: taskcat_strs >= set(x))
        ]
    if not filtered_df.empty and "All" not in selected_domains:
        text_source_strs = set(
            [
                source_str
                for k in selected_domains
                for source_str in all_constants["DOMAIN_GROUPS"].get(k, [])
            ]
        )
        filtered_df = filtered_df[
            filtered_df["Text Sources"].apply(lambda x: text_source_strs >= set(x))
        ]

    if not filtered_df.empty and (selected_start_time or selected_end_time):

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
