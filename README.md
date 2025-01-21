Hydromosaic-db
===============

The hydromosaic database stores metadata about modeled stream flow, stream temperature, and oxygen content. The data is in netCDF files, each of which contains multiple timeseries calculated for different stream outlets. This database supports a data server to locate and stream available data for each stream outlet. 

It has no geographical data on the locations or upstream/downstream relationships of stream outlets; geography and mapping are handled by a separate database.

Initializing a new database
---------------------------

Database design is handled with [sqlalchemy](https://www.sqlalchemy.org/) and [alembic](https://alembic.sqlalchemy.org/en/latest/). In order to initialize or upgrade a database:

1. Install the ORM with `poetry install`
1. Edit the `sqlalchemy.url` line in alembic.ini to a connection string for the database you wish to update
1. Type `poetry run alembic update head` to initialize the database