from collections import OrderedDict

import fiona
import fiona.crs
import shapely

from .reach_metrics import reach_metrics
from .network_container import NetworkContainer

# TODO: put in top-level __init__, as it has global effects?
if shapely.speedups.available:
    shapely.speedups.enable()


def reach_metrics_batch(
    pedestrian_db_directory,
    street_db_directory,
    out_file,
    driver="GPKG",
    counter=None,
    processes=None,
):
    # TODO: use multiprocessing - speed up by nx, where n = cores
    networks = NetworkContainer.from_directories(
        pedestrian_db_directory, street_db_directory
    )

    # Enable to use multiple cores. Will not work with SQLite graphs
    # kwargs_list = []
    # for u, v, street in networks.street.G.network.edges:
    #     kwargs_list.append(
    #         {
    #             "networks": networks,
    #             "u": u,
    #             "v": v,
    #             "street": street,
    #             "counter": counter,
    #         }
    #     )

    # def run_jobs(processes, func, kwargs_list):
    #     with multiprocessing.Pool(processes=processes) as pool:
    #         results = [
    #             pool.apply_async(func, kwds=kwargs) for kwargs in kwargs_list
    #         ]

    #         for result in results:
    #             yield result.get()

    # nsr_ebunch = list(run_jobs(processes, _edge_nsr, kwargs_list))

    nsr_ebunch = []
    for u, v, street in networks.street.G.network.edges:
        nsr = _edge_nsr(networks, u, v, street, counter)
        nsr_ebunch.append((u, v, nsr))

    # Update via geopackage wrapper because graph update is broken
    networks.street.G.network.edges.update(nsr_ebunch)

    # Write to file. Use fiona as temporary hack rather than implementing
    # in-memory-to-file strategy
    street_network = networks.street.G.network
    properties_schema = OrderedDict()

    # with street_network.gpkg.connect() as conn:
    #     col_query = list(conn.execute("PRAGMA table_info('edges')"))
    # for row in col_query:
    #     if row["name"] in ("_u", "_v", "geom", "fid"):
    #         # These get stripped from feature properties
    #         continue
    #     if row["type"].upper() == "INTEGER":
    #         properties_schema[row["name"]] = "int"
    #     elif row["type"].upper() == "REAL":
    #         properties_schema[row["name"]] = "float"
    #     elif row["type"].upper() == "DOUBLE":
    #         properties_schema[row["name"]] = "float"
    #     elif row["type"].upper() == "TEXT":
    #         properties_schema[row["name"]] = "str"

    # Only include score-specific properties to reduce output size and
    # complexity. TODO: make this user-controllable

    with street_network.gpkg.connect() as conn:
        col_query = list(conn.execute("PRAGMA table_info('edges')"))

    for row in col_query:
        if row["name"].startswith("_weight"):
            properties_schema[row["name"]] = "float"

    for profile in networks.pedestrian.profiles:
        profile_id = profile["id"]
        column_name = f"nsr_{profile_id}"
        properties_schema[column_name] = "float"

    schema = {
        "geometry": "LineString",
        "properties": properties_schema,
    }

    crs = fiona.crs.from_epsg(4326)

    with fiona.open(out_file, "w", driver=driver, crs=crs, schema=schema) as c:
        i = 0
        batch = []
        for u, v, d in street_network.edges:
            feature = {}

            feature["geometry"] = d.pop("geom")
            feature["id"] = d.pop("fid")

            # Hack to remove any attributes in d that are missing in the schema
            missing = set(d.keys()).difference(set(properties_schema))
            for key in missing:
                d.pop(key)

            feature["properties"] = d
            if i < 1000:
                batch.append(feature)
                i += 1
            else:
                c.writerecords(batch)
                i = 0
        c.writerecords(batch)


def _edge_nsr(networks, u, v, street, counter=None):
    nsr = reach_metrics(networks, street)
    nsr = {f"nsr_{key}": value for key, value in nsr.items()}
    if counter is not None:
        counter.update(1)
    return nsr
