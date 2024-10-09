from census import Census, Census_vars
from geometry import TargetGeometry, Boundary, TargetGeometry_vars, Boundary_vars
import yaml

with open("../configuration/targetgeom_config.yaml", "r") as f:
    tg_config = yaml.load(f, Loader=yaml.FullLoader)

with open("../configuration/gen_config.yaml", "r") as f:
    gen_config = yaml.load(f, Loader=yaml.FullLoader)

for cen_country, year_list in gen_config["census_years"].items():
    print(cen_country)
    for cen_year in year_list:
        print(cen_year)

        with open(f"../configuration/{cen_country}_{cen_year}_config.yaml", "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)

        census_config = config["census"]
        boundary_config = config["boundaries"]

        census = Census(
            Census_vars(
                output_path=gen_config["output_path"],
                output_filetype=gen_config["output_filetype"],
                **census_config,
            )
        )

        list_of_boundaries = []

        for bound, bound_details in boundary_config.items():

            tmp_boundary = Boundary(
                Boundary_vars(
                    census_year=census.vars.year,
                    census_country=census.vars.country,
                    output_path=gen_config["output_path"],
                    output_filetype=gen_config["output_filetype"],
                    **bound_details,
                )
            )

            tmp_boundary.get_geometry_data()
            tmp_boundary.process()

            list_of_boundaries.append(tmp_boundary)

        if len(list_of_boundaries) > 1:

            boundary = list_of_boundaries[0].merge_boundaries(list_of_boundaries[1:])

        else:
            boundary = tmp_boundary

        for geom, geom_details in tg_config.items():
            print(geom_details["geom_name"])
            target_geom = TargetGeometry(
                TargetGeometry_vars(
                    census_year=census.vars.year,
                    census_country=census.vars.country,
                    output_path=gen_config["output_path"],
                    output_filetype=gen_config["output_filetype"],
                    **geom_details,
                )
            )
            target_geom.get_geometry_data()
            target_geom.clean_tg()
            target_geom.process()
            target_geom.assigntoboundary(
                boundary,
            )
            target_geom.create_uid_of_geocode_field()
            target_geom.dedup_addresses()
            target_geom.create_tgforlinking()
            census.geocode(target_geom)
