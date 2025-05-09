# Hydromosaic-db

The hydromosaic database stores metadata about modeled stream flow, stream temperature, and oxygen content. The data is in netCDF files, each of which contains multiple timeseries simulated for different stream outlets. This database supports a [data server](https://github.com/pacificclimate/hydromosaic-service) to locate and stream available data for each stream outlet. 

It has no geographical data on the locations or upstream/downstream relationships of stream outlets; geography and mapping are handled by a separate database.

## Initializing a new database

Database design is handled with [sqlalchemy](https://www.sqlalchemy.org/) and [alembic](https://alembic.sqlalchemy.org/en/latest/). In order to initialize or upgrade a database:

1. Install the ORM with `poetry install`
1. Edit the `sqlalchemy.url` line in alembic.ini to a connection string for the database you wish to update
1. Type `poetry run alembic upgrade head` to initialize the database

## Indexing netCDF files into the database

The indexing script is installed by poetry. It accepts a directory and a database connection string as arguments, and attempts to index every netCDF file in the directory into the database. To run the indexing script:

```
poetry run index_directory -d postgresql://user:password@server:port/hydromosaic /path/to/data/directory/
```

### Indexing pitfalls

The indexing script skips over any file already in the database. If you add data to or remove data from a file, it will not be updated unless you delete the file from the database first.

The indexing script identifies a file by its full path. If you rename or move a file, and index it in its new location, its data will be duplicated in the database unless you delete the old file entry first.

### Expected File format

Timeseries netCDFs are expected to have the following format:

- `time` and `nbasins` dimensions. `nbasins` should have cardinality equal to the number of sites or outlets in this file
- a `basin_name` variable with the single dimension `nbasins`. It should provide a string code to uniquely identify each outlets
- one or more variables with dimensions `nbasins` and `time`. These should conform to [CF Conventions](https://cfconventions.org/) for variable metadata, including `units` and `long_name`.
- global metadata in accordance with the PCIC Metadata Standards. Load-bearing attributes in this case concern the model and the emissions scenario, required for the database:
    - `downscaling_GCM_institute_id`
    - `downscaling_GCM_model_id`
    - `downscaling_GCM_experiment_id`
    - `downscaling_GCM_experiment`

An alternate prefix (instead of `downscaling_GCM_`, which is used for data generated by hydrological models forced by downscaled GCM data) may be supplied via the `-p` argument, if needed for data with an alternate history, such as hydrological models forced by gridded observation data.