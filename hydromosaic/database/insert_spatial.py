import geopandas as gpd
import fiona
from sqlalchemy import create_engine, insert
from sqlalchemy.orm import sessionmaker
import logging
from hydromosaic.database import Outlet, River, Lake
import psycopg2_adapters
from shapely.geometry import mapping, LineString, MultiLineString, Polygon, MultiPolygon
from geoalchemy2.shape import from_shape

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for expected columns
EXPECTED_COLUMNS = {
    "rivers": {"SubId", "DowSubId", "Seg_Id", "geometry"},
    "lakes": {"SubId", "HyLakeId", "geometry"},
}

psycopg2_adapters.register()


def validate_gpkg(gdf, layer_name):
    # Normalize column names to lowercase
    gdf.columns = [col.lower() for col in gdf.columns]
    expected_columns = {col.lower() for col in EXPECTED_COLUMNS[layer_name]}

    missing_columns = expected_columns - set(gdf.columns)

    logger.debug(f"Expected columns for {layer_name}: {expected_columns}")
    logger.debug(f"Actual columns in GeoPackage: {set(gdf.columns)}")

    if missing_columns:
        logger.error(f"Missing columns in {layer_name}: {missing_columns}")
        raise ValueError(
            f"{layer_name.title()} GeoPackage missing columns: {missing_columns}"
        )
    logger.info(f"Data types before insertion: {gdf.dtypes}")

    # Convert column data types to Python-native types
    if layer_name == "rivers":
        gdf = gdf.astype({"subid": int, "dowsubid": int, "seg_id": int})
    elif layer_name == "lakes":
        gdf = gdf.astype({"subid": int, "hylakeid": int})

    return gdf


def convert_to_multi(geom):
    if isinstance(geom, LineString):
        return MultiLineString([geom])
    elif isinstance(geom, Polygon):
        return MultiPolygon([geom])
    return geom


def prepare_data(gdf, layer_name):
    """Prepare data for insertion, mapping GeoPackage attributes to DB column names."""
    if layer_name == "rivers":
        return [
            {
                "sub_id": row["subid"],
                "dow_sub_id": row["dowsubid"],
                "seg_id": row["seg_id"],
                "geom": from_shape(convert_to_multi(row["geometry"]), srid=3005),
            }
            for _, row in gdf.iterrows()
        ]
    elif layer_name == "lakes":
        return [
            {
                "sub_id": row["subid"],
                "hy_lake_id": row["hylakeid"],
                "geom": from_shape(convert_to_multi(row["geometry"]), srid=3005),
            }
            for _, row in gdf.iterrows()
        ]
    else:
        raise ValueError(f"Unknown layer type: {layer_name}")


def bulk_insert(session, table, data):
    if data:
        insert_stmt = insert(table).values(data)
        session.execute(insert_stmt)
        logger.info(f"Inserted {len(data)} records into {table.name}.")


def read_first_layer(geopackage_path):
    """Read the first layer from a GeoPackage."""
    layers = fiona.listlayers(geopackage_path)
    if not layers:
        raise ValueError(f"No layers found in GeoPackage: {geopackage_path}")

    return gpd.read_file(geopackage_path, layer=layers[0])


def import_data(dsn, rivers_path, lakes_path):
    """Import from GeoPackage files into PostgreSQL DB."""
    logger.info("Starting data import...")

    # Read GeoPackage files into GeoDataFrames
    rivers_gdf = read_first_layer(rivers_path)
    lakes_gdf = read_first_layer(lakes_path)

    if rivers_gdf.empty and lakes_gdf.empty:
        logger.warning("No data to import. Exiting.")
        return

    # Validate GeoPackages
    rivers_gdf = validate_gpkg(rivers_gdf, "rivers")
    lakes_gdf = validate_gpkg(lakes_gdf, "lakes")

    # Reproject GeoDataFrames
    rivers_gdf = rivers_gdf.to_crs("EPSG:3005")
    lakes_gdf = lakes_gdf.to_crs("EPSG:3005")

    engine = create_engine(dsn)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        logger.info("Preparing outlets...")
        unique_sub_ids = set(rivers_gdf["subid"].unique()) | set(
            lakes_gdf["subid"].unique()
        )
        existing_outlets = (
            session.query(Outlet.id).filter(Outlet.id.in_(unique_sub_ids)).all()
        )
        existing_outlet_ids = {o[0] for o in existing_outlets}
        new_outlets = [
            {"outlet_id": sub_id, "code": str(sub_id)}
            for sub_id in unique_sub_ids - existing_outlet_ids
        ]

        if new_outlets:
            bulk_insert(session, Outlet.__table__, new_outlets)
            logger.info(f"Inserted {len(new_outlets)} new outlets.")

        logger.info("Preparing rivers...")
        rivers_data = prepare_data(rivers_gdf, "rivers")
        bulk_insert(session, River.__table__, rivers_data)

        logger.info("Preparing lakes...")
        lakes_data = prepare_data(lakes_gdf, "lakes")
        bulk_insert(session, Lake.__table__, lakes_data)

        session.commit()
        logger.info("Data import completed successfully.")

    except Exception as e:
        session.rollback()
        logger.error(f"Error during data import: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "-d",
        "--dsn",
        help="database connection string of the form postgresql://user:password@host:port/database",
        required=True,
    )
    parser.add_argument(
        "--rivers", help="Path to Fraser_3005_rivers.gpkg file", required=True
    )
    parser.add_argument(
        "--lakes", help="Path to Fraser_3005_lakes.gpkg file", required=True
    )

    args = parser.parse_args()

    import_data(dsn=args.dsn, rivers_path=args.rivers, lakes_path=args.lakes)
