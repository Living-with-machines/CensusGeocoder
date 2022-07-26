import pandas as pd


def setup_eval(partition_on, partition_list):
    inds_list = []
    adds_list = []
    adds_list_dup = []
    inds_list_all = []
    adds_list_all = []
    eval_df = pd.DataFrame({partition_on: partition_list})
    return inds_list, adds_list, adds_list_dup, inds_list_all, adds_list_all, eval_df


# def append_lists(
#     cen_geom_lkp, census_params, new_uid, inds_list, adds_list,
# ):

#     inds_list.append(cen_geom_lkp[census_params.census_fields.uid].nunique())
#     adds_list.append(cen_geom_lkp[new_uid].nunique())

#     return inds_list, adds_list


# def append_list(df, cols, *lists):
#     for col, list1 in list(zip(cols, lists)):
#         list1.append(df[col].nunique())
#         print(col, list1)
#     return lists


def append_list(df, col, list_to_append):
    if df.empty:
        list_to_append.append(0)
    else:
        list_to_append.append(df[col].nunique())
    return list_to_append


def eval_df_add(
    eval_df,
    inds_list,
    adds_list,
    adds_list_dup,
    inds_list_all,
    adds_list_all,
    output_dir,
    geom_name,
):
    eval_df["inds_linked"] = inds_list
    eval_df["adds_linked"] = adds_list
    eval_df["adds_duplink_count"] = adds_list_dup
    eval_df["inds_all"] = inds_list_all
    eval_df["adds_all"] = adds_list_all

    eval_df["inds_linked_perc"] = (eval_df["inds_linked"] / eval_df["inds_all"]) * 100
    eval_df["adds_linked_perc"] = (eval_df["adds_linked"] / eval_df["adds_all"]) * 100
    eval_df["adds_duplink_perc"] = (
        eval_df["adds_duplink_count"] / eval_df["adds_all"]
    ) * 100
    print(eval_df)

    eval_df.to_csv(output_dir / f"{geom_name}_summary.tsv", sep="\t", index=False)
    pass
