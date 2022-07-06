def new():
    pass


def link_geocode_to_icem(
    self,
    linked,
    partition,
    new_uid,
    geom_name,
    census_fields,
    census_output_params,
    tmpcensusdir,
):
    """_summary_
    :func:`~new`
    :param linked: _description_
    :type linked: _type_
    :param partition: _description_
    :type partition: _type_
    :param new_uid: _description_
    :type new_uid: _type_
    :param geom_name: _description_
    :type geom_name: _type_
    :param census_fields: _description_
    :type census_fields: _type_
    :param census_output_params: _description_
    :type census_output_params: _type_
    :param tmpcensusdir: _description_
    :type tmpcensusdir: _type_
    """

    census = pd.read_parquet(
        tmpcensusdir,
        filters=[[(census_output_params.partition_on, "=", f"{partition}")]],
        columns=[census_output_params.new_uid, census_fields.uid],
    )
    print(census.info())
    print(linked.info())
    new_trial = pd.merge(
        left=census, right=linked, on=census_output_params.new_uid, how="inner"
    )
    new_trial = new_trial[[census_fields.uid, new_uid]]
    new_trial.to_csv(
        utils.make_path(self.output_dir, geom_name)
        / f"{self.census_year}_{geom_name}_{partition}_lkup.tsv",
        sep="\t",
        index=False,
    )
    pass
