"""reach_metrics CLI."""
import os
import sqlite3

import click
import fiona

import entwiner
from unweaver.build import build_graph, get_layers_paths
from unweaver.parsers import parse_profiles
from unweaver.server import run_app
from reach_metrics.reach_metrics_batch import reach_metrics_batch

# Size of batch inserts
BATCH_SIZE = 1000


@click.group()
def reach_metrics():
    pass


@reach_metrics.command()
@click.argument("directory", type=click.Path("r"))
@click.option("--changes-sign", multiple=True)
def build(directory, changes_sign):
    pedestrian_directory = os.path.join(directory, "pedestrian")
    street_directory = os.path.join(directory, "street")

    click.echo("Building street network...")
    click.echo("Estimating street feature count...")
    n_streets = 0
    for path in get_layers_paths(street_directory):
        with fiona.open(path) as c:
            n_streets += len(c)
    with click.progressbar(length=n_streets, label="Importing edges") as bar:
        build_graph(street_directory, changes_sign=changes_sign, counter=bar)

    click.echo("Building pedestrian network...")
    click.echo("Estimating pedestrian feature count...")
    n_pedestrian = 0
    for path in get_layers_paths(pedestrian_directory):
        with fiona.open(path) as c:
            n_pedestrian += len(c)
    with click.progressbar(
        length=n_pedestrian, label="Importing edges"
    ) as bar:
        build_graph(
            pedestrian_directory, changes_sign=changes_sign, counter=bar
        )

    click.echo("Done.")


@reach_metrics.command()
@click.argument("directory", type=click.Path("r"))
def weight(directory):
    for network_type in ("street", "pedestrian"):
        network_directory = os.path.join(directory, network_type)

        click.echo(f"Calculating static {network_type} network weights...")

        profiles = parse_profiles(network_directory)
        n_profiles = len([p for p in profiles if p["precalculate"]])

        G = entwiner.DiGraphDB(
            path=os.path.join(network_directory, "graph.gpkg")
        )
        n_weights = G.size() * n_profiles

        with click.progressbar(
            length=n_weights, label=f"Computing {network_type} network weights"
        ) as bar:
            for profile in profiles:
                if profile["precalculate"]:
                    cost_function = profile["cost_function"]()
                    weight_column = "_weight_{}".format(profile["id"])
                    try:
                        with G.network.gpkg.connect() as conn:
                            conn.execute(
                                f"""ALTER TABLE edges
                                     ADD COLUMN {weight_column} DOUBLE"""
                            )
                    except sqlite3.OperationalError:
                        pass
                    batch = []
                    for u, v, d in G.iter_edges():
                        weight = cost_function(u, v, d)
                        if len(batch) == BATCH_SIZE:
                            G.update_edges(batch)
                            batch = []
                        batch.append((u, v, {weight_column: weight}))
                        bar.update(1)
                    # Update any remaining edges in batch
                    if batch:
                        G.update_edges(batch)

    click.echo("Done.")


@reach_metrics.command()
@click.argument("directory", type=click.Path("r"))
@click.option("--output", "-o", default="reach_metrics.gpkg")
@click.option("--output_driver", "-od", default="GPKG")
def score(directory, output, output_driver):
    pedestrian_directory = os.path.join(directory, "pedestrian")
    street_directory = os.path.join(directory, "street")

    G = entwiner.DiGraphDB(path=os.path.join(street_directory, "graph.gpkg"))
    n = G.size()
    click.echo("Converting to in-memory graph databases...")
    with click.progressbar(length=n, label="Computing metrics") as bar:
        reach_metrics_batch(
            pedestrian_directory,
            street_directory,
            out_file=os.path.join(directory, output),
            driver=output_driver,
            counter=bar,
        )
    click.echo("Done.")


@reach_metrics.command()
@click.argument("directory", type=click.Path("r"))
@click.option("--host", "-h", default="localhost")
@click.option("--port", "-p", default=8000)
@click.option("--debug", is_flag=True)
def serve(directory, host, port, debug=False):
    click.echo("Starting server in {}...".format(directory))
    run_app(directory, host=host, port=port, debug=debug)
