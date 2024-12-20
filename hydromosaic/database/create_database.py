# crude script that creates tables in the database.
# expected to be deleted when we get alembic set up.

from argparse import ArgumentParser
import re
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from hydromosaic.database import Base


def main(dsn):
    """
    Create an empty hydromosaic database.
    :param dsn: connection info for the database to update
    """
    engine = create_engine(dsn)
    db_connection = engine.connect()

    db_connection.execute(text("SET search_path = hydromosaic, public"))

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--dsn",
        help="database connection string of the form "
        "postgresql://user:password@host:port/database",
        required=True,
    )
    args = parser.parse_args()

    main(dsn=args.dsn)
