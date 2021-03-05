import os

import entwiner
from unweaver.build import MissingLayersError


def build_graphs(path, changes_sign=None):
    if changes_sign is None:
        changes_sign = []

    layers_path = os.path.join(path, "layers")
    if not os.path.exists(layers_path):
        raise MissingLayersError("layers directory not found.")

    # TODO: address redundancy between streets / ped steps
    ped_layers_path = os.path.join(layers_path, "pedestrian")
    if not os.path.exists(ped_layers_path):
        raise MissingLayersError("pedestrian layers directory not found.")

    st_layers_path = os.path.join(layers_path, "street")
    if not os.path.exists(st_layers_path):
        raise MissingLayersError("street layers directory not found.")

    ped_layers_files = [
        os.path.join(ped_layers_path, f)
        for f in os.listdir(ped_layers_path)
        if f.endswith("geojson")
    ]
    if not ped_layers_files:
        raise MissingLayersError("No GeoJSON files in pedestrian layers directory.")

    st_layers_files = [
        os.path.join(st_layers_path, f)
        for f in os.listdir(st_layers_path)
        if f.endswith("geojson")
    ]
    if not st_layers_files:
        raise MissingLayersError("No GeoJSON files in street layers directory.")

    # TODO: specify behavior when graph already exists
    # TODO: add progress bar
    ped_db_path = os.path.join(path, "pedestrian.db")
    st_db_path = os.path.join(path, "street.db")
    G_ped = entwiner.build.create_graph(ped_layers_files, ped_db_path, changes_sign=changes_sign)
    G_st = entwiner.build.create_graph(st_layers_files, st_db_path, changes_sign=changes_sign)

    return G_ped, G_st
