## Data

### OpenStreetMap data

This repository makes use of OpenStreetMap data for a variety of purposes.

Specificially, a Seattle-area extract is generated as part of the data
processing workflow, generating `artifacts/seattle.osm.pbf`. This file is
included as part of this repository under the ODbL license.

To regenerate this extract (by running the
`00 - Extract Seattle Area OpenStreetMap.ipynb` notebook), a file named
`data/washington-latest.osm.pbf` muts exist, an OSM PBF-format file that
includes the Seattle area. This file can be downloaded from
`https://download.geofabrik.de/north-america/us/washington-latest.osm.pbf`.

### For Figures

#### Coastlines from OpenStreetMap

The backgrounds for several figures uses Seattle landmasses and is located at
`artifacts/seattle_landmasses.geojson`. This artifact is included in this
repository

The backgrounds for several figures are derived from an OpenStreetMap-derived
coastlines dataset knowing as `processed_p.shp`. This is normally obtained at
[this URL](http://tile.openstreetmap.org/processed_p.tar.bz2). Placing this
file in the data/landmasses directory will enable the
`notebooks/Extract Seattle-area landmass polygons.ipynb` notebook to run,
generating the `artifcats/seattle_landmass.gpkg` file. However, at the time of
publication this URL is unavailable and visiting it returns a status code of
403: forbidden. Any landmass polygon GeoPackage can be substituted in its
place.

Note that this notebook requires the use of the command line tool `tar`.

## Installing software

### `osmium`

Some notebooks extract data from OpenStreetMap using `osmium`, an open source
command line tool. This tool is widely available. On systems with `apt`, like
Debian and Ubuntu, it can be installed using `apt install osmium-tool`.

### Python libraries

This notebook was developed using [poetry](https://python-poetry.org/) and can
be most easily installed using that tool. If you have `poetry` installed,
simply run `poetry install` in the main directory. A new virtual environment
will be created for you and all libraries will be installed. To run the
Jupyter environment, run `poetry run jupyter notebook`.

If you would prefer to use a native `pip`-based install, a `requirements.txt`
is included that acts as a lockfile for all libraries. To install all of the
required libraries, run `pip3 install -r requirements.txt`. To run the Jupyter
environment, run `jupyter notebook`. You may prefer to create a virtual
environment for this project in advance.

## Running the code

All code necessary for recreating our analyses and figures is available in the
two Jupyter notebook directories, `data_notebooks` and `figure_notebooks`. Once
you have created your Python environment according to the installation
instructions, you can run `jupyter notebook` using either
`poetry run jupyter notebook` (with the recommended `poetry` installation) or
using `jupyter notebook` (if you chose a custom installation method).

### 0. (optional) process from original data sources

If you want to recreate the underlying basemap data, follow the instructions
above for OpenStreetMap figure data and then run the notebooks beginning with
`000` in the `data_notebooks` directory.

### 1. Run the data notebooks

The notebooks have been named in the order in which they must be run, with the
smallest number running first. These notebooks will generate artifacts in the
`artifacts` directory.

### 2. Run the figure notebooks

The notebooks have been named in the order in which they must be run, with the
smallest number running first. These notebooks will generate artifacts in the
`artifacts/figures` directory.

## QGIS projects

Some of the figures were generated as QGIS exports rather than plotnine code
- mostly for performance reasons. The notebooks in the `qgis` subdirectory can
be run after all of the notebooks in `data_notebooks` have been run, creating
the necessary artifacts. The "aoi" polygon layers should be used during export
to define the extent.

## Licenses

Unless otherwise noted, all code in this repository is released under the MIT
license. Code with other licenses have a LICENSE file within their directory,
a license within the code files themselves, or within a pyproject.toml file.

Data included in this repository is licensed as permissively as its source
allows.

### Licensed under ODbL

- `artifacts/seattle.osm.pbf`
- `artifacts/seattle_landmasses.geojson`

### Licensed under the Apache-2.0 license

- `data/unweaver` (all files)

### Public domain data

- `data/seattle.geojson`
- `data/reach_metrics.gpkg`
