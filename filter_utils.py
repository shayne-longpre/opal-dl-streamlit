import os
import numpy as np
import pandas as pd
from collections import Counter, defaultdict

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
        resolved_use_case = "unclear"
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

# extract licenses and license_urls for each aggregator.
# classify each set of pairs, and resolve them, then assign them to new fields
def map_license_criteria(data_summary, all_constants):

    # Unpack licenses for each dataset
    our_uid_to_license_infos = defaultdict(list)
    hf_uid_to_license_infos = defaultdict(list)
    github_uid_to_license_infos = defaultdict(list)
    pwc_uid_to_license_infos = defaultdict(list)
    for row in data_summary:
        uid = row["Unique Dataset Identifier"]
        for license_info in row["Licenses"]:
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


    # def apply_license_classes_to_df(df, resolved_classes, aggregator):
    #     # update dataframe with columns for use, attribution, share_alike
    #     df[f'License Use ({aggregator})'] = df['Unique Dataset Identifier'].map(lambda x: resolved_classes.get(x)[0])
    #     df[f'License Attribution ({aggregator})'] = df['Unique Dataset Identifier'].map(lambda x: resolved_classes.get(x)[1])
    #     df[f'License Share Alike ({aggregator})'] = df['Unique Dataset Identifier'].map(lambda x: resolved_classes.get(x)[2])
    #     return df

    # df = apply_license_classes_to_df(df, ours_resolved, "DataProvenance")
    # df = apply_license_classes_to_df(df, hf_resolved, "HuggingFace")
    # df = apply_license_classes_to_df(df, gh_resolved, "GitHub")
    # df = apply_license_classes_to_df(df, pwc_resolved, "PapersWithCode")

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
    selected_licenses,
    selected_license_use,
    selected_license_attribtution,
    selected_license_sharealike,
    selected_languages,
    selected_task_categories,
):
    filtered_df = df

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

    if selected_licenses:
        license_strs = set(all_constants["LICENSE_CLASSES"].keys())
        filtered_df = filtered_df[
            filtered_df["Licenses"].apply(lambda xs: license_strs >= set([x["License"] for x in xs]))
        ]

    if selected_license_use:
        valid_license_use_idx = constants.LICENSE_USE_TYPES.index(selected_license_use)
        valid_license_uses = constants.LICENSE_USE_TYPES[:valid_license_use_idx+1]
        filtered_df = filtered_df[
            filtered_df["License Use (DataProvenance)"].apply(lambda x: x in valid_license_uses)
        ]

    if selected_license_attribtution:
        filtered_df = filtered_df[
            filtered_df["License Attribution (DataProvenance)"].apply(lambda x: x <= int(selected_license_attribtution))
        ]

    if selected_license_sharealike:
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

    return filtered_df